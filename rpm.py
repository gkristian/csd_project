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
import time


class RPM(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(RPM, self).__init__(*args, **kwargs)
		self.datapaths = {}

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
		
		self.start_time = 0

		# format {"dpid1": {"start_time": 100, "measured_time": 13, "xid": 1234}}
		self.switches_data = {}
		# format on position dpid, current xid

	"""
	Main loop of sending  install/update/delete flow mods to the switches,
	currently sending ca 16 request every second. i.e get results for 4 switches every second
	TODO Send to DM every 5-10 seconds?
	"""
	def _monitor(self): #TODO CHANGE FOR NEW STRUCTURE
		xid = 0
		while True:			
			self._print("SENDING FLOW MODS...")
			dpids = self.switches_DPIDs.viewkeys()
			for dpid in dpids: # Testing flow mod + flow remove
				dp = self.switches_DPIDs[dpid]

				self.send_flow_mod(dp, 1, '00:00:00:00:00:00', "ADD")
				self.send_flow_mod(dp, 1, '10:00:00:00:00:00', "UPDATE")
				self.send_flow_mod(dp, 1, '10:00:00:00:00:00', "DELETE")
				self.send_flow_mod(dp, 2, '20:00:00:00:00:00', "ADD")
				self.send_flow_mod(dp, 2, '20:00:00:00:00:00', "DELETE")
				self._print("FLOW MODS SENT")

				#TODO work in structure for saving away data
				self.switches_data[dpid]["start_time"] = int(round(time.time() * 1000))
				xid += 1
				self.switches_data[dpid]["xid"] = xid
				self.send_barrier_request(dp, xid)
				self._print("BARRIER REQ WITH ID %d SENT" %xid)
				
				self._print(str(self.switches_data.viewitems()))
				time.sleep(0.0625)



	"""
	Install or update a flow rule for a given switch/datapath. 
	"""
	def send_flow_mod(self, datapath, in_port_nr, eth_dst_adr, command_dir):
		ofp = datapath.ofproto
		#self._print(ofp)

		ofp_parser = datapath.ofproto_parser

		cookie = cookie_mask = 0
		table_id = 0
		idle_timeout = 0
		hard_timeout = 10
		priority = 32768
		buffer_id = ofp.OFP_NO_BUFFER

		if command_dir == "ADD":
			command = ofp.OFPFC_ADD
		elif command_dir == "UPDATE":
			command = ofp.OFPFC_MODIFY
		elif command_dir == "DELETE":
			command = ofp.OFPFC_DELETE
		else:
			self._print("Not a valid command %s, sending as install" % command_dir)
			command = ofp.OFPFC_ADD



	
		match = ofp_parser.OFPMatch(in_port=in_port_nr, eth_dst= eth_dst_adr)  # DUMMY IP
		actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)]
		inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,actions)]
		req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask,
									table_id, command,
									idle_timeout, hard_timeout,
									priority, buffer_id,
									ofp.OFPP_ANY, ofp.OFPG_ANY,
									ofp.OFPFF_SEND_FLOW_REM,
									match, inst)
		datapath.send_msg(req)

	def send_barrier_request(self, datapath, xid):
		ofp_parser = datapath.ofproto_parser

		req = ofp_parser.OFPBarrierRequest(datapath)
		req.set_xid(xid)
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

		#TODO BE ABLE TO IDENTIFY RPM FLOW EVENT

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
	
	
	@set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
	def _handle_barrier(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		dpid = datapath.id
		self._print("Barrier datapath %d" % dpid)

		current_time = int(round(time.time() * 1000))
		starting_time = self.switches_data[dpid]["start_time"]
		timed = current_time - starting_time

		self.switches_data[dpid]["measured_time"] = timed
		
		self._print('OFPBarrierReply received')
		# Time taken for installation of all current waiting rules and RTT
		print "Timer from barrier req to resp: %d (ms) for datapath %d" % (timed, datapath.id)


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

		DPIDS = self.switches_DPIDs.viewkeys()

		if len(DPIDS) == self.totalSwitchesNr:
			print DPIDS
			for key in DPIDS:
				print key
				self.switches_data[key] = {"start_time": -1, "measured_time": -1, "xid": -1}
			self._print(str(self.switches_data.viewitems()))

			# Start monitoring thread sending flow mods and barrier requests
			self.monitoring_thread = hub.spawn(self._monitor)
			self._print("Monitoring thread started")
			
			






