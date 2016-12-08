
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
import matplotlib.pyplot as plt
from ryu.lib.mac import haddr_to_bin
import time
#from collections import deque #used to remove first and last element from the list efficently




class ProjectController(app_manager.RyuApp):
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
        super(ProjectController, self).__init__(*args, **kwargs)
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
        self.defines_D = {'bcast_mac':'ff:ff:ff:ff:ff:ff', 'bootstrap_in_progress': True,'flow_table_strategy_semi_proactive': True}
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

    # Handy function that lists all attributes in the given object
    def ls(self,obj):
        print("\n".join([x for x in dir(obj) if x[0] != "_"]))


    """
    Table miss flow entry looks like below:
    mininet> sh ovs-ofctl -O OpenFlow13 dump-flows l3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=0.352s, table=0, n_packets=1, n_bytes=60, priority=65535,dl_dst=01:80:c2:00:00:0e,dl_type=0x88cc actions=CONTROLLER:65535
     cookie=0x0, duration=0.399s, table=0, n_packets=2, n_bytes=120, priority=0 actions=CONTROLLER:65535

    mininet> sh ovs-ofctl -O OpenFlow13 dump-flows l1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=2.572s, table=0, n_packets=1, n_bytes=60, priority=65535,dl_dst=01:80:c2:00:00:0e,dl_type=0x88cc actions=CONTROLLER:65535
     cookie=0x0, duration=2.627s, table=0, n_packets=2, n_bytes=120, priority=0 actions=CONTROLLER:65535

    """
    # An openflow v1.3 implementation must install a table-miss flow entry rule while version 1.0 doesn't require this.
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Openflow v1.3 requires that table-miss flow entry rule be installed by the controller to direct the packets to the controller that do not match
        existing rule.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    #Openflow v1.3 add_flow
    def add_flow(self, datapath, priority, match, actions):
        """
            add_flow for openflow v1.3
            Note that it installs an instruction from the actions input.
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)
	#"""
	# add_flow for openflowv1
	# """
    # def add_flow(self, datapath, in_port, dst, actions):
    #     ofproto = datapath.ofproto
    #
    #     match = datapath.ofproto_parser.OFPMatch(
    #         in_port=in_port, dl_dst=haddr_to_bin(dst))
    #
    #     mod = datapath.ofproto_parser.OFPFlowMod(
    #         datapath=datapath, match=match, cookie=0,
    #         command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
    #         priority=ofproto.OFP_DEFAULT_PRIORITY,
    #         flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
    #     datapath.send_msg(mod)
    def shortest_path(self,src_node,dst_node):
        sp_L = nx.shortest_path(self.net,src_node, dst_node, weighted = True) # L indicates it is a list of nodes e.g. [1,2,3,4]
        return sp_L
    def __check_bootstrap_completion(self):
        'has the criteria for bootstrap completion met, if yes then set the completion flag'
        if self.defines_D['bootstrap_in_progress']:
            if (self.network_bootstrap_type == 0):
                if int(time.time()) - self.epoc_starttime > self.network_bootstrap_time:
                    self.defines_D['bootstrap_in_progress'] = False
                    self.logger.debug("Bootstrap type %d just Completed", self.network_bootstrap_type)
            if (self.network_bootstrap_type == 1):
                if len(self.l2_mac2ip_table) == self.network_bootstrap_discovery_count:
                    self.defines_D['bootstrap_in_progress'] = False
                    self.logger.debug("Bootstrap type %d just Completed", self.network_bootstrap_type)

    #@staticmethod #I dont know how RYU shall deal with staticmethods though its use is justified here so I ll stick to what has worked in past
    def __remove_macs_from_shortest_path(self,spath):
        """
        :param spath:
        this function is not tested yet
        returns a list after having removed first and last element from spath which are src_mac and dst_mac respectively
        this must be done in the most efficent manner python has to offer so we use deque,  see timeit benchmarks at below URL
        URL  : http://stackoverflow.com/questions/33626623/the-most-efficient-way-to-remove-first-n-elements-in-a-python-list
        :return:
        """
        #spath_dq = collections.deque(spath) #this was giving ERROR #CSD CC 2 which makes sense
        spath_dq = deque(spath)
        dst_mac= spath_dq.pop()  # removes last element from the list
        src_mac = spath_dq.popleft()  # removes first element from the list, not that classical python list manipulations are slow as compared to this
        return (src_mac, dst_mac, list(spath_dq))

    def __install_path_flow(self,spath_with_macs):
        """
        input is a networkx shortest path list of the format [src_mac, switch1, sw2,..., swN, dst_mac]
        it installs flows in all the switches1..N
        :rtype: Boolean
        :param spath
        :return: true if operation was successful or else false
        """
        self.logger.debug("Considering path %r", spath_with_macs)
        #we don't do src_mac=spath[0] since I  have already done a deque operation of pops and I just dont want to repeat it
        ########### below works but we want to avoid it
        ###########(src_mac,dst_mac,spath_without_macs) = self.__remove_macs_from_shortest_path(spath_with_macs)
        ###########self.logger.debug("install_path_flow: src_mac = %r, dst_mac = %r, spath_without_macs = %r", src_mac, dst_mac, spath_without_macs)

        #for dpid in spath_without_macs:
        #n = len(spath_without_macs) #nr of switches in the path
        n = len(spath_with_macs)  # nr of switches in the path + 2 i.e.including src mac and dst mac
        i = 1
        src_mac = spath_with_macs[i-1]  # during first iterations its the src_mac
        dst_mac = spath_with_macs[n-1]
        while (i <= n-2): # n-1 is the last node which is the dst mac
            self.logger.debug("Installing rule on %r nth switch in path ", i)
            sw_b = spath_with_macs[i];  # this switch already has flow installed during first iteration
            sw_c = spath_with_macs[i + 1]  # on sw_b , flow is to be installed
            sw_a = spath_with_macs[i - 1]  #

            in_port = self.net.edge[sw_a][sw_b]['dst_port']
            out_port = self.net.edge[sw_b][sw_c]['src_port']
            self.__send_flow_mod(sw_b, src_mac, in_port, dst_mac, out_port)
            i = i + 1

        #INSTALL REVERSE ROUTES

        dst_mac = spath_with_macs[0]  # during first iterations its the src_mac
        src_mac = spath_with_macs[n - 1]
        i = n - 2
        while (i >= 1):  #  1 is the first switch
            self.logger.debug("Installing reverse rule on %r nth switch in path ", i)
            sw_b = spath_with_macs[i];  # this switch already has flow installed during first iteration
            sw_c = spath_with_macs[i - 1]  # on sw_b , flow is to be installed
            sw_a = spath_with_macs[i + 1]  #

            in_port = self.net.edge[sw_a][sw_b]['dst_port']
            out_port = self.net.edge[sw_b][sw_c]['src_port']
            self.__send_flow_mod(sw_b, src_mac, in_port, dst_mac, out_port)
            i = i - 1

            """
            self.logger.debug("Installing rule on %r nth switch in path ", i)
            if i == 1: # first loop iteration i.e. installing rules on switch connected to src_mac

                sw_a = spath_with_macs[i] #during last iteration its dst_mac
                sw_b = spath_with_macs[i+1]  # during last iteration its dst_mac
                in_port = self.net.edge[src_mac][sw_a]['dst_port']
                out_port = self.net.edge[sw_a][sw_b]['src_port']
                self.__send_flow_mod(sw_a, src_mac, in_port, dst_mac, out_port)
            else:

                if i == n-2: #last loop iteration i.e. installing rules on switch to which dst_mac is connected

                    sw_b = spath_with_macs[n-2]
                    sw_a = spath_with_macs[n-3]
                    in_port = self.net.edge[sw_a][sw_b]['dst_port']
                    out_port = self.net.edge[sw_b][dst_mac]['src_port']
                    self.__send_flow_mod(sw_b, src_mac, in_port, dst_mac, out_port)
                else:
                    sw_b = spath_with_macs[i] ; # this switch already has flow installed during first iteration
                    sw_c = spath_with_macs[i+1]  # on sw_b , flow is to be installed
                    sw_a = spath_with_macs[i-1]  #

                    in_port = self.net.edge[sw_a][sw_b]['dst_port']
                    out_port = self.net.edge[sw_b][sw_c]['src_port']
                    self.__send_flow_mod(sw_b, src_mac, in_port, dst_mac, out_port)
            i = i + 1
            """



    #def __install_flow(self, dpid, src_mac, dst_mac): #spath is without any macs, only contains switch dpids
    #    self.__send_flow_mod(self.datapathDb(dpid), src_mac,in_port, dst_mac, out_port) #, in_port, out_port)


    # below method sourced from the ryu api doc at:http://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#modify-state-messages
    # added dst_mac which is a string e.g. 'ff:ff:ff:ff:ff:ff'
    #not using in_port for now as a criteria for routing but may be later.

    def __send_flow_mod(self, dpid, src_mac, in_port, dst_mac, out_port):
        self.logger.debug("FLOWMOD_1 : flow_rule to install , dpid = %r, %r -> %r ====TO=== %r -> %r ", dpid, src_mac, in_port, dst_mac,out_port)
        datapath = self.datapathDb[dpid]
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        cookie = cookie_mask = 0
        table_id = 0
        idle_timeout = hard_timeout = 0
        priority = 32768 #this is default priority assumed if no priority specified
        buffer_id = ofp.OFP_NO_BUFFER
        match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=dst_mac, eth_src=src_mac)  # 'ff:ff:ff:ff:ff:ff'
        # match = ofp_parser.OFPMatch(
        #     in_port=1,
        #     eth_dst=dst_mac,
        #     eth_src=src_mac,
        #     arp_cp='',... see notebook flags or ctr-q up at OFPMatch)  # 'ff:ff:ff:ff:ff:ff'
        #
        #actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)]
        actions = [ofp_parser.OFPActionOutput(out_port)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                 actions)]
        req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask,
                                    table_id, ofp.OFPFC_ADD,
                                    idle_timeout, hard_timeout,
                                    priority, buffer_id,
                                    ofp.OFPP_ANY, ofp.OFPG_ANY,
                                    ofp.OFPFF_SEND_FLOW_REM,
                                    match, inst)
        datapath.send_msg(req)
    def __save_datapath(self,datapath):
        #do we need to check if the datapath is recorded from the most recent packet received by the controller. currently this is the case as we keep overwriting it.
        #we could have some check to verify if its a valid datapath
        self.datapathDb[datapath.id]=datapath
    def __isPathNotAlreadyInstalled(self,spath):
        spath_as_tuple = tuple(spath)
        if spath_as_tuple in self.already_installed_paths_SET: #set can only contain a hashable immutable object, a list is not acceptable.
            #this computed shortest path is already installed in the switches
            return True
        else:

            #A list cannot be added to a set because it is not hashable, while a tuple can be added cuz its not mutable but hashable.
            self.already_installed_paths_SET.add(spath_as_tuple)
            return False



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.print_l2_table()
        self.__check_bootstrap_completion()
        self.save_topolog_to_file() #this should go away in the production version and above lines be uncommented in a proper manner

        msg = ev.msg
        datapath = msg.datapath
        #we save all datapaths in a dictionary so that the controller can install flowmod rules in any switch it wants
        self.__save_datapath(datapath)
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']
        if in_port:#if not empty
            #self.logger.debug("Received Packet-IN and in_port is not empty")
            pass
        else:
            self.logger.error("EMPTY in_port in Packet-IN message")

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)


        dst_mac = pkt_eth.dst
        src_mac = pkt_eth.src
        dpid = datapath.id
        #note the switch dpid in our table
        #self.mac_to_port.setdefault(dpid, {})

        if pkt_eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packel
            return


        # self.logger.debug("OFPP_FLOOD = %r",ofproto.OFPP_FLOOD) #only when pingall done, then it gave OFPP_FLOOD = 65531
        # #note that 65531 decimal in hex is  FFFB
        # self.logger.debug("OFPP_FLOOD in hex = %x",ofproto.OFPP_FLOOD)  # only when pingall done, this gave fffb
        # self.logger.debug("haddr_to_bin(dst) = %r",haddr_to_bin(dst_mac)) #this on pingall gave: '\xff\xff\xff\xff\xff\xff'

        if dst_mac == self.defines_D['bcast_mac']: #if dst == 'ff:ff:ff:ff:ff:ff' means its a host that is flooding the network, we gotta learn it
            self.logger.debug("broadcast received from src mac = %s , switch dpid = %r at in_port = %r", src_mac, dpid, msg.match['in_port'])

            #Below are two ways to make sure that an ARP header is there in the broadcast packet received
            #if eth.ethertype != ether_types.ETH_TYPE_ARP:
            #    self.logger.warning("Missing ARP header in broadcast packet. Unable to learn. Aborting execution of broadcast loop in code")
            #    return

            ############################# Below was discarded idea of representing graph nodes: srcdpid-srcport, dstdpid-dstport that lead to such edges in topology ('3-1', '00:00:00:00:00:03'), ('2-1', '00:00:00:00:00:02')
            ####self.net.add_edge(str(dpid)+ '-' + str(msg.in_port), str(src),{'end_host': 1}) #-1 indicates its a host
            ############################# The way of representing the graph nodes

            # broadcast arp must have arp header
            pkt_arp = pkt.get_protocol(arp.arp)  # this object does not have any indexes so no [0]
            if not pkt_arp:
                return

            if src_mac not in self.net: #learn it
                self.logger.debug("LEARNING : learning a new src_mac = %r for the first time ", src_mac)
                #self.logger.debug("our current l2_table is %r", self.l2_dpid_table)
                #open for IP src and IP dst of ARP broadcast: we  associate src mac learn from source and use destination IP to route to correct switch


                # learn a mac address to avoid FLOOD next time.
                # a 3 column table is maintained: dpid, src_mac, in_port
                # self.mac_to_port[dpid][src_mac]['port'] #this is illegal
                #below is illegal
                #self.mac_to_port[dpid][src_mac].setdefault('port',msg.in_port)  #msg.match['port'] is this a v3 v1 thing?
                ###self.mac_to_port[dpid].setdefault(src_mac, {})
                #now start addings keys to this setdefaulted dict with key srcmac
                #self.mac_to_port[dpid][src_mac]['port']= msg.in_port  # msg.match['port'] is this a v3 v1 thing?
                ####self.mac_to_port[dpid][src_mac]['port'] = msg.match['port']
                ####self.mac_to_port[dpid][src_mac]['port'] = msg.match['port']
                #is this a v3 v1 thing?
                #open the arp packet for IP adddress


                # now u can add keys to this above setdefaulted dict on the fly
                # self.mac_to_port[dpid][src_mac]['ip']='some_value' #this is legal now, thats why we used setdefault for
                # since its destined to bcast address, arp header must be there so no need to check IF ARP HEADER PRESENT
                #self.mac_to_port[dpid][src_mac]['ip'] = pkt_arp.src_ip  # this is legal because we are appending a key in this C-array like way to an existing setdefaulted dict
                #self.l2_lookup_table[dpid] ={src_mac: {}}
                #self.l2_lookup_table[dpid][src_mac]={'in_port':in_port, 'ip':pkt_arp.src_ip}

                #below three tables could be improved by putting all info in one object and use getters and setters but I dont know if it would be as efficent as having below dictionary as a lookup table
                self.l2_dpid_table[dpid]={src_mac:{'in_port':msg.match['in_port'] , 'ip':pkt_arp.src_ip}}
                self.l2_ip2mac_table[pkt_arp.src_ip]=src_mac
                self.l2_mac2ip_table[src_mac]=pkt_arp.src_ip


                self.logger.debug("LEARNING : ARP extractions show about packet details as : arp.src_ip = %r , arp.dst_ip = %r , arp.opcode (1 for Request)  = %r  ", pkt_arp.src_ip, pkt_arp.dst_ip, pkt_arp.opcode)
                #since its a directonal graph so we need to add two pairs for every single links i.e in each direction

                self.net.add_edge(src_mac, dpid,
                                  {'src_port': msg.match['in_port'] , 'dst_port': msg.match['in_port'] ,
                                   'src_dpid': src_mac, 'dst_dpid': dpid, 'end_host': True,
                                   'ip': pkt_arp.src_ip})  # src is the src mac

                self.net.add_edge(dpid, src_mac,
                                  {'src_port': msg.match['in_port'], 'dst_port': msg.match['in_port'],
                                   'src_dpid': dpid, 'dst_dpid': src_mac, 'end_host': True})  # src is the src mac

                self.print_l2_table()

                # self._handle_arp(datapath, port, pkt_ethernet, pkt_arp)
                # if eth.ethertype == ether_types.ETH_TYPE_ARP:
                # extract the src and dst IP address
                # arp = pkt.get_protocol(ethernet.)
                # get IPs from ARP packet
                # arp = pkt.get_protocol(arp..src_ip
                # a=pkt.arp.arp_ip
                # self.logger.debug("%r",a)
                # return

            else:
                if pkt_arp.opcode != arp.ARP_REQUEST:
                    self.logger.debug("IGNORING packet as its not an arp request")
                    return
                self.logger.debug(
                    "RX_BCAST_SRC_MAC_ALREADY_LEARNT: Received a broadcast packet with source mac alrd in our l2_table, creating arp reply and attaching to OF packet_out")
                #have we learnt the IP in arp.dst_ip header ie. do we know its mac yet
                if not pkt_arp.dst_ip in self.l2_ip2mac_table:
                    self.logger.debug("RX_BCAST..:Src Mac known but havent learnt the target IP yet i.e. arp.dst_ip's mac yet. Return")
                    return

                # get  mac of the dst ip in arp header
                mac_of_arp_dst_ip= self.l2_ip2mac_table[pkt_arp.dst_ip]
                ip_of_arp_dst_mac = self.l2_mac2ip_table[mac_of_arp_dst_ip]
                self.logger.debug("KEY1 : Found dst_mac %r for arp header dst ip %r , puttin in arp reply",mac_of_arp_dst_ip , pkt_arp.dst_ip)
                new_pkt = packet.Packet()
                new_pkt.add_protocol(ethernet.ethernet(ethertype=pkt_eth.ethertype,
                                                   dst=pkt_eth.src,
                                                   src=mac_of_arp_dst_ip))
                new_pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                         src_mac=mac_of_arp_dst_ip,
                                         src_ip=ip_of_arp_dst_mac,
                                         dst_mac=src_mac,
                                         dst_ip=pkt_arp.src_ip))
                self.logger.debug("Crafting an ARP reply") #pkt_arp.src_mac

                #self._send_packet(datapath, self.l2_dpid_table[dpid][src_mac]['in_port'], new_pkt) #dpid= datapath.id the switch the packet in came from we want to reply on that switch
                self._send_packet(datapath, in_port,new_pkt)  # dpid= datapath.id the switch the packet in came from we want to reply on that switch
                self.logger.debug("Sending arp reply reply done")


        else: #if dst_mac is not broadcat rather some specific address
            #either we have already learnt this address
            self.logger.info("RX_NO_BCAST_ONLY_TARGETED_DST_MAC : compute shortest path and install flows if bstrap completed")
            # This is if block ensures that code after it only gets executed once the network has bootstraped i.e. bootstrap time limit has reached
            if self.defines_D['bootstrap_in_progress']:
                self.logger.info("RX_NO_BCddAST_ONLY_TARGETED_DST_MAC : Sorry network bootstrap still in progress not computing spath , not installing any flows")
                #if int(time.time()) - self.epoc_starttime > self.network_bootstrap_time:
                #    self.defines_D['bootstrap_in_progress'] = False
                return #below code wont get executed during network bootstrap

            self.logger.debug("RX_NO_BCAST_ONLY_TARGETED_DST_MAC : Network Bootstrap Completed. Proceeding with shortest path calculation")

            if dst_mac in self.net:
                self.logger.debug("RX_NO_BCAST_ONLY_TARGETED_DST_MAC: ALREADY_LEARNT: Received ARP to specific dst mac %r that exist in our graph", dst_mac)
                self.logger.debug("Do we have a path to this destination mac? src= %r , dst = %r ",dst_mac,src_mac)
                if not nx.has_path(self.net,src_mac,dst_mac): #if returned False we abort
                    #Above line once caused error CSD_CC_1 reported in ERRORS.txt
                    self.logger.debug("Cannot find path from src mac %r to dst_mac %r, returning ie. doing nothing more",src_mac,dst_mac)
                    return
                #dst mac  is in our topology graph
                spath=nx.shortest_path(self.net,src_mac,dst_mac)


                self.logger.debug("Found shortest path from src mac %r to dst mac %r as %r", src_mac, dst_mac,spath)
                if self.__isPathNotAlreadyInstalled(spath):
                    self.logger.debug("Installing path : %r", spath)
                    self.__install_path_flow(spath)

                #lookup dst mac in our graph, has_path()
                #if yes find path
                #install_path_flows(path)
                # print (src in self.net)
                # print nx.shortest_path(self.net,1,4)
                # print nx.shortest_path(self.net,4,1)
                # print nx.shortest_path(self.net,src,4)
                # path=nx.shortest_path(self.net,src,dst)
                # next=path[path.index(dpid)+1]
                # out_port=self.net[dpid][next]['port']
                # else:
                #    self.logger.debug("MAC_port table %r", self.mac_to_port)
                # out_port = ofproto.OFPP_FLOOD

                #####actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

                # install a flow to avoid packet_in next time

                # if out_port != ofproto.OFPP_FLOOD:
                #   self.add_flow(datapath, msg.in_port, dst, actions)

                #     out = datapath.ofproto_parser.OFPPacketOut(
                #     datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
                #     actions=actions)
                # datapath.send_msg(out)

                #pass

            else: #this is not an lldp packet, this is not arp broadcast, the dst mac is not known but is not broadcast either
                #check if its a valid openflow packet
                self.logger.debug("LEARN_NEW_MAC dst_mac=%r src_mac=%r ", dst_mac,src_mac)
                #self.logger.debug("NEW_SPECIFIC_DST_MAC: We see some traffic - it cant be LLDP though")
                self.print_l2_table()


            #here we get dst mac to be fffff all the time

            # #Is            it            a            valid            openflow - check msg len
            # #do we have this packet in our mac_to_port table
            # if dst_mac in self.mac_to_port[dpid]:
            #     #compute
            #     #find output to prepaer a flow-mod to all the switches in the path
            #     #this outport just tells
            #     #route this packet to switch dpid's out_port
            #
            #     #out_port = self.mac_to_port[dpid][dst_mac]
            #
            #     pass
            # #else:
            #     #we have no path to the destination mac address, we ll just wait and wont flood the network.
            #     #pass

            #self.logger("type of msg.in_port is %s",type(msg.in_port))
            #self.logger.debug("Received PacketIn: dpid = %r , in_port = %r , srcmac= %r, dstmac = %r , packet_type = %r",dpid, msg.match['in_port'] , src,dst, eth.ethertype)
            #print "Received PacketIn: dpid = ", dpid, "srcmac=", src, "dstmac = ", dst, "packet_type = ", eth.ethertype
            #store in a dict what types of packets received and how many
            #uncomment following till
            # if pkt_eth.ethertype in self.rxpkts_types_D:
            #     self.rxpkts_types_D[pkt_eth.ethertype] += 1
            # else:
            #     self.rxpkts_types_D.setdefault(pkt_eth.ethertype,1) #for dictionary D, against a key eth.ethertype, set a default value 1
            # till HERE when u wanna develop a statistics counter

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
            # if src_mac not in self.net:
            #
            #     #####self.net.add_node(src)
            #     edge_dict={'port': msg.in_port}
            #     self.logger.debug("Entering the control loop : Received PacketIn: in_port = %r", edge_dict['port'])

                #self.net.add_edge(dpid,src,edge_dict) #to this edge we are attaching a dictionary edge_dict
                #self.net.add_edge(src,dpid)
            #if dst_mac in self.net:
            #   pass
            #    self.logger.debug("dst mac in our graph")

            self.show_graph_stats()

    """
    Save the current network graph to a PNG file

    """
    def save_topolog_to_file(self):
        filename='network_with_dst_port.png'
        #nx.draw(self.net, with_labels=True)

        ###
        #pos = nx.random_layout(self.net)
        ###pos = nx.circular_layout(G)
        # pos = nx.shell_layout(G)
        pos = nx.spring_layout(self.net)
        #pos = nx.graphviz_layout(self.net,prog='dot')
        nx.draw(self.net, pos, with_labels=True , hold= False)
        #print in_port and out_port as well
        label_src = nx.get_edge_attributes(self.net, 'src_port')
        nx.draw_networkx_edge_labels(self.net, pos, edge_labels=label_src)
        plt.savefig("network_with_src_port.png")
        label_dst = nx.get_edge_attributes(self.net, 'dst_port')
        nx.draw_networkx_edge_labels(self.net, pos, edge_labels=label_dst)


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
        plt.clf() #this cleans the palette for the next time


    def show_graph_stats(self):
        self.logger.debug( "list of edges: self.net.edges %s ",self.net.edges())
        self.logger.debug("list of nodes: \n %r", self.net.nodes())
        self.logger.debug("l2_lookup_table : %r", self.l2_dpid_table)
        #self.logger.debug("show edge data LOT of output: %r",self.net())

        self.print_l2_table()
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
        links_onedirection_L=[(link.src.dpid,link.dst.dpid,{'src_port':link.src.port_no, 'dst_port':link.dst.port_no, 'src_name': link.src.name, 'dst_name':link.dst.name}) for link in links_list]
        links_opp_direction_L=[(link.dst.dpid, link.src.dpid, {'dst_port': link.dst.port_no, 'src_port':link.src.port_no, 'src_name': link.src.name, 'dst_name':link.dst.name}) for link in links_list]

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



