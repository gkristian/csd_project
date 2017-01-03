from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
import networkx as nx
from client import client_side
import time
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp







class TestController(app_manager.RyuApp):
	"""
	app_manager._CONTEXTS = {
		'network' : nx.DiGraph([(1,'00:00:00:00:00:01',{'src_port':1,'dst_port':1,'src_dpid':1,'dst_dpid':'00:00:00:00:00:01','bw':100}),('00:00:00:00:00:01',1,{'src_port':1,'dst_port':1,'src_dpid':'00:00:00:00:00:01','dst_dpid':1,'bw':100}), (1,'00:00:00:00:00:02',{'src_port':2,'dst_port':2,'src_dpid':1,'dst_dpid':'00:00:00:00:00:02','bw':100}), ('00:00:00:00:00:02',1,{'src_port':2,'dst_port':2,'src_dpid':'00:00:00:00:00:02','dst_dpid':1,'bw':100})])
	}
	"""
	app_manager._CONTEXTS = {
		#'network' : nx.DiGraph([('1-1','2-1',{'bw':10}),('2-1','1-1',{'bw':10}),('1-2','3-2',{'bw':30}),('3-2','1-2',{'bw':30}),('2-2','3-1',{'bw':20}),('3-1','2-2',{'bw':20})])
		'network' : nx.DiGraph([(1,2,{'src_port':1,'dst_port':1,'src_dpid':1,'dst_dpid':2,'bw':100}),(1,3,{'src_port':2,'dst_port':1,'src_dpid':1,'dst_dpid':3,'bw':100}),(1,4,{'src_port':3,'dst_port':1,'src_dpid':1,'dst_dpid':4,'bw':100}),(2,5,{'src_port':3,'dst_port':1,'src_dpid':2,'dst_dpid':5,'bw':10}),(2,3,{'src_port':2,'dst_port':2,'src_dpid':2,'dst_dpid':3,'bw':10}),(3,4,{'src_port':3,'dst_port':2,'src_dpid':3,'dst_dpid':4,'bw':10}),(2,6,{'src_port':4,'dst_port':1,'src_dpid':2,'dst_dpid':6,'bw':10}),(3,6,{'src_port':4,'dst_port':2,'src_dpid':3,'dst_dpid':6,'bw':10}),(3,8,{'src_port':5,'dst_port':1,'src_dpid':3,'dst_dpid':8,'bw':10}),(4,7,{'src_port':3,'dst_port':1,'src_dpid':4,'dst_dpid':7,'bw':10}),(4,8,{'src_port':4,'dst_port':2,'src_dpid':4,'dst_dpid':8,'bw':10}),(5,6,{'src_port':2,'dst_port':3,'src_dpid':5,'dst_dpid':6,'bw':10}),(6,7,{'src_port':4,'dst_port':2,'src_dpid':6,'dst_dpid':7,'bw':5}),(7,8,{'src_port':3,'dst_port':3,'src_dpid':7,'dst_dpid':8,'bw':5}),(5,'00:00:00:00:01:01',{'src_port':3,'dst_port':3,'src_dpid':5,'dst_dpid':'00:00:00:00:01:01','bw':5}),(7,'00:00:00:00:03:01',{'src_port':4,'dst_port':4,'src_dpid':7,'dst_dpid':'00:00:00:00:03:01','bw':5}),(2,1,{'src_port':1,'dst_port':1,'src_dpid':2,'dst_dpid':1,'bw':100}),(3,1,{'src_port':1,'dst_port':2,'src_dpid':3,'dst_dpid':1,'bw':100}),(4,1,{'src_port':1,'dst_port':3,'src_dpid':4,'dst_dpid':1,'bw':100}),(5,2,{'src_port':1,'dst_port':3,'src_dpid':5,'dst_dpid':2,'bw':10}),(3,2,{'src_port':2,'dst_port':2,'src_dpid':3,'dst_dpid':2,'bw':10}),(4,3,{'src_port':2,'dst_port':3,'src_dpid':4,'dst_dpid':3,'bw':10}),(6,2,{'src_port':1,'dst_port':4,'src_dpid':6,'dst_dpid':2,'bw':10}),(6,3,{'src_port':2,'dst_port':4,'src_dpid':6,'dst_dpid':3,'bw':10}),(8,3,{'src_port':1,'dst_port':5,'src_dpid':8,'dst_dpid':3,'bw':10}),(7,4,{'src_port':1,'dst_port':3,'src_dpid':7,'dst_dpid':4,'bw':10}),(8,4,{'src_port':2,'dst_port':4,'src_dpid':8,'dst_dpid':4,'bw':10}),(6,5,{'src_port':3,'dst_port':2,'src_dpid':6,'dst_dpid':5,'bw':10}),(7,6,{'src_port':2,'dst_port':4,'src_dpid':7,'dst_dpid':6,'bw':5}),(8,7,{'src_port':3,'dst_port':3,'src_dpid':8,'dst_dpid':7,'bw':5}),('00:00:00:00:01:01',5,{'src_port':3,'dst_port':3,'src_dpid':'00:00:00:00:01:01','dst_dpid':5,'bw':5}),('00:00:00:00:03:01',7,{'src_port':4,'dst_port':4,'src_dpid':'00:00:00:00:03:01','dst_dpid':7,'bw':5})])

		}
	
	def __init__(self, *args, **kwargs):
		super(TestController, self).__init__(*args, **kwargs)
		self.lastTimeRequest = int(round(time.time()*1000))
		self.linkUtilizations = {}
		self.DMclient = client_side(" ")
		
		#hub.spawn(self.fetchNFMData())
		#self.fetchingThread.start()
		#self.fe()
	
	def _print(self, message):
		self.logger.info("[CONTROLLER] "+message)
	
	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		#self.logger.info("PACKET_IN")
		#self.logger.info(int(round(time.time()*1000)))

		"""
		msg = ev.msg
		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocols(ethernet.ethernet)[0]
		arp_pkt = pkt.get_protocol(arp.arp)
		if arp_pkt:
			self.logger.info("ARP PACKET")
			self.logger.info(arp_pkt)
		#in_port = msg.match['in_port']
		#if eth.ethertype == 0x0806:
		#	match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
		"""
		currentMillis = int(round(time.time()*1000))
		
		#Every 10 seconds, update flow table
		if currentMillis - self.lastTimeRequest > 10000:
			self.lastTimeRequest = currentMillis
			self._print("ATTEMPTING TO FETCH DATA FROM DB")
			#self.logger.info("CONTROLLER ATTEMPTING A DB REQUEST")
			try:
				#response = self.DMclient.getme({'module':'nfm', 'timestamp':0,'keylist':['link_utilization']})
				self._print("RECEIVED FLOW DATA: ")
				#self._print(str(response))				
				#self.logger.info("RECEIVED FLOW DATA:")
				#self.logger.info(response)

				
			except:
				self._print("NO DATA IN DB")
				#self.logger.info("NO DATA IN DB")
			


