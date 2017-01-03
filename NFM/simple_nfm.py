from operator import attrgetter


import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.lib import hub
import json
import threading
from client import client_side


class SimpleNFM(simple_switch_13.SimpleSwitch13):	
	

	neighbourDict = {}	# dictionary to store each switch's neighbours
	flows = {}		# dictionary to store each switch's flows
	bla = threading.Event() # semaphore variable to syncronize between flow request and path computing
	blabla = threading.Event() #semaphore variable to synchronize between port request and ---||---
	switchCounter = 0	# total registered switches
	responsedSwitches = 0	# counter of a round's responded switches
	responsedSwitchesPortStatus = 0 #counter of a round's responded switches of port stats
	DMclient = client_side(" ")
	mininetRunning = False
	pathComponents = {}
	linkBytes = {}
	updateTime = 5
	portDict = {}
	

	def __init__(self, *args, **kwargs):
		super(SimpleNFM, self).__init__(*args, **kwargs)
		self.datapaths = {}
		#self.monitor_thread = hub.spawn(self._monitor)
		self.topology_api_app = self
		#testSend = {'module': 'nfm', 'id': 380,'flow':1,'delay':5567}
		#self.DMclient.postme(testSend)

	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		if self.mininetRunning is False:
			self.monitoring_thread = hub.spawn(self._monitor)
			self.mininetRunning = True
		datapath = ev.datapath
		if ev.state == MAIN_DISPATCHER:
			if datapath.id not in self.datapaths:
				self.logger.debug('registered datapath: %016x', datapath.id)
				self.datapaths[datapath.id] = datapath
		elif ev.state == DEAD_DISPATCHER:
			if datapath.id in self.datapaths:
				self.logger.debug('unregister.datapath: %016x', datapath.id)
				del self.datapaths[datapath.id]
	
	@set_ev_cls(event.EventSwitchEnter)
	def get_topology_data(self, ev):
		switch_list = get_switch(self.topology_api_app, None)
		switches = [switch.dp.id for switch in switch_list]
		links_list = get_link(self.topology_api_app, None)
		links = [(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]
		
		#global self.neighbourDict
		#print "one round"		
		for link in links:
			#self.logger.info("%d %d %s", link[0], link[1], link[2])
			self.logger.debug("Neighbours of switch %s are: ", link[0])
			
			if str(link[0]) in self.neighbourDict:
				nList = self.neighbourDict[str(link[0])]
				link_tuple = {str(link[1]): link[2]}
				if link_tuple not in nList:
 					nList.append(link_tuple)
				self.neighbourDict[str(link[0])] = nList
			else:
				nList = []
				link_tuple = {str(link[1]): link[2]}
				#if link_tuple not in nList:
 				nList.append(link_tuple)
				self.neighbourDict[str(link[0])] = nList
			#self.logger.info(self.neighbourDict)
		#self.logger.info(switches)
		#self.logger.info(links)
		#self.logger.info(self.neighbourDict)
		self.logger.debug("NEIGHBOURS LEARNED...")
		self.switchCounter = len(switches)
		self.logger.debug("TOTAL SWITCHES: %d", len(switches))

	

	def _monitor(self):
		self.bla.set()
		self.blabla.set()
		while True:
			self.logger.debug("REQUESTING FLOW STAT...")
			hub.sleep(self.updateTime)
			
			self.bla.wait()
			self.blabla.wait()
			#self.logger.info("BLA")

			for dp in self.datapaths.values():
				self._request_stats(dp)
			self.bla.clear()
			self.blabla.clear()
			

	def _request_stats(self, datapath):
		self.logger.debug('send stats....')
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)
		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
		datapath.send_msg(req)

	def print_flow_table(self, ev):
		body = ev.msg.body
		#self.logger.info('datapath	'
		#				 ' in-port  eth-dst	    '
		#				 'out-port packets  bytes')
		#self.logger.info('---------------- '
		#				 '-------- ----------------- '
		#				 '-------- -------- --------')
		#self.logger.info(body)
		#self.logger.info("PRINTING TABLE")		
		table_list = []
		for stat in [flow for flow in body if flow.priority >= 0]:
			in_port = -1
			eth_dest = -1
			if 'in_port' in stat.match:
				in_port = stat.match['in_port']
			if 'eth_dst' in stat.match:
				eth_dest = stat.match['eth_dst']
			"""
			self.logger.info('%016x %8x %17s %8x %8d %8d',
							ev.msg.datapath.id,
							in_port, eth_dest,
							stat.instructions[0].actions[0].port,
							stat.packet_count, stat.byte_count)
			"""
			table_list.append([in_port, eth_dest, stat.instructions[0].actions[0].port, stat.packet_count, stat.byte_count])
		self.flows[ev.msg.datapath.id] = table_list
		#self.logger.info(table_list)
		#self.logger.info('\n')
		#getFlows(table_list)
		#self.logger.info(self.flows)
		self.responsedSwitches += 1
		#self.logger.info("FLOW STAT RECEIVED")
		self.logger.debug("FLOW STAT RECEIVED: %d/%d", self.responsedSwitches, self.switchCounter)
		#self.logger.info(self.responsedSwitches)
		"""
		WHEN EVERY SWITCH HAS GIVEN THE NFM ITS FLOW STAT, START CALCULATING THE PATHS
		"""
		if self.responsedSwitches == self.switchCounter:
			self.responsedSwitches = 0
			self.calculatePaths()
			self.bla.set()
		
			
	"""
	CHECK EVERY POSSIBLE LINK TO SEE IF THERE IS A FLOW ON THAT LINK 
	AND COMPUTE THE WHOLE PATHS BETWEEN END HOSTS
	"""
	def calculatePaths(self):
		#TODO: Compute the whole paths between end hosts
		for switchX in range(6):
			for switchY in range(6):
				if switchX is not switchY:
					#self.logger.info("Checking between %d and %d", switchX+1, switchY+1)
					self.checkLink(switchX+1, switchY+1)
		#self.logger.info(self.pathComponents)

	"""
	ALGORITHM: CROSSCHECKING BETWEEN NEIGHBOURS OF THE SWITCHES AND EACH SWITCH'S FLOWS,
			DETERMING THAT A FLOW EXISTS BETWEEN THE TWO GIVEN SWITCHES
	"""
	def checkLink(self, Sx, Sy):
		#TODO
		#DEBUG
		if str(Sx) not in self.neighbourDict:
			self.logger.info("%d not listed in neighbour dictionary", Sx)
			self.logger.info(self.neighbourDict)
		Sx_neighbours = self.neighbourDict[str(Sx)]
		Sy_exists = False
		Sx_port = None	
		for tup in Sx_neighbours:			
			if str(Sy) in tup.viewkeys():
				Sy_exists = True
				Sx_port = tup[str(Sy)]['port']
				break
		if not Sy_exists:
			return False
		Sx_flows = self.flows[Sx]
		#bytes = {}
		for flow in Sx_flows:
			if flow[2] == Sx_port:
				#Determing BW
				path = str(Sx)+" -> "+str(Sy)+"[src_port: "+str(flow[0])+",dst:"+str(flow[1])+"]"
				"""
				if path in bytes:
					linkBytes = bytes[path]
					linkBytes += flow[4]
					bytes[path] = linkBytes
				else:
					bytes[path] = flow[4]
				"""	
				bw = 0			
				if path in self.linkBytes:
					linkBytes = self.linkBytes[path]
					#self.logger.info("%d %d", flow[4], linkBytes)
					#if flow[4] >= linkBytes:
					bw = (flow[4] - linkBytes)/self.updateTime
				else:
					bw = flow[4]/self.updateTime
				self.linkBytes[path] = flow[4]
							
				speed = str(bw*8)+" bit/s"
				if (bw*8) > 1024:
					speed = str((bw*8)/1024)+" Kbit/s"
				elif (bw*8) > (1024*1024):
					speed = str((bw*8)/(1024*1024))+" Mbit/s"
				self.logger.info("Flow exists: %d -> %d with destination: %s. Packets: %d, bytes: %d, bw: %s", Sx, Sy, flow[1], flow[3], flow[4], speed)				
				if flow[1] in self.pathComponents:
					pathList = self.pathComponents[flow[1]]
					if path not in pathList:
						pathList.append(path)
					self.pathComponents[flow[1]] = pathList
				elif flow[1] != -1:
					pathList = [path]
					self.pathComponents[flow[1]] = pathList
				#return True
		
		#for link in bytes:
		#	self.logger.info("BW of link %s: %d bytes/sec", link, bytes[link]/self.updateTime)
		return False


	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		
		self.print_flow_table(ev)
		#self.print_json(ev)			
			

	def print_json(self, ev):
		self.logger.info('datapath id: %016x', ev.msg.datapath.id)
		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
						indent=3, sort_keys=True))

	def print_port_table(self, ev):
		body = ev.msg.body
		
		
		portDictKey = str(ev.msg.datapath.id)
		if portDictKey in self.portDict:
			subDict = self.portDict[portDictKey]
			for stat in sorted(body, key=attrgetter('port_no')):
				subDictKey = str(stat.port_no)
				if subDictKey in subDict:
					tx_bytes = subDict[subDictKey]
					tx_bytes += stat.tx_bytes
					subDict[subDictKey] = tx_bytes
				else:
					subDict[subDictKey] = stat.tx_bytes
			self.portDict[portDictKey] = subDict
		else:
			subDict = {}
			for stat in sorted(body, key=attrgetter('port_no')):
				subDictKey = str(stat.port_no)
				subDict[subDictKey] = stat.tx_bytes
			self.portDict[portDictKey] = subDict

		self.responsedSwitchesPortStatus += 1
		if self.responsedSwitchesPortStatus == self.switchCounter:
			self.responsedSwitchesPortStatus = 0
			self.logger.info("PORT DICT: ")
			self.logger.info(self.portDict)
			self.logger.info("\n")
			self.blabla.set()

		"""
		self.logger.info('datapath	 port	'
						 '  rx-pkts  rx-bytes rx-error '
						 'tx-pkts  tx-bytes tx-error')
		self.logger.info('---------------- -------- '
						 '-------- -------- -------- '
						 '-------- -------- -------')
		for stat in sorted(body, key=attrgetter('port_no')):
			self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
							  ev.msg.datapath.id, stat.port_no,
							  stat.rx_packets, stat.rx_bytes, stat.rx_errors,
							  stat.tx_packets, stat.tx_bytes, stat.tx_errors)	
		"""

	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):
		self.print_port_table(ev)
		#self.logger.info('\n\n')
		#a = 0







