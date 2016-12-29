
"""
Controller_Core - a ryu application for the team 4 project
The code uses the topology discovery code sourced from [1] as a starting point. The original code is based on Openflow v1 and uses ryu topology api
and flooding to build the topology. However, it underwent major modification to support below features:

-topology discovery without ARP flooding the network. To bootstrap the network, one must perform  pingall in the mininet.
-Implement a discrete graph from the data provided by topology api
-Compute shortest path from the graph
-Install flows in the all the switches in a path to route a packet from one node to another

References:
    [1] https://sdn-lab.com/2014/12/31/topology-discovery-with-ryu/
"""

import logging
import struct
from pprint import pprint


from ryu.base import app_manager
#from ryu.controller import mac_to_port
from collections import deque
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ether_types

from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches 
import networkx as nx
#Ryu controller won't run on a linux without x-windows unless an Agg backend is selected
import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')
#Done with Agg backend selection in case an X is not avaialble
import matplotlib.pyplot as plt
from ryu.lib.mac import haddr_to_bin
import time
#from collections import deque #used to remove first and last element from the list efficently
#***********************************************************
#below imports are used to import the database client library
import sys
import os

#path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from datetime import datetime
from client import client_side

#***********************************************************






class CPMdummy(app_manager.RyuApp):
    'CPM module for CSD Team4 project'
    net = nx.DiGraph()
    app_manager._CONTEXTS = {'network': net}
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    #my custom logger only works if i use the ryu's logger: self.logger.info in the code and then use my custom logger, even then I noticed
    #my logger seemed to be affected by ryu's logger config since both use the logging module. Did not spend any time discovering it further
    #  since ryu's logger meets the needs. --shafi
    # def init_logger(self):
    #     import logging
    #     logging.basicConfig(filename='cc.log', level=logging.DEBUG,format='%(levelname)s:%(asctime)s:%(message)s')
    #     # log to file
    #     self.CSDLOG = logging.getLogger(__name__)
    #     self.CSDLOG.debug('Configuring logger at startup')


    def __init__(self, *args, **kwargs):
        super(CPMdummy, self).__init__(*args, **kwargs)

        self.defines_D = {'bcast_mac': 'ff:ff:ff:ff:ff:ff',
                          'bootstrap_in_progress': True,
                          'flow_table_strategy_semi_proactive': True,
                          'logdir': '/var/www/html/spacey',
                          'cpmlogdir': '/var/www/html/spacey/cpmweights.log',
                          'metrics_fetch_rest_url': 'http://127.0.0.1:8000/Tasks.txt',
                          'fetch_timer_in_seconds': 4}

        self.cpmlogger = logging.getLogger("cpm" + __name__)
        self.cpmlogger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(self.defines_D['cpmlogdir'])
        handler.setLevel(logging.DEBUG)
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.cpmlogger.addHandler(handler)
        self.cpmlogger.info("Starting up cpmlogger. edges are %r", self.net.edges())





        #self.mac_to_port = {}
        self.l2_dpid_table = {}
        """
        #an example from log is: here 21 is the dpid, one can access using l2[21]['00:00:...']['ip']
        # l2_dpid_table: {21: {'00:00:00:00:01:02': {'ip': '10.1.0.2', 'in_port': 4}},
        #                   23: {'00:00:00:00:02:02': {'ip': '10.2.0.2', 'in_port': 5}}}

        #
        #below is 'ip' address of mac 'x:x:x' learnt on switch with dpid 3
        ipofmacX = l2_dpid_table[3]['x:x:x']['ip']
        #below is the port at which mac 'x:x:x' was learnt by switch with dpid 3
        port_of_mac_X_on_switch3 = l2_dpid_table[3]['x:x:x']['in_port']

        """

        #self.net = kwargs['network']
        #app_manager._CONTEXT = {'network',self.net}
        #self.net = app_manager._CONTEXT['network']
        #_CONTEXT = {'network',self.net}

        """wegiths read from a remote cache/db and injected into the topology graph
        note that :
            link_util is for each link so should be stored in each edge of the graph
            sw_packet_drop_rate is for each switch so should be stored in each node of the graph

        """

        self.edge_weights = dict.fromkeys(['core_util','mem_usage','rpm_weight','link_util','sw_packet_drop_rate'])

        self.l2_ip2mac_table = {}
        self.l2_mac2ip_table = {}
        self.topology_api_app = self

        self.nodes = {}
        self.links = {}
        self.no_of_nodes = 0
        self.no_of_links = 0
        self.i=0

        """
        flow_table_strategy_semi_proactive: when controller receives the first packet, it reacts to it by proactively installing flows in all switches that lie in the computed
                                            shortest path for that packet to reach its destination.
        proactive:  controller before receiving any packet to be routed, installs the paths in the switches
        reactive: controller installs the rules in one switch
        """
        self.rxpkts_types_D= {}
        self.logger.info("controller_core module starting up....")
        self.epoc_starttime = int(time.time())
        self.network_bootstrap_type = 1 # parameter described below, TODO: do as enumeration
        """
        type 0 means end bootstraping after a certain number of seconds i..e time limited bootstrap
        type 1 means end bootstrapping once a certain number of mac addresses have been discovered ie. discovered mac address count limited. It counts the len of l2_mac2_ip_table dictionary
        """
        self.network_bootstrap_time = 70 # in seconds and used by type 0
        self.network_bootstrap_discovery_count = 4 #used by type 1, means stop after 4 mac addresses learnt

        self.datapathDb = {}
        self.already_installed_paths_SET = set()

        # Fetch metrics from remote Cache related data structures
        self.time_of_last_fetch = 0

        self.cpmlogger.info("BOOTSTRAP, type = %r , host_count = %r",self.network_bootstrap_type, self.network_bootstrap_discovery_count)



    #Below method just populates the net graph to which above packet-in method just adds src/dst
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        #we reap from two source provided by LLDP based ryu topology api : switch_list and link_list
        #and put the info into a networkx based graph "net"
        #****************** switches *******************
        self.logger.debug("EventSwitchEnter observed: %r", ev)
        switch_list = get_switch(self.topology_api_app, None)
        """
        #commenting out this block we dont want to add the switch dpid to the graph since this info is there already in the links_list
        self.logger.debug("type(switch_list) = %r", type(switch_list))
        for s in switch_list:
            self.logger.debug(s.dp.id)
        #print "switch_list dict \n", switch_list.to_dict() #FAILED: no such attributed to_dict()
        switches=[switch.dp.id for switch in switch_list]

        #self.logger.debug("switches is of type: %s", type(switches)) #this shows list
        #self.logger.debug("switches on ls shows None because its just a list has %s", self.ls(switches))
        self.logger.debug ("List of switches %r", switches)

        #adding the switch info to our topology graph
        self.net.add_nodes_from(switches)
        self.logger.debug ("nodes:")
        self.logger.debug( self.net.nodes() )

        #print "List of switches"
        #for switch in switch_list:
        #self.ls(switch)
        #print switch
        #self.nodes[self.no_of_nodes] = switch
        #self.no_of_nodes += 1
        #
        """
	    #************** LINKS **************************
        links_list = get_link(self.topology_api_app, None)
        # self.logger.debug( "type(links_list): %s",type(links_list) ) #this in log shows  <class 'ryu.topology.switches.LinkState'>
        # self.logger.debug("links_list: %r", links_list) #multiple
        # self.logger.debug("self.ls(links_list): %r", self.ls(links_list)) #this always gives None

        #print links_list.to_dict()

        #print links_list

        #links = [self.logger.debug("link = %r",link) for link in links_list]
        #links_dict = [self.logger.debug("link.to_dict() = %r", link.to_dict()) for link in links_list] #this in log shows as below:

        # link.to_dict() in logs shows {'src':
        #                       {'hw_addr': '06:f3:96:df:a2:6c', 'name': u'l1-eth1', 'port_no': '00000001',
        #                        'dpid': '0000000000000015'},
        #                   'dst': {'hw_addr': 'ee:d9:44:eb:c4:76', 'name': u's1-eth3', 'port_no': '00000003',
        #                           'dpid': '000000000000000b'}}

        #links_type = [self.logger.debug("type(link) = %r", type(link)) for link in links_list] #this shows <ryu.topology.switches.Link

        #link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]
        ##################################################### Graph node representation idea 1 ######################################################
        #Below was the initial idea of representing the graph topology its now obsoleted by later
        # Since "net" is a Directional Graph so we need to add two ordered pairs srcdpid-srcinport,dstdpid-dstinport,{'weight',100}) for a link between switch srcdpid and dstdpid

        #links=[(str(link.src.dpid) + '-' + str(link.src.port_no), str(link.dst.dpid) + '-' + str(link.dst.port_no) ,{'weight': 100,'src_dpid':link.src.dpid, 'src_port':link.src.port_no, 'dst_dpid':link.dst.dpid, 'dst_port':link.dst.port_no}) for link in links_list]
        #self.logger.debug("List to be added to graph ,should be of form [(a,b,{}), (c,d,{}) ..]: \n %r",links)

        ##################################################### Graph node representation idea 2 #####################################################
        #just put switches as node names and add the below dictionary as data to edges
        # Storing the src and dst dpid key in the dictionary is redundant but I want to experiment with something later.

        """Below has an error that was fixed in subsequent block
        links_onedirection_L=[(link.src.dpid,link.dst.dpid,{'src_port':link.src.port_no, 'dst_port':link.dst.port_no, 'src_name': link.src.name, 'dst_name':link.dst.name}) for link in links_list]
        links_opp_direction_L=[(link.dst.dpid, link.src.dpid, {'dst_port': link.dst.port_no, 'src_port':link.src.port_no, 'src_name': link.src.name, 'dst_name':link.dst.name}) for link in links_list]
        """
        #while installing flow rules observed that src and dst port are opposite to our understanding (BUG: in_port and out_port are the same as infact this)


        links_onedirection_L = [(link.src.dpid, link.dst.dpid,
                                 {'dst_port': link.src.port_no, 'src_port': link.dst.port_no, 'dst_name': link.src.name,
                                  'src_name': link.dst.name,'bw': 10,'wegiht': 1 }) for link in links_list]
        links_opp_direction_L = [(link.dst.dpid, link.src.dpid,
                                  {'src_port': link.dst.port_no, 'dst_port': link.src.port_no,
                                   'dst_name': link.src.name, 'src_name': link.dst.name, 'bw':10 , 'weight': 1}) for link in links_list]

        """
        #Below is an attempt to introduce src_dst key and then just plot it in the topology graph instead of having two sepreate graphs
        links_onedirection_L = [(link.src.dpid, link.dst.dpid,
                                 {'dst_port': link.src.port_no, 'src_port': link.dst.port_no, 'dst_name': link.src.name,
                                  'src_name': link.dst.name, 'src_dst': str(link.dst.port_no + '-' + link.src.port_no)})
                                for link in links_list]
        links_opp_direction_L = [(link.dst.dpid, link.src.dpid,
                                  {'src_port': link.dst.port_no, 'dst_port': link.src.port_no,
                                   'dst_name': link.src.name, 'src_name': link.dst.name,
                                   'src_dst': str(link.dst.port_no + '-' + link.src.port_no)}) for link in links_list]
        """

        #
        # for l in links_list:
        #     self.logger.debug("%r",l.src.dpid)
        #     self.logger.debug("%r",l.dst.dpid)
        #     self.logger.debug("type dst.dpid: %r", type(l.dst.dpid)) #this is type int
        #     self.logger.debug("%r", l.src.port_no) # values see are crisp i.e 4 , 2 etc
        #     self.logger.debug("%r", l.dst.port_no) # values are crisp 23, 24,etc. same as dpid assigned in the mininet (base 10)
        #     self.logger.debug("type dst.port_no: %r", type(l.dst.port_no)) #this is type int
        #     #Hint: to convert a port_no or dpid to string if required, you can use the below helper functions:
        #     #from ryu.lib.dpid import dpid_to_str, str_to_dpid
        #     #from ryu.lib.port_no import port_no_to_str
        #     #See: ryu/topology/switches.py


        #print links
        #self.net.add_edges_from(links) #these are ordered pairs like if s1 and s2 are connected u will get (1,2),(2,1) that 1 -> and 2->1
        #links=[(link.dst.dpid,link.src.dpid,{'port':link.dst.port_no}) for link in links_list]
        #print links
        ################################################## Updating the "net" graph with LLDP learnt topology
        self.net.add_edges_from(links_onedirection_L)
        self.net.add_edges_from(links_opp_direction_L) #since its a directional graph it must contain edges in opposite direction as well.


        #for link in links_list:
	    #print link.dst
            #print link.src
            #print "Novo link"
	    #self.no_of_links += 1
        
	#print "@@@@@@@@@@@@@@@@@Printing both arrays@@@@@@@@@@@@@@@"
    #for node in self.nodes:	
	#    print self.nodes[node]
	#for link in self.links:
	#    print self.links[link]
	#print self.no_of_nodes
	#print self.no_of_links

    #@set_ev_cls(event.EventLinkAdd)
    #def get_links(self, ev):
	#print "################Something##############"
	#print ev.link.src, ev.link.dst
    def print_l2_table(self):
        self.logger.debug("l2_table = %r", self.l2_dpid_table)
        self.logger.debug("l2_mac2ip = %r", self.l2_mac2ip_table)
        self.logger.debug("l2_ip2mac = %r", self.l2_ip2mac_table)

    def _send_packet(self, datapath, port, pkt):
        #self.logger.debug("Sending crafted packet to datapath = %r, port = %r", datapath,port)
        self.logger.debug("Sending an arp reply in _send_packet")
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("crafted arp reply packet-out %s" % (pkt,))
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=pkt.data)
        datapath.send_msg(out)

    def clamp(self,n, smallest, largest):
        return max(smallest, min(n, largest))

    def __update_graph(self,src_dpid,dst_dpid, key,value):
        """key can be <module_name><module_key> e.g. 'nfm_link_utilization' """
        self.logger.info("FETCH UPDATE_GRAPH_NFM , weight = %r", value)
        try:
            self.net.edge[src_dpid][dst_dpid][key] = value
            #self.net[src_dpid][dst_dpid][key] = value
            self.logger.debug("FETCH Assigned value self.net.edge[%r][%r]['weight'] = %r", src_dpid,dst_dpid,self.net.edge[src_dpid][dst_dpid]['weight]'])
        except (KeyError):
            self.logger.error("FETCH KeyError when updating graph")
            #raise
        except (NameError):
            self.logger.error("FETCH NameError when updating graph")
        except Exception,e:
            #self.logger.exception("Unable to update this key in the graph on fetch %r",e)
            self.logger.error('Unable to update this key in the graph, here is the traceback',exc_info=True)


    def __fetch_metrics_and_insert_in_graph(self,module_name):
        self.current_time = int(round(time.time()*1000))
        #every 4 seconds
        time_max_limit = self.defines_D['fetch_timer_in_seconds'] * 1000
        self.logger.debug("FETCH fetch_metric_and_insert_ingraph, time_max_limit = %r",time_max_limit)
        if not (self.current_time - self.time_of_last_fetch > time_max_limit) or self.defines_D['bootstrap_in_progress']:
            return
        else:
            self.time_of_last_fetch = self.current_time
            self.logger.debug("FETCH_TIME_CHECK_OK, about to fetch_KPI")


        if module_name == 'nfm':
            url = self.defines_D['metrics_fetch_rest_url']
            DMclient = client_side(url)
            nfm_what_metrics_to_fetch = {'module': 'nfm', 'keylist': ['link_utilization']}
            response = DMclient.getme(nfm_what_metrics_to_fetch)
            self.logger.debug("FETCH_METRICS_NFM: getme response = %r ",response)
            self.cpmlogger.debug("cpmlogger : response = %r",response)
            response1 = response[0]
            #graph = response [0][1]
            graph = response1[1]
            del response1
            del response

            self.logger.debug("FETCH_METRICS_NFM:  graph = %r", graph)
            # tthe output in log was :
            # graph =  {u'2-1': 0.0, u'1-2': 0.0}

            for gkey in graph:
                gkey = gkey.encode('ascii', 'ignore')
                self.logger.debug("%r corresponds to %r",gkey,graph[gkey])
                src_dpid, dst_dpid = gkey.split('-')  # returns a lista
                src_dpid = src_dpid.strip()  # default to removing white spaces
                dst_dpid = dst_dpid.strip()  # defaults to removing white spaces
                #if len(graph[gkey]) > 1:
                #    self.logger.warn("grap[gkey] > 1 and is = %r",graph[gkey])

                link_util_value = self.clamp(graph[gkey], 0, 100)  # the link_utilization value must be between 0 to 100

                # value = clamp(-300.0023,0,100) #the link_utilization value must be between 0 to 100
                # value2 = clamp(300.0023,0,100) #the link_utilization value must be between 0 to 100

                self.logger.debug("FETCH_METRICS_NFM: src_dpid = %r , '-', dst_dpid = %r, '====', value =%r",src_dpid, dst_dpid , link_util_value)
                self.__update_graph(src_dpid,dst_dpid,'nfm_link_util',link_util_value)
            # self.net.edge[src_dpid][dst_dpid]['link_utilization'] = graph[gkey]




