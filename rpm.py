from ryu.base import app_manager
from ryu.controller import ofp_event

from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_all_link

from ryu.lib import hub
import networkx as nx
import json
import threading
#from client import client_side
from datetime import datetime
from ryu.app.ofctl import api
from ryu.ofproto import ofproto_v1_3
import simple_switch_13



class RPM(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(RPM, self).__init__(*args, **kwargs)

		self.datapaths = {}		#store datapaths
		#self.net = app_manager._CONTEXTS['network']	#fetch graph object of physical network
		self.net = nx.DiGraph([(1,2,{'src_port':1,'dst_port':1,'src_dpid':1,'dst_dpid':2,'bw':10}),
								(1,3,{'src_port':2,'dst_port':2,'src_dpid':1,'dst_dpid':3,'bw':30}),
								(2,3,{'src_port':2,'dst_port':1,'src_dpid':2,'dst_dpid':3,'bw':20}),
								(2,1,{'src_port':1,'dst_port':1,'src_dpid':2,'dst_dpid':1,'bw':10}),
								(3,1,{'src_port':2,'dst_port':2,'src_dpid':3,'dst_dpid':1,'bw':30}),
								(3,2,{'src_port':1,'dst_port':2,'src_dpid':2,'dst_dpid':3,'bw':20}),
								(1,'00:00:00:00:01:01',{'src_port':3,'dst_port':3,'src_dpid':1,'dst_dpid':'00:00:00:00:01:01','bw':5}),
								('00:00:00:00:01:01',1,{'src_port':3,'dst_port':3,'src_dpid':'00:00:00:00:01:01','dst_dpid':1,'bw':5}),
								(2,'00:00:00:00:02:01',{'src_port':3,'dst_port':3,'src_dpid':2,'dst_dpid':'00:00:00:00:02:01','bw':5}),
								('00:00:00:00:02:01',2,{'src_port':3,'dst_port':3,'src_dpid':'00:00:00:00:02:01','dst_dpid':2,'bw':5}),
								(3,'00:00:00:00:03:01',{'src_port':3,'dst_port':3,'src_dpid':3,'dst_dpid':'00:00:00:00:03:01','bw':5}),
								('00:00:00:00:03:01',3,{'src_port':3,'dst_port':3,'src_dpid':'00:00:00:00:03:01','dst_dpid':3,'bw':5})])
		
		self.totalSwitchesNr = self.determineNumberOfSwitches()	#calculate total switches by the graph topology object
		self._print("TOTAL SWITCHES: %d" % self.totalSwitchesNr)
		
		self.logger.debug("TOTAL SWITCHES: %d", self.totalSwitchesNr)

		self.DICT_TO_DB = {'module':'rpm'}	#prepare a dictionary for updating and sending to Database
		
		self.updateTime = 10
		self.switches_DPIDs = {}	#dict to store all switches in order of dpid
		

		#self.DMclient = client_side(" ")	#instance of Database module client
		
		self.responses = 0	#counter for amount of switch flows retrieving after a request
		
		#TODO start monitoring thread(s) to continuosly monitor switches
		# inside the thread have semaphore to unlock when switches are ready
		#self.monitoring_semaphore = threading.Event();


	def send_flow_mod(self, datapath):
		ofp = datapath.ofproto
		#self._print(ofp)

		ofp_parser = datapath.ofproto_parser

		cookie = cookie_mask = 0
		table_id = 0
		idle_timeout = 0
		hard_timeout = 1
		priority = 32768
		buffer_id = ofp.OFP_NO_BUFFER
	
		match = ofp_parser.OFPMatch(in_port=1, eth_dst='00:00:00:00:00:00')  # DUMMY IP
		actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)]
		inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,actions)]
		req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask,
									table_id, ofp.OFPFC_ADD,
									idle_timeout, hard_timeout,
									priority, buffer_id,
									ofp.OFPP_ANY, ofp.OFPG_ANY,
									ofp.OFPFF_SEND_FLOW_REM,
									match, inst)
		datapath.send_msg(req)

	"""
	Function to calculate the number of switches in the physical topology with the help of graph object
	"""
	def determineNumberOfSwitches(self):
		return len([n for n in self.net.nodes() if len(str(n).split(':')) == 1])

	def _print(self, message):
		self.logger.info("[RPM] " + message)

	@set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
	def flow_removed_handler(self, ev):
		self._print("FLOW REMOVED")

		msg = ev.msg
		dp = msg.datapath
		ofp = dp.ofproto
		ofp_id = dp.id

		self._print("Switch with id: %d" % ofp_id)

		if msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
			reason = 'IDLE TIMEOUT'
		elif msg.reason == ofp.OFPRR_HARD_TIMEOUT:
			reason = 'HARD TIMEOUT'
		elif msg.reason == ofp.OFPRR_DELETE:
			reason = 'DELETE'
		elif msg.reason == ofp.OFPRR_GROUP_DELETE:
			reason = 'GROUP DELETE'
		else:
			reason = 'unknown'

		self._print(reason)


		self.logger.debug('OFPFlowRemoved received: '
						'cookie=%d priority=%d reason=%s table_id=%d '
						'duration_sec=%d duration_nsec=%d '
						'idle_timeout=%d hard_timeout=%d '
						'packet_count=%d byte_count=%d match.fields=%s',
						msg.cookie, msg.priority, reason, msg.table_id,
						msg.duration_sec, msg.duration_nsec,
						msg.idle_timeout, msg.hard_timeout,
						msg.packet_count, msg.byte_count, msg.match)
	"""
	Switch state change handler. Called every time a switch state changes, creates a dict dpid -> datapath
	"""
	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		
		datapath = ev.datapath
		if ev.state == MAIN_DISPATCHER:
			if datapath.id not in self.datapaths:
				self.logger.info('registered datapath: %016x', datapath.id)
				self.switches_DPIDs[datapath.id] = datapath
		elif ev.state == DEAD_DISPATCHER:
			if datapath.id in self.datapaths:
				self.logger.info('unregister.datapath: %016x', datapath.id)
				del self.switches_DPIDs[datapath.id]

		if len(self.switches_DPIDs.viewkeys()) == self.totalSwitchesNr:
			print self.switches_DPIDs.viewkeys()
			# Testing flow mod + flow remove
			# TODO: 
			#if innit set a semaphore here to open up when all switches are availible
			#self.monitoring_semaphore = 
			dp = self.switches_DPIDs[1]
			print dp
			self.send_flow_mod(dp)
			self._print("FLOW MOD SENT!")





