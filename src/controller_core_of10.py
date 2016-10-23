
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
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches 
import networkx as nx
import matplotlib.pyplot as plt
from ryu.lib.mac import haddr_to_bin
import time




class ProjectController(app_manager.RyuApp):
	
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
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
        super(ProjectController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.topology_api_app = self
        self.net=nx.DiGraph()
        self.nodes = {}
        self.links = {}
        self.no_of_nodes = 0
        self.no_of_links = 0
        self.i=0
        self.defines_D = {'bcast_mac':'ff:ff:ff:ff:ff:ff', 'build_graph_once': True}
        #adnan 's experiments added
        #self.init_logger()
        self.rxpkts_types_D= {}
        self.logger.info("controller_core module starting up....")
        self.epoc_starttime = int(time.time())
        self.network_bootstrap_time = 40 # in seconds

    # Handy function that lists all attributes in the given object
    def ls(self,obj):
        print("\n".join([x for x in dir(obj) if x[0] != "_"]))
	
    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)
    def shortest_path(self,src_node,dst_node):
        sp_L = nx.shortest_path(self.net,src_node, dst_node, weighted = True) # L indicates it is a list of nodes e.g. [1,2,3,4]
        return sp_L

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        #Do something after the network finished bootstraping e.g. save the topology diagram just once after the network has bootstrapped
        # if self.defines_D['build_graph_once']:  # we do it because nx.draw overwrite the previous graph everytime we draw it. as if matlab hold is on. TOFIX
        #     if int(time.time()) - self.epoc_starttime > self.network_bootstrap_time:
        #         self.defines_D['build_graph_once'] = False
        #         self.save_topolog_to_file()

        self.save_topolog_to_file()

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.in_port
        if in_port:
            #self.logger.debug("Received Packet-IN and in_port is not empty")
            pass
        else:
            self.logger.error("EMPTY in_port in Packet-IN message")

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)


        dst = eth.dst
        src_mac = eth.src
        dpid = datapath.id
        #note the switch dpid in our table
        self.mac_to_port.setdefault(dpid, {})

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packel
            return

        self.logger.debug("OFPP_FLOOD = %r",ofproto.OFPP_FLOOD) #only when pingall done, then it gave OFPP_FLOOD = 65531
        #note that 65531 decimal in hex is  FFFB
        self.logger.debug("OFPP_FLOOD in hex = %x",ofproto.OFPP_FLOOD)  # only when pingall done, then it gave OFPP_FLOOD = 65531
        self.logger.debug("haddr_to_bin(dst) = %r",haddr_to_bin(dst))

        if dst == self.defines_D['bcast_mac']: #if dst == 'ff:ff:ff:ff:ff:ff' means its a host that is flooding the network, we gotta learn it
            self.logger.debug("Now learning a node with src mac = %s that is arp broadcasting", src_mac)
            self.logger.debug("dpid= %r , in_port = %r", dpid, msg.in_port)
            ############################# Below was discarded idea of representing graph nodes: srcdpid-srcport, dstdpid-dstport that lead to such edges in topology ('3-1', '00:00:00:00:00:03'), ('2-1', '00:00:00:00:00:02')
            ####self.net.add_edge(str(dpid)+ '-' + str(msg.in_port), str(src),{'end_host': 1}) #-1 indicates its a host
            ############################# The way of representing the graph nodes
            self.net.add_edge(dpid,src_mac,
                                     {'src_port': msg.in_port, 'dst_port': msg.in_port,
                                      'src_dpid': dpid, 'dst_dpid': src_mac, 'end_host':True}) #src is the src mac
            self.net.add_edge(src_mac, dpid,
                              {'src_port': msg.in_port, 'dst_port': msg.in_port,
                               'src_dpid': src_mac, 'dst_dpid': dpid, 'end_host':True })  # src is the src mac

            # learn a mac address to avoid FLOOD next time.
            # a 3 column table is maintained: dpid, src_mac, in_port
            self.mac_to_port[dpid][src_mac] = msg.in_port  #msg.match['port'] is this a v3 v1 thing?
            self.show_graph_stats()


        else: #this is not an lldp packet, this is not arp broadcast.
            #check if its a valid openflow packet
            self.logger.debug("Received Packet-IN event with dst mac not broadcast. ")
            #Is            it            a            valid            openflow - check msg len
            #do we have this packet in our mac_to_port table
            if dst in self.mac_to_port[dpid]:
                #compute
                #find output to prepaer a flow-mod to all the switches in the path
                #this outport just tells
                #route this packet to switch dpid's out_port

                out_port = self.mac_to_port[dpid][dst]

                pass
            #else:
                #we have no path to the destination mac address, we ll just wait and wont flood the network.
                #pass

        #self.logger("type of msg.in_port is %s",type(msg.in_port))
        #self.logger.debug("Received PacketIn: dpid = %r , in_port = %r , srcmac= %r, dstmac = %r , packet_type = %r",dpid, msg.match['in_port'] , src,dst, eth.ethertype)
        #print "Received PacketIn: dpid = ", dpid, "srcmac=", src, "dstmac = ", dst, "packet_type = ", eth.ethertype
        #store in a dict what types of packets received and how many
        if eth.ethertype in self.rxpkts_types_D:
            self.rxpkts_types_D[eth.ethertype] += 1;
        else:
            self.rxpkts_types_D.setdefault(eth.ethertype,1) #for dictionary D, against a key eth.ethertype, set a default value 1

        #eth.etheretype == ether_types.ETH_TYPE_ARP
        #eth.etheretype == ether_types.ETH_TYPE_LLDP
        #eth.etheretype == ether_types.


        #print "start mac_to_port: _____"
        #pprint (self.mac_to_port)

        #print "nodes"
        #print self.net.nodes()
        #print "edges"
        #print self.net.edges()
        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)

        #In exampleswitch13-rev1 in_port was like below
        #in_port = msg.match['in_port']
        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        #we are never able to enter this if, showing net graph is super quickly built
        if src_mac not in self.net:

            #####self.net.add_node(src)
            edge_dict={'port': msg.in_port}
            self.logger.debug("Entering the control loop : Received PacketIn: in_port = %r", edge_dict['port'])

            #self.net.add_edge(dpid,src,edge_dict) #to this edge we are attaching a dictionary edge_dict
            #self.net.add_edge(src,dpid)
        if dst in self.net:
            pass
            #print (src in self.net)
            #print nx.shortest_path(self.net,1,4)
            #print nx.shortest_path(self.net,4,1)
            #print nx.shortest_path(self.net,src,4)

            #path=nx.shortest_path(self.net,src,dst)
            #next=path[path.index(dpid)+1]
            #out_port=self.net[dpid][next]['port']
        else:
            self.logger.debug("MAC_port table %r", self.mac_to_port)
            #out_port = ofproto.OFPP_FLOOD

        #####actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time

        #if out_port != ofproto.OFPP_FLOOD:
        #   self.add_flow(datapath, msg.in_port, dst, actions)

        #     out = datapath.ofproto_parser.OFPPacketOut(
        #     datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
        #     actions=actions)
        # datapath.send_msg(out)
        #

    """
    Save the current network graph to a PNG file

    """
    def save_topolog_to_file(self):
        filename='controller_core_network.png'
        #nx.draw(self.net, with_labels=True)

        ###
        #pos = nx.random_layout(self.net)
        ###pos = nx.circular_layout(G)
        # pos = nx.shell_layout(G)
        pos = nx.spring_layout(self.net)
        #pos = nx.graphviz_layout(self.net,prog='dot')
        nx.draw(self.net, pos, with_labels=True , hold= False)
        #nx.draw_graphviz(self.net)
        #nx.draw_circular(self.net, with_labels=True)

        #nx.draw_random(self.net, with_labels=True)
        # doesnt worknx.graphviz(self.net,prog='dot',with_labels=True)
        # A=nx.to_agraph(self.net)
        # A.layout()
        # A.draw('test.png')

        #labels = nx.get_edge_attributes(self.net, 'weight')
        #nx.draw_networkx_edge_labels(self.net, pos, edge_labels=labels) #this will draw weights as well
        ###


        #plt.show() #Do not uncomment this in a realtime application. This will invoke a standalone application to view the graph.
        plt.savefig(filename)
        plt.clf() #this cleans the palette for next time

    def show_graph_stats(self):
        self.logger.debug( "list of edges: self.net.edges %s ",self.net.edges())
        self.logger.debug("list of nodes: \n %r", self.net.nodes())


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
        # self.logger.debug("type(links_list): perentR %r", type(links_list)) #this in log shows  <class 'ryu.topology.switches.LinkState'>
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
        links_onedirection_L=[(link.src.dpid,link.dst.dpid,{'src_port':link.src.port_no, 'dst_port':link.dst.port_no, 'src_dpid': link.src.dpid, 'dst_dpid':link.dst.dpid}) for link in links_list]
        links_opp_direction_L=[(link.dst.dpid, link.src.dpid, {'dst_port': link.dst.port_no, 'src_port':link.src.port_no, 'src_dpid': link.src.dpid, 'dst_dpid':link.dst.dpid}) for link in links_list]

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
        self.show_graph_stats()

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

