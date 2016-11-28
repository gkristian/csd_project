from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
import networkx as nx
import time
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
import simple_switch_13



class TestController(simple_switch_13.SimpleSwitch13):
	app_manager._CONTEXTS = {
		'network' : nx.DiGraph([(1,'00:00:00:00:00:01',{'src_port':2,'dst_port':2,'src_dpid':1,'dst_dpid':'00:00:00:00:00:01','bw':5}),('00:00:00:00:00:01',1,{'src_port':2,'dst_port':2,'src_dpid':'00:00:00:00:00:01','dst_dpid':1,'bw':5}), (2,'00:00:00:00:00:02',{'src_port':2,'dst_port':2,'src_dpid':2,'dst_dpid':'00:00:00:00:00:02','bw':5}), ('00:00:00:00:00:02',2,{'src_port':2,'dst_port':2,'src_dpid':'00:00:00:00:00:02','dst_dpid':2,'bw':5}),
(1,2,{'src_port':1,'dst_port':1,'src_dpid':1,'dst_dpid':2,'bw':10}),
(2,1,{'src_port':1,'dst_port':1,'src_dpid':2,'dst_dpid':1,'bw':10})])
	}
	def __init__(self, *args, **kwargs):
		super(TestController, self).__init__(*args, **kwargs)
	

	"""
		S1  --- S2
		|       |
		H1      H2
	"""

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		self.logger.info("FEATURES")

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		self.logger.info("PACKET IN")
		self.logger.info(ev.msg.datapath.id)
		


