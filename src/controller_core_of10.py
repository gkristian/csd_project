
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
from ryu.lib.mac import haddr_to_bin




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
        self.defines_D = {'bcast_mac':'ff:ff:ff:ff:ff:ff'}
        #adnan 's experiments added
        #self.init_logger()
        self.rxpkts_types_D= {}
        self.logger.debug("controller_core starting up....")


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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)


        dst = eth.dst
        src = eth.src
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
            self.logger.debug("Now learning a node with src mac = %s that is arp broadcasting", src)
            # learn a mac address to avoid FLOOD next time.
            # a 3 column table is maintained: dpid, src_mac, in_port
            self.mac_to_port[dpid][src] = msg.in_port
        else: #this is not an lldp packet, this is not arp broadcast.
            #check if its a valid openflow packet
            self.logger.debug("Is it a valid openflow")
            #do we have this packet in our mac_to_port table
            if dst in self.mac_to_port[dpid]:
                #compute
                #find output to prepaer a flow-mode to all the switches in the path
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
        if src not in self.net:
            self.net.add_node(src)
            edge_dict={'port': msg.in_port}
            self.logger.debug("Received PacketIn: in_port = %r", edge_dict['port'])

            self.net.add_edge(dpid,src,edge_dict) #to this edge we are attaching a dictionary edge_dict
            self.net.add_edge(src,dpid)
        if dst in self.net:
            #print (src in self.net)
            #print nx.shortest_path(self.net,1,4)
            #print nx.shortest_path(self.net,4,1)
            #print nx.shortest_path(self.net,src,4)

            path=nx.shortest_path(self.net,src,dst)   
            next=path[path.index(dpid)+1]
            out_port=self.net[dpid][next]['port']
        else:
            self.logger.debug("MAC_port table %r", self.mac_to_port)
            #out_port = ofproto.OFPP_FLOOD

        #####actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time

        #if out_port != ofproto.OFPP_FLOOD:
        #   self.add_flow(datapath, msg.in_port, dst, actions)

        """out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions)
        datapath.send_msg(out)
        """
    #Below method just populates the nx graph to which above packet-in method just adds src/dst
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        #we reap from two source provided by LLDP based ryu topology api : switch_list and link_list
        #and put the info into a networkx based graph "net"
        #****************** switches *******************
        self.logger.debug("EventSwitchEnter observed: %r", ev)
        switch_list = get_switch(self.topology_api_app, None)

        for s in switch_list:
            self.logger.debug(s.dp.id)
        #print "switch_list dict \n", switch_list.to_dict() #FAILED: no such attributed to_dict()
        switches=[switch.dp.id for switch in switch_list]

        #self.logger.debug("switches is of type: %s", type(switches)) #this shows list
        #self.logger.debug("switches on ls shows None because its just a list has %s", self.ls(switches))
        self.logger.debug ("List of switches %r", switches)



        self.net.add_nodes_from(switches)
        self.logger.debug ("nodes:")
        self.logger.debug( self.net.nodes() )
        self.logger.debug ("edges:")
        self.logger.debug (self.net.edges())

        #print "List of switches"
        #for switch in switch_list:
        #self.ls(switch)
        #print switch
        #self.nodes[self.no_of_nodes] = switch
        #self.no_of_nodes += 1
        #
	    #************** LINKS **************************
        links_list = get_link(self.topology_api_app, None)
        self.logger.debug( "type(links_list): %s",type(links_list) ) #this in log shows  <class 'ryu.topology.switches.LinkState'>
        self.logger.debug("type(links_list): perentR %r", type(links_list)) #this in log shows  <class 'ryu.topology.switches.LinkState'>
        self.logger.debug("links_list: %r", links_list) #multiple
        self.logger.debug("self.ls(links_list): %r", self.ls(links_list)) #this always gives None
        ####self.CSDLOG(links_list)
        #print links_list.to_dict()

        #print links_list

        links = [self.logger.debug("link = %r",link) for link in links_list]
        links_dict = [self.logger.debug("link.to_dict() = %r", link.to_dict()) for link in links_list] #this in log shows as below:
        # link.to_dict() in logs shows {'src':
        #                       {'hw_addr': '06:f3:96:df:a2:6c', 'name': u'l1-eth1', 'port_no': '00000001',
        #                        'dpid': '0000000000000015'},
        #                   'dst': {'hw_addr': 'ee:d9:44:eb:c4:76', 'name': u's1-eth3', 'port_no': '00000003',
        #                           'dpid': '000000000000000b'}}

        links_type = [self.logger.debug("type(link) = %r", type(link)) for link in links_list] #this shows <ryu.topology.switches.Link

        #link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]

        # Since "net" is a Directional Graph so we need to add two ordered pairs (1,2) and (2,1) for a link between s1 and s2.
        links=[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]
        #print links
        self.net.add_edges_from(links) #these are ordered pairs like if s1 and s2 are connected u will get (1,2),(2,1) that 1 -> and 2->1
        links=[(link.dst.dpid,link.src.dpid,{'port':link.dst.port_no}) for link in links_list]
        #print links
        self.net.add_edges_from(links)
        self.logger.debug( "list of edges: self.net.edges %s ",self.net.edges())

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

