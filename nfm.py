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
import networkx as nx
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
		self.net = nx.DiGraph([('1-1','2-1',{'bw':10}),('2-1','1-1',{'bw':10}),('1-2','3-2',{'bw':30}),('3-2','1-2',{'bw':30}),('2-2','3-1',{'bw':20}),('3-1','2-2',{'bw':20}), ('00:00:00:00:01:01','1-3',{'bw':5}),('1-3','00:00:00:00:01:01',{'bw':5}),('00:00:00:00:02:01','2-3',{'bw':5}),('2-3','00:00:00:00:02:01',{'bw':5}),('00:00:00:00:03:01','3-3',{'bw':5}),('3-3','00:00:00:00:03:01',{'bw':5})])
		#self.logger.info([n for n in self.net.nodes()])
		#self.logger.info([n for n in self.net.edges(data='bw')])
		self.totalSwitches = self.determineNumberOfSwitches()
		self.logger.info("TOTAL SWITCHES: %d", self.totalSwitches)
		#self.populateNET()
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



	def determineNumberOfSwitches(self):
		total = []
		nodes = [str(n) for n in self.net.nodes()]
		self.logger.info(nodes)
		for dpid_port in nodes:
			DPID_P = dpid_port.split('-')
			dpid = DPID_P[0]
			if len(DPID_P) == 2 and dpid not in total:
				total.append(dpid)
		return len(total)

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
		edges = [n for n in self.net.edges(data='bw')]
		for (From, To, Attr) in edges:
			DPID_PORT = From.split('-')
			if len(DPID_PORT) == 2:
				FROM_DPID = DPID_PORT[0]
				FROM_PORT = DPID_PORT[1]
				bytes = self.checkFlowTable(FROM_DPID, FROM_PORT)
				self.logger.info("BYTES SENT FROM SWITCH %d PORT %d: %d", int(FROM_DPID), int(FROM_PORT), bytes)
				self.logger.info("LINK UTLIZATION: {0:.0f}%".format(100*((float(bytes)*8)/(float(Attr)*1000000))))
				#self.logger.info("%.2f",float(Attr)/3)

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
		#Sx_neighbours = self.neighbourDict[str(Sx)]
 
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


	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		dpid = ev.msg.datapath.id
		self.logger.info("DPID")
		self.logger.info(dpid)
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
			self.logger.info("dpid: %d, eth_src: %s, eth_dst: %s, out_port: %d, bytes: %d", dpid, eth_src, eth_dest, out_port, bytes)
			#if switch already exists in dictionary, check if the current flow exists in that subdictionary
			#update bytes counter only if that flow already exists
			#else append the flow to the subdictionary list
			if dpid in self.flows:
				UPDATED_LINK_UTILIZATION = False
				self.logger.info("CHECKING FLOWS")
				#self.logger.info(self.flows)
				flowCounter = 0
				for [OUT_P, ETH_D, ETH_S, BYTES_C] in self.flows[dpid]:
					if out_port == OUT_P and eth_dest == ETH_D and eth_src == ETH_S:
						#Update link utilization
						#self.logger.info("UPDATING FLOW BYTES; PREVIOUS: %d, CURRENt: %d", BYTES_C, bytes)
						self.flows[dpid][flowCounter][3] = bytes - BYTES_C
						UPDATED_LINK_UTILIZATION = True
						break
					flowCounter += 1
				if not UPDATED_LINK_UTILIZATION:
					#Append to list
					self.flows[dpid].append([out_port, eth_dest, eth_src, bytes])
			#else add the complete flow to the dictionary mapping to this switch
			else:
				self.flows[dpid] = [[out_port, eth_dest, eth_src, bytes]]
		self.responsedSwitches += 1
		#self.logger.info("FLOW STAT RECEIVED")
		self.logger.info("FLOW STAT RECEIVED: %d/%d", self.responsedSwitches, self.totalSwitches)
		#self.logger.info(self.responsedSwitches)

		#WHEN EVERY SWITCH HAS GIVEN THE NFM ITS FLOW STAT, START CALCULATING THE PATHS

		if self.responsedSwitches == self.totalSwitches:
			self.logger.info("Responsed Switches %d", self.responsedSwitches)
			self.responsedSwitches = 0
			self.calculatePaths()
			self.bla.set()		
	
	def checkFlowTable(self, Sx, Sx_port):
		#self.logger.info(self.flows)
		if int(Sx) in self.flows:
			Sx_flows = self.flows[int(Sx)]
			for [OUT_PORT, ETH_DST, ETH_SRC, BYTES] in Sx_flows:
				#self.logger.info([OUT_PORT, ETH_DST, ETH_SRC, BYTES])
				if OUT_PORT == int(Sx_port):
					return BYTES
		return 0
			

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







