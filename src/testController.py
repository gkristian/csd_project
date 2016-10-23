from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
import networkx as nx
from client import client_side
import time







class TestController(app_manager.RyuApp):
	
	app_manager._CONTEXTS = {
		'network' : nx.DiGraph([('1-1','2-1',{'bw':10}),('2-1','1-1',{'bw':10}),('1-2','3-2',{'bw':30}),('3-2','1-2',{'bw':30}),('2-2','3-1',{'bw':20}),('3-1','2-2',{'bw':20})])
		}
	
	def __init__(self, *args, **kwargs):
		super(TestController, self).__init__(*args, **kwargs)
		self.lastTimeRequest = int(round(time.time()*1000))
		self.linkUtilizations = {}
		self.DMclient = client_side(" ")
		#hub.spawn(self.fetchNFMData())
		#self.fetchingThread.start()
		#self.fe()

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		#self.logger.info("PACKET_IN")
		#self.logger.info(int(round(time.time()*1000)))
		currentMillis = int(round(time.time()*1000))
		
		#Every 10 seconds, update flow table
		if currentMillis - self.lastTimeRequest > 10000:
			self.lastTimeRequest = currentMillis
			#response = self.DMclient.getme({'module':'nfm', 'timestamp':0,'keylist':['link_utilization']})
			self.logger.info("REQUEST FLOW DATA")


