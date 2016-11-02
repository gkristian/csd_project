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



class RPM(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(RPM, self).__init__(*args, **kwargs)

		self.datapaths = {}		#store datapaths
		self.net = app_manager._CONTEXTS['network']	#fetch graph object of physical network
		self.totalSwitchesNr = self.determineNumberOfSwitches()	#calculate total switches by the graph topology object
		self._print("TOTAL SWITCHES: %d" % self.totalSwitchesNr)
		
		self.logger.debug("TOTAL SWITCHES: %d", self.totalSwitchesNr)

		self.DICT_TO_DB = {'module':'rpm'}	#prepare a dictionary for updating and sending to Database
		
		self.updateTime = 10
		#self.flow_request_semaphore = threading.Event();
		self.switchesDPIDs = []	#list to store all switches dpid

		self.mininetRunning = False
		#self.DMclient = client_side(" ")	#instance of Database module client
		
		self.responses = 0	#counter for amount of switch flows retrieving after a request

		# Testing flow mod + flow remove
		datapath_id = 1
		dp = api.get_datapath(self, datapath_id)
		self.send_flow_mod(dp)


	def send_flow_mod(self, datapath):
		ofp = datapath.ofproto
		self._print(ofp)

		ofp_parser = datapath.ofproto_parser

		cookie = cookie_mask = 0
		table_id = 0
		idle_timeout = 0
		hard_timeout = 0.1
		priority = 32768
		buffer_id = ofp.OFP_NO_BUFFER
	
		match = ofp_parser.OFPMatch(in_port=1, ip_dst='120.7.7.1')  # DUMMY IP
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



