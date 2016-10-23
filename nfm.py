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
from datetime import datetime


class NFM(simple_switch_13.SimpleSwitch13):	

	flows = {}		# dictionary to store each switch's flows
	#bla = threading.Event() # semaphore variable to syncronize between flow request and path computing

	#switchCounter = 0	# total registered switches
	responsedSwitches = 0	# counter of a round's responded switches
	responsedSwitchesPortStatus = 0 #counter of a round's responded switches of port stats
	#DMclient = client_side(" ")
	#mininetRunning = False
	#pathComponents = {}
	#updateTime = 10
	#portDict = {}
	#switches = []
	
	
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(NFM, self).__init__(*args, **kwargs)
		self.datapaths = {}		#store datapaths
		self.net = app_manager._CONTEXTS['network']	#fetch graph object of physical network
		self.totalSwitches = self.determineNumberOfSwitches()
		self.logger.info("TOTAL SWITCHES: %d", self.totalSwitches)
		self.DICT_TO_DB = {'module':'nfm'}
		self.pathComponents = {}
		self.updateTime = 10
		self.flow_request_semaphore = threading.Event();
		self.switches = []	#list to store all switches dpid
		self.portDict = {}	
		self.mininetRunning = False
		self.DMclient = client_side(" ")


	"""
	Switch state change handler. Called every time a switch state changes
	"""
	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		
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


	
	"""
	Function to calculate the number of switches in the physical topology with the help of graph object
	"""
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

	"""
	Main loop of requesting statistics of the switches
	"""
	def _monitor(self):
		#hub.sleep(10)
		self.flow_request_semaphore.set()

		while True:
			self.logger.info("REQUESTING FLOW STAT...")
			hub.sleep(self.updateTime)
			
			self.flow_request_semaphore.wait()

			for dp in self.datapaths.values():
				self._request_stats(dp)
			self.flow_request_semaphore.clear()
			
	"""
	Function to request flow statistics and port statistics of a datapath (switch)
	"""
	def _request_stats(self, datapath):
		self.logger.debug('send stats....')
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)
		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
		datapath.send_msg(req)


			
	"""
	Main callback function of retreiving flow statistics.
	This will use the event which occured, to get necessary information such as IN_PORT, OUT_PORT, ETHERNET DESTINATION etc...
	It will add these flows to the class global dictionary if not already added. In the case of already existing flow in the dict, 
	update the bytes information.
	"""
	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		dpid = ev.msg.datapath.id
		#self.logger.info("DPID")
		#self.logger.info(dpid)

		for stat in [flow for flow in body if flow.priority >= 0]:
			in_port = -1
			out_port = -1
			eth_dest = -1
			#eth_src = -1
			#self.logger.info(stat)
			if 'in_port' in stat.match:
				in_port = stat.match['in_port']
			if 'eth_dst' in stat.match:
				eth_dest = stat.match['eth_dst']
			#if 'eth_src' in stat.match:
			#	eth_src = stat.match['eth_src']
			out_port = stat.instructions[0].actions[0].port
			CURRENT_BYTES = stat.byte_count
			#if eth_dest == -1 or eth_src == -1:
			if in_port == -1 or out_port == -1 or eth_dest == -1:
				continue
			self.logger.debug("dpid: %d, eth_dst: %s, out_port: %d, bytes: %d", dpid, eth_dest, out_port, CURRENT_BYTES)
			#if switch already exists in dictionary, check if the current flow exists in that subdictionary
			#update bytes counter only if that flow already exists
			#else append the flow to the subdictionary list
			prev_bytes = 0
			if dpid in self.flows:
				UPDATED_LINK_UTILIZATION = False
				flowCounter = 0
				#for [OUT_P, ETH_D, ETH_S, PREVIOUS_BYTES, DIFF_BYTES] in self.flows[dpid]:
				for [IN_P, OUT_P, ETH_D, PREVIOUS_BYTES, DIFF_BYTES] in self.flows[dpid]:
					#if out_port == OUT_P and eth_dest == ETH_D and eth_src == ETH_S:
					if in_port == IN_P and out_port == OUT_P and eth_dest == ETH_D:
						#Update link utilization
						self.logger.debug("UPDATING FLO'W BYTES; PREVIOUS: %d, DIFF: %d", PREVIOUS_BYTES, DIFF_BYTES)
						self.flows[dpid][flowCounter][4] = CURRENT_BYTES - PREVIOUS_BYTES
						self.flows[dpid][flowCounter][3] = CURRENT_BYTES
						UPDATED_LINK_UTILIZATION = True
						break
					flowCounter += 1
				if not UPDATED_LINK_UTILIZATION:
					#Append to list
					#self.flows[dpid].append([out_port, eth_dest, eth_src, CURRENT_BYTES, prev_bytes])
					self.flows[dpid].append([in_port, out_port, eth_dest, CURRENT_BYTES, prev_bytes])
			#else add the complete flow to the dictionary mapping to this switch
			else:
				#self.flows[dpid] = [[out_port, eth_dest, eth_src, CURRENT_BYTES, prev_bytes]]
				self.flows[dpid] = [[in_port, out_port, eth_dest, CURRENT_BYTES, prev_bytes]]
		self.responsedSwitches += 1
		self.logger.info("FLOW STAT RECEIVED: %d/%d", self.responsedSwitches, self.totalSwitches)

		#WHEN EVERY SWITCH HAS GIVEN THE NFM ITS FLOW STAT, START CALCULATING THE PATHS
		if self.responsedSwitches == self.totalSwitches:
			self.logger.debug("Responsed Switches %d", self.responsedSwitches)
			self.responsedSwitches = 0
			self.calculatePaths()
			self.flow_request_semaphore.set()		

	"""
	CHECK EVERY POSSIBLE LINK TO SEE IF THERE IS A FLOW ON THAT LINK 
	AND COMPUTE THE LINK UTILIZATION
	"""
	def calculatePaths(self):
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		self.DICT_TO_DB['timestamp'] = timestamp
		self.DICT_TO_DB['link_utilization'] = {}
		edges = [n for n in self.net.edges(data='bw')]
		for (From, To, Attr) in edges:
			DPID_PORT = From.split('-')
			if len(DPID_PORT) == 2:
				FROM_DPID = DPID_PORT[0]
				FROM_PORT = DPID_PORT[1]
				bytes = self.checkFlowTable(FROM_DPID, FROM_PORT)
				self.logger.debug("BYTES SENT FROM SWITCH %d PORT %d: %d", int(FROM_DPID), int(FROM_PORT), bytes)
				LINK_UTILIZATION = float(bytes)*8/(float(Attr)*1000000)
				self.logger.debug("LINK UTLIZATION: {0:.0f}%".format(100*LINK_UTILIZATION))
				DPID_TO_DPID = FROM_DPID+'-'+To.split('-')[0]
				self.DICT_TO_DB['link_utilization'][DPID_TO_DPID] = LINK_UTILIZATION
		#self.DMclient.postme(self.DICT_TO_DB)

	
	def checkFlowTable(self, Sx, Sx_port):
		if int(Sx) in self.flows:
			Sx_flows = self.flows[int(Sx)]
			#for [OUT_PORT, ETH_DST, ETH_SRC, PREVIOUS_BYTES, DIFF] in Sx_flows:
			for [IN_PORT, OUT_PORT, ETH_DST, PREVIOUS_BYTES, DIFF] in Sx_flows:
				if OUT_PORT == int(Sx_port):
					return DIFF
		return 0
			

	"""
	Function to print the event statistics as json dump
	"""
	def print_json(self, ev):
		self.logger.info('datapath id: %016x', ev.msg.datapath.id)
		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
						indent=3, sort_keys=True))

	"""
	Function to print the port statstics as table
	"""
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

	"""
	Main callback function of retreiving port statistics of the switch
	"""
	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):
		#self.print_port_table(ev)
		#self.logger.info('\n\n')
		a = 0







