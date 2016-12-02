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


#class NFM(simple_switch_13.SimpleSwitch13): #SHOULD INHERIT APP MANAGER WHEN USED WITH REAL CPM
class NFM(app_manager.RyuApp):
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
		self.DICT_TO_DB = {'module':'nfm', 'timestamp':0, 'link_utilization':{}, 'packet_dropped':{}}	#prepare a dictionary for updating and sending to Database
		#self.DICT_TO_DB['keylist'] = {}	#UNNECESSARY WITH KEYLIST
		#self.DICT_TO_DB['keylist']['packet_dropped'] = {}
		self.pathComponents = {}
		self.updateTime = 1
		#self.flow_request_semaphore = threading.Event()
		self.port_stat_request_semaphore = threading.Event()
		self.switches = []	#list to store all switches dpid
		self.portDict = {}
		self.mininetRunning = False
		#self.DMclient = client_side("http://127.0.0.1:8000/Tasks.txt")	#instance of Database module client
		self.responsedSwitches = 0	#counter for amount of switch flows retrieving after a request
		self.responsedSwitchesPortStatus = 0
		self.flows = {}		#dictionary to store each switch's flows
		self.dropped = {}	#dictionary to store dropped packets for each dp
		self.transmittedBytes = {}	#dictionary to keep track of previous transmitted bytes
		self.linkUtilizations = {}	#dictionary to keep track of link utilizations


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
		self.port_stat_request_semaphore.set()
		hub.sleep(10)
		while True:
			self.logger.debug("REQUESTING PORT STAT...")
			hub.sleep(self.updateTime)
			self.port_stat_request_semaphore.wait()
			self.logger.info("\n")
			for dp in self.datapaths.values():
				self._request_stats(dp)
			self.port_stat_request_semaphore.clear()

	"""
	Function to request flow statistics and port statistics of a datapath (switch)
	"""
	def _request_stats(self, datapath):
		self.logger.debug('send stats....')
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		#req = parser.OFPFlowStatsRequest(datapath)		DON'T USE THIS NOW
		#datapath.send_msg(req)							DON'T USE THIS NOW
		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
		datapath.send_msg(req)



	"""
	Function to print the event statistics as json dump
	"""
	def print_json(self, ev):
		self.logger.info('datapath id: %016x', ev.msg.datapath.id)
		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
						indent=3, sort_keys=True))


	"""
	Calculate link utilization [unidirectional] of the port statistics
	"""
	def store_port_stat(self, ev):
		body = ev.msg.body
		dpid = ev.msg.datapath.id
		for stat in sorted(body, key=attrgetter('port_no')):	#loop through all stats
			portNr = stat.port_no
			rx_bytes = stat.rx_bytes
			tx_bytes = stat.tx_bytes
			[IS_SWITCH_LINK, TO, BW] = self.port_to_switch(dpid, portNr)	#get the link's other switch and bw
			if IS_SWITCH_LINK:		#If this link is towards another switch (check port_to_swith function for details)
				if dpid in self.transmittedBytes:	#if dpid already stored in dictionary of transmitted bytes
					tx_dict = self.transmittedBytes[dpid]
					if portNr in tx_dict:			#if port number stored in this dpid transmitted bytes dict
						previous_tx_bytes = tx_dict[portNr]		#get previous monitored transmitted bytes
						diff_tx_bytes = tx_bytes - previous_tx_bytes	#calculate the transmitted bytes from last monitor call
						LINK_UTILIZATION = 100*(float(diff_tx_bytes)*8/(float(BW)*1000000*self.updateTime)) #calculate link utilization for this link (from this switch to the other [unidirectional] )
						if dpid in self.linkUtilizations:
							self.linkUtilizations[dpid][TO] = LINK_UTILIZATION	#store link utilization
						else:
							self.linkUtilizations[dpid] = {TO:LINK_UTILIZATION}	#store link utilization
					self.transmittedBytes[dpid][portNr] = tx_bytes	#store current transmitted bytes
				else:
					self.transmittedBytes[dpid] = {portNr:tx_bytes} #store current transmitted bytes



	"""
	Loop through the graph object and find the edge that matches dpid and port number. Return that links opposite dpid and bandwidth and True if this link is towards another switch and not host.
	"""
	def port_to_switch(self, dpid, port_no):
		edges = [n for n in self.net.edges(data=True)]
		for (FROM, TO, ATTR) in edges:
			if len(str(FROM).split(':')) == 1 and len(str(TO).split(':')) == 1 and FROM == dpid and ATTR['src_port'] == port_no:
				#self.logger.info((FROM, TO, ATTR))
				return [True, TO, ATTR['bw']]
		return [False, None, None]

	"""
	Calculate dropped packets from the acquired port statistics
	Method: Sum up all the received packets for the switch. Sum up all the transmitted
	packets and then take the difference. If transmitted packets equals the receieved,
	then no dropped packets. If transmitted is less than received, then switch has dropped
	packets.
	"""
	def calculate_dropped_packets(self, ev):

		#self.DICT_TO_DB['packet_dropped'] = {}	

		body = ev.msg.body
		rx_packets = 0
		tx_packets = 0

		#Sum up all the recieved and transmitted packets
		for stat in sorted(body, key=attrgetter('port_no')):
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
			percentage = 0.0
			if diff_rx != 0:
				percentage = float(dropped) / float(diff_rx)
				if percentage < 0:
					percentage = 0
			percentage_string = "{0:.2f}%".format(100*percentage)
			#self.logger.info('DROPPED PACKETS PERCENTAGE ON SWITCH %x: %s', ev.msg.datapath.id, percentage_string)
			DPID = str(ev.msg.datapath.id)
			self.DICT_TO_DB['packet_dropped'][DPID] = percentage # write into dict prepared to be sent to DM 
			#self.DICT_TO_DB['keylist']['packet_dropped'][dpid] = percentage
		self.dropped[ev.msg.datapath.id] = {'rx':rx_packets, 'tx':tx_packets} #store the current measured received and transmitted packets

	"""
	Calculate TOTAL link utilization
		& after all date updated, push it to DM
	Function store_port_stat above will store transmitted bytes and calculate link utilzation BUT only for link in one direction. This function will loop through all those saved utilizations and match the correct ones and add this upp. EX:
	FROM SWITCH 1 TO SWITCH 2: UTILIZATION = 30%
	FROM SWITCH 2 TO SWITCH 1: UTILIZATION = 9%
	TOTAL = 30 + 9 %
	"""
	def calculate_link_utilization(self):
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		self.DICT_TO_DB['timestamp'] = timestamp
		#self.DICT_TO_DB['keylist']['timestamp'] = timestamp 
		#self.DICT_TO_DB['keylist']['link_utilization'] = []	
		#self.DICT_TO_DB['link_utilization'] = {}
		for FROM, value in self.linkUtilizations.iteritems():
			for TO, FROM_UTIL in value.iteritems():
				try:
					TO_UTILS = self.linkUtilizations[TO]
					TO_UTIL = TO_UTILS[FROM]
					#TOTAL_UTIL = FROM_UTIL + TO_UTIL
					TOTAL_UTIL = FROM_UTIL
					TOTAL_UTIL_STRING = "{0:.2f}%".format(TOTAL_UTIL)
					#self.logger.info("TOTAL UTILIZATION %d -> %d: %s", FROM, TO, TOTAL_UTIL_STRING)
					DPID_TO_DPID = str(FROM)+'-'+str(TO)
					self.DICT_TO_DB['link_utilization'][DPID_TO_DPID] = TOTAL_UTIL # write into dict
					#self.DICT_TO_DB['keylist']['link_utilization'].append((FROM, TO,{'weight':TOTAL_UTIL}))
				except:
					self.logger.info("[ERROR] Link only has one directional utilization, check opposite switch")
		#self.DMclient.postme(self.DICT_TO_DB) # Push to DM
		self.logger.info(self.DICT_TO_DB)


	"""
	Main callback function of retreiving port statistics of the switch
	"""
	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):
		self.store_port_stat(ev)
		self.calculate_dropped_packets(ev) # when packet_dropped rate on a swith is calculated, wirte into dict right away
		self.responsedSwitches += 1
		if self.responsedSwitches == self.totalSwitches:
			self.logger.debug("Responsed Switches %d", self.responsedSwitches)
			self.responsedSwitches = 0
			self.calculate_link_utilization() # this function also push dict to DM after all new data is included
			self.port_stat_request_semaphore.set()
