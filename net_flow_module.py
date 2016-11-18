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
from ryu.ofproto import ether
from ryu.lib import hub
import networkx as nx
import json
import threading
from client import client_side
from datetime import datetime


class NFM(simple_switch_13.SimpleSwitch13):
	
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(NFM, self).__init__(*args, **kwargs)
		self.datapaths = {}		#store datapaths
		self.net = app_manager._CONTEXTS['network']	#fetch graph object of physical network
		self.totalSwitches = self.determineNumberOfSwitches()	#calculate total switches by the graph topology object
		#self.logger.info("TOTAL SWITCHES: %d", self.totalSwitches)
		self.logger.info(self.totalSwitches)
		self.DICT_TO_DB = {'module':'nfm'}	#prepare a dictionary for updating and sending to Database
		self.pathComponents = {}
		self.updateTime = 1
		self.flow_request_semaphore = threading.Event();
		self.switches = []	#list to store all switches dpid
		self.portDict = {}	
		self.mininetRunning = False
		self.DMclient = client_side(" ")	#instance of Database module client
		self.responsedSwitches = 0	#counter for amount of switch flows retrieving after a request
		self.responsedSwitchesPortStatus = 0
		self.flows = {}		#dictionary to store each switch's flows
		self.dropped = {}	#dictionary to store dropped packets for each dp
		self.transmittedBytes = {}


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
		return len([n for n in self.net.nodes() if len(str(n).split(':')) == 1])


	"""
	Main loop of requesting statistics of the switches
	"""
	def _monitor(self):
		self.flow_request_semaphore.set()
		hub.sleep(10)
		while True:
			self.logger.debug("REQUESTING FLOW STAT...")
			hub.sleep(self.updateTime)
			self.flow_request_semaphore.wait()
			self.logger.info("\n")
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

		for stat in [flow for flow in body if flow.priority >= 1 and flow.priority <= 33000]:
			in_port = -1
			out_port = -1
			#eth_dest = -1
			if 'in_port' in stat.match:
				in_port = stat.match['in_port']
			#if 'eth_dst' in stat.match:
			#	eth_dest = stat.match['eth_dst']
			out_port = stat.instructions[0].actions[0].port
			CURRENT_BYTES = stat.byte_count
			if in_port == -1 or out_port == -1:
				continue
			self.logger.info("dpid: %d, in_port: %s, out_port: %d, bytes: %d", dpid, in_port, out_port, CURRENT_BYTES)
			#if switch already exists in dictionary, check if the current flow exists in that subdictionary
			#update bytes counter only if that flow already exists
			#else append the flow to the subdictionary list
			prev_bytes = 0
			if dpid in self.flows:
				UPDATED_LINK_UTILIZATION = False
				flowCounter = 0

				for [IN_P, OUT_P, PREVIOUS_BYTES, DIFF_BYTES] in self.flows[dpid]:
					if in_port == IN_P and out_port == OUT_P:
						#Update link utilization
						self.logger.info("UPDATING FLOW BYTES; PREVIOUS: %d, DIFF: %d", PREVIOUS_BYTES, DIFF_BYTES)
						self.flows[dpid][flowCounter][3] = CURRENT_BYTES - PREVIOUS_BYTES
						self.flows[dpid][flowCounter][2] = CURRENT_BYTES
						UPDATED_LINK_UTILIZATION = True
						break
					flowCounter += 1
				if not UPDATED_LINK_UTILIZATION:
					#Append to list
					self.flows[dpid].append([in_port, out_port, CURRENT_BYTES, prev_bytes])
			#else add the complete flow to the dictionary mapping to this switch
			else:
				self.flows[dpid] = [[in_port, out_port, CURRENT_BYTES, prev_bytes]]
		self.responsedSwitches += 1
		self.logger.debug("FLOW STAT RECEIVED: %d/%d", self.responsedSwitches, self.totalSwitches)

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

		#TODO
		#Perhaps the link between host and switch should also be checked
		#As of now, only links between switches are checked

		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		self.DICT_TO_DB['timestamp'] = timestamp
		self.DICT_TO_DB['link_utilization'] = {}
		edges = [n for n in self.net.edges(data=True)]
		for (FROM, TO, ATTR) in edges:
			# Check that 'From' and 'To' are switches. A host would return a list with length larger than 1
			if len(str(FROM).split(':')) == 1 and len(str(TO).split(':')) == 1:	
				FROM_PORT = ATTR['src_port']
				bytes = self.checkFlowTable(FROM, FROM_PORT)
				
				LINK_UTILIZATION = float(bytes)*8/(float(ATTR['bw'])*1000000*self.updateTime)
				lu = "LINK UTILIZATION: {0:.0f}%".format(100*LINK_UTILIZATION)
				self.logger.debug("BYTES SENT FROM SWITCH %d PORT %d: %d [bw=%d Mbit/s] %s", FROM, FROM_PORT, bytes, ATTR['bw'], lu)
				
				DPID_TO_DPID = str(FROM)+'-'+str(TO)
				#self.logger.info("LINK UTILIZATION ON LINK %s: %d {0:.2}%".
				self.DICT_TO_DB['link_utilization'][DPID_TO_DPID] = LINK_UTILIZATION
		#self.logger.info("NFM ATTEMPTING A PUSH TO DB")		
		#self.DMclient.postme(self.DICT_TO_DB)

	"""
	Function to return amounts of bytes sent on a specific port from last check
	"""
	def checkFlowTable(self, Sx, Sx_port):
		if Sx in self.flows:
			Sx_flows = self.flows[Sx]
			for [IN_PORT, OUT_PORT, PREVIOUS_BYTES, DIFF] in Sx_flows:
				if OUT_PORT == Sx_port:
					return DIFF
		return 0
			

	"""
	Function to print the event statistics as json dump
	"""
	def print_json(self, ev):
		self.logger.info('datapath id: %016x', ev.msg.datapath.id)
		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
						indent=3, sort_keys=True))



	def store_port_stat(self, ev):
		body = ev.msg.body
		dpid = ev.msg.datapath.id
		edges = [n for n in self.net.edges(data=True)]
		#self.logger.info(edges)
		
		for stat in sorted(body, key=attrgetter('port_no')):
			portNr = stat.port_no
			rx_bytes = stat.rx_bytes
			tx_bytes = stat.tx_bytes
			for (FROM, TO, ATTR) in edges:
				if len(str(FROM).split(':')) == 1 and len(str(TO).split(':')) == 1:
					FROM_PORT = ATTR['src_port']
					if portNr == FROM_PORT:
						
						
						if dpid in self.transmittedBytes:
							if portNr is 
							//DO SOMETHING
						else:

							self.transmittedBytes[dpid] = [[portNr, tx_bytes]]
						
						LINK_UTILIZATION = float(tx_bytes)*8/(float(ATTR['bw'])*1000000*self.updateTime)
						lu = "{0:.2f}%".format(100*LINK_UTILIZATION)
						self.logger.info("Transmitted bytes on switch %d port %d: %d {bw=%d Mbit/s, LINK UTILIZATION %s}", dpid, portNr, tx_bytes, ATTR['bw'], lu)
	"""
	Calculate dropped packets from the acquired port statistics
	Method: Sum up all the received packets for the switch. Sum up all the transmitted
	packets and then take the difference. If transmitted packets equals the receieved,
	then no dropped packets. If transmitted is less than received, then switch has dropped 
	packets.
	"""
	def calculate_dropped_packets(self, ev):

		#TODO
		#Still a bug that will print out negative percentage of dropped packet sometimes

		body = ev.msg.body
		rx_packets = 0
		tx_packets = 0

		#Sum up all the recieved and transmitted packets
		for stat in sorted(body, key=attrgetter('port_no')):
			#self.logger.info("[PORT STAT] BYTES SENT FROM SWITCH %d PORT %d: %d", ev.msg.datapath.id, stat.port_no, stat.tx_bytes)
			#self.logger.info("[PORT STAT] BYTES RECEIVED FROM SWITCH %d PORT %d: %d",ev.msg.datapath.id, stat.port_no, stat.rx_bytes)
			rx_packets += stat.rx_packets
			tx_packets += stat.tx_packets

		"""
		If switch has some stored data about recieved and transmitted packets,
		compute the difference
		"""
		if ev.msg.datapath.id in self.dropped:
			stored_rx_packets = self.dropped[ev.msg.datapath.id]['rx']
			stored_tx_packets = self.dropped[ev.msg.datapath.id]['tx']
			diff_rx = rx_packets - stored_rx_packets
			diff_tx = tx_packets - stored_tx_packets
			dropped = diff_rx - diff_tx
			#print("[DEBUG] diff_rx, diff_tx", diff_rx, diff_tx)
			percentage = 0.0
			if diff_rx != 0:
				#print("[DEBUG] dropped, diff", dropped, diff_rx)
				percentage = float(dropped) / float(diff_rx)
				#print("[DEBUG] Percentage: ", percentage)
			percentage_string = "{0:.2f}%".format(100*percentage)
			self.logger.info('DROPPED PACKETS PERCENTAGE ON SWITCH %x: %s', ev.msg.datapath.id, percentage_string)
		self.dropped[ev.msg.datapath.id] = {'rx':rx_packets, 'tx':tx_packets} #store the current measured received and transmitted packets



	"""
	Main callback function of retreiving port statistics of the switch
	"""
	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):
		self.store_port_stat(ev)
		self.calculate_dropped_packets(ev)








