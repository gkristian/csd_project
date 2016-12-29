# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
#below ahs duplicates

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




class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    net = nx.DiGraph()
    bootstrap_complete= True
    app_manager._CONTEXTS = {'network': net }
    app_manager._CONTEXTS = {'bootstrap_complete': bootstrap_complete }

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)

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
