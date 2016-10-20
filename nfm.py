from operator import attrgetter


import simple_switch_13
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_all_link
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub
import json
import threading
from client import client_side


class NFM(simple_switch_13.SimpleSwitch13):	
	

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
	updateTime = 10
	portDict = {}
	switches = []
	

	def __init__(self, *args, **kwargs):
		super(NFM, self).__init__(*args, **kwargs)
		self.datapaths = {}
		#self.monitor_thread = hub.spawn(self._monitor)
		self.topology_api_app = self
		self.mac_to_port = {}
		#testSend = {'module': 'nfm', 'id': 380,'flow':1,'delay':5567}
		#self.DMclient.postme(testSend)

	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		#self.logger.info(ev.state)
		
		if self.mininetRunning is False:
			self.monitoring_thread = hub.spawn(self._monitor)
			self.mininetRunning = True
		
		datapath = ev.datapath
		if ev.state == MAIN_DISPATCHER:
			if datapath.id not in self.datapaths:
				self.logger.info('registered datapath: %016x', datapath.id)
				self.datapaths[datapath.id] = datapath
		elif ev.state == DEAD_DISPATCHER:
			if datapath.id in self.datapaths:
				self.logger.info('unregister.datapath: %016x', datapath.id)
				del self.datapaths[datapath.id]
	
	@set_ev_cls(event.EventSwitchEnter)
	def get_topology_data(self, ev):
		switch_list = get_switch(self.topology_api_app, None)
		self.switches = [switch.dp.id for switch in switch_list]
		links_list = get_link(self.topology_api_app)
		links_list2 = get_all_link(self.topology_api_app)
		
		links = [(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]
		self.logger.info("LINKS2: ")
		for link in links_list2:
			self.logger.info(link)		
		#self.logger.info(links)
		#self.logger.info(links_list2)
		#global self.neighbourDict
		#print "one round"
		self.neighbourDict = {}		
		for link in links:
			self.logger.info("%d %d %s", link[0], link[1], link[2])
			self.logger.info("Neighbours of switch %s are: ", link[0])
			
			if str(link[0]) in self.neighbourDict:
				nList = self.neighbourDict[str(link[0])]
				link_tuple = {str(link[1]): link[2]}
				if link_tuple not in nList:
 					nList.append(link_tuple)
				self.neighbourDict[str(link[0])] = nList
				self.logger.info(nList)
			else:
				nList = []
				link_tuple = {str(link[1]): link[2]}
				#if link_tuple not in nList:
 				nList.append(link_tuple)
				self.neighbourDict[str(link[0])] = nList
				self.logger.info(nList)
			self.logger.info("\n")
			#self.logger.info(self.neighbourDict)
		#self.logger.info(switches)
		#self.logger.info(links)
		#self.logger.info(self.neighbourDict)
		#self.logger.info("NEIGHBOURS LEARNED...")
		self.switchCounter = len(self.switches)
		#self.logger.info("TOTAL SWITCHES: %d", len(switches))


	def _monitor(self):
		hub.sleep(10)
		self.logger.info(self.neighbourDict)
		self.bla.set()
		#self.blabla.set()
		while True:
			self.logger.info("REQUESTING FLOW STAT...")
			hub.sleep(self.updateTime)
			
			self.bla.wait()
			#self.blabla.wait()
			#self.logger.info("BLA")

			for dp in self.datapaths.values():
				self._request_stats(dp)
			self.bla.clear()
			#self.blabla.clear()
			

	def _request_stats(self, datapath):
		self.logger.debug('send stats....')
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)
		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
		datapath.send_msg(req)


			
	"""
	CHECK EVERY POSSIBLE LINK TO SEE IF THERE IS A FLOW ON THAT LINK 
	AND COMPUTE THE WHOLE PATHS BETWEEN END HOSTS
	"""
	def calculatePaths(self):
		#TODO: Compute the whole paths between end hosts
		for switchX in self.switches:
			for switchY in self.switches:
				if switchX is not switchY:
					self.logger.info("Checking between %d and %d", switchX, switchY)
					self.checkLink(switchX, switchY)
		self.logger.info("PATH COMPONENTS:")		
		self.logger.info(self.pathComponents)
		self.updateNIB()

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
		#self.logger.info(self.flows)
		if Sx in self.flows:
			Sx_flows = self.flows[Sx]
		
			for [OUT_PORT, ETH_DST, ETH_SRC, BYTES] in Sx_flows:
				if OUT_PORT == Sx_port:
					component = [Sx,Sy,ETH_SRC]
					if ETH_DST in self.pathComponents:
						if component not in self.pathComponents[ETH_DST]:
							self.pathComponents[ETH_DST].append(component)
					else:
						self.pathComponents[ETH_DST] = [component]

		#bytes = {}
		"""
		for flow in Sx_flows:
			#self.logger.info(flow)
			if flow[2] == Sx_port:
				#Determing BW
				path = str(Sx)+" -> "+str(Sy)+"[src_port: "+str(flow[0])+",dst:"+str(flow[1])+"]"
				subPath = [Sx,Sy]
				
				if path in bytes:
					linkBytes = bytes[path]
					linkBytes += flow[4]
					bytes[path] = linkBytes
				else:
					bytes[path] = flow[4]
				
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
				self.logger.info("Flow exists: %d -> %d with destination: %s. Source: %s. Packets: %d, bytes: %d, bw: %s", Sx, Sy, flow[1], flow[3], flow[4], speed)				
				if flow[1] in self.pathComponents:
					pathList = self.pathComponents[flow[1]]
					#if subPath not in pathList:
					pathList.append(subPath)
					self.pathComponents[flow[1]] = pathList
				elif flow[1] != -1:
					pathList = [subPath]
					self.pathComponents[flow[1]] = pathList
				#return True
		"""
		#for link in bytes:
		#	self.logger.info("BW of link %s: %d bytes/sec", link, bytes[link]/self.updateTime)
		return False

	def updateNIB(self):
		self.logger.info("UPDATING NIB")
		"""
		for key,value in self.pathComponents.iteritems():
			#self.logger.info(key)
			flowPaths = 0
			totalTo = 0
			for flow in value:
				
			fromSwitch = 0
			toSwitch = 0
			for [Sx, Sy] in value:
				#self.logger.info(fromSwitch)
				if Sy == fromSwitch
				fromSwitch = Sx
				toSwitch = Sy
		"""

	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		dpid = ev.msg.datapath.id
	
		#table_list = []
		for stat in [flow for flow in body if flow.priority >= 0]:
			#in_port = -1
			eth_dest = -1
			eth_src = -1
			#self.logger.info(stat)
			#if 'in_port' in stat.match:
			#	in_port = stat.match['in_port']
			if 'eth_dst' in stat.match:
				eth_dest = stat.match['eth_dst']
			if 'eth_src' in stat.match:
				eth_src = stat.match['eth_src']
			out_port = stat.instructions[0].actions[0].port
			bytes = stat.byte_count
			if eth_dest == -1 or eth_src == -1:
				continue
			#self.logger.info("in_port: %d, eth_src: %s, eth_dst: %s, out_port: %d, bytes: %d", in_port, eth_src, eth_dst, out_port, bytes)
			#if switch already exists in dictionary, check if the current flow exists in that subdictionary
			#update bytes counter only if that flow already exists
			#else append the flow to the subdictionary list
			if dpid in self.flows:
				temp = [out_port, eth_dest, eth_src]
				UPDATED_LINK_UTILIZATION = False
				for [OUT_P, ETH_D, ETH_S, BYTES_C] in self.flows[dpid]:
					if temp is [OUT_P, ETH_D, ETH_S]:
						#Update link utilization
						self.flows[dpid][4] = bytes - BYTES_C
						UPDATED_LINK_UTILIZATION = True
				if not UPDATED_LINK_UTILIZATION:
					#Append to list
					self.flows[dpid].append([out_port, eth_dest, eth_src, bytes])
			#else add the complete flow to the dictionary mapping to this switch
			else:
				self.flows[dpid] = [[out_port, eth_dest, eth_src, bytes]]
		self.responsedSwitches += 1
		#self.logger.info("FLOW STAT RECEIVED")
		self.logger.info("FLOW STAT RECEIVED: %d/%d", self.responsedSwitches, self.switchCounter)
		#self.logger.info(self.responsedSwitches)

		#WHEN EVERY SWITCH HAS GIVEN THE NFM ITS FLOW STAT, START CALCULATING THE PATHS
		if self.responsedSwitches == self.switchCounter:
			self.logger.info("Responsed Switches %d", self.responsedSwitches)
			self.responsedSwitches = 0
			self.calculatePaths()
			self.bla.set()		
		
			

	def print_json(self, ev):
		self.logger.info('datapath id: %016x', ev.msg.datapath.id)
		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
						indent=3, sort_keys=True))

	def print_port_table(self, ev):
		body = ev.msg.body
		
		"""
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
		self.logger.info("PORT TABLE")
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
		
		self.logger.info("\n")
	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):
		#self.print_port_table(ev)
		#self.logger.info('\n\n')
		a = 0







