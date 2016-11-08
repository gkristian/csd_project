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
import sys

if len(sys.argv) > 4:
	rate = int(sys.argv[2])
	mods_nr = int(sys.argv[3])
	update = int(sys.argv[4])

	if (1/rate) > 0.03125 and update > 3: # minimum values
		print "Taking arguments send %s barrier request every sec , send %s flow mod messages, send updates every %s sec" % (rate, mods_nr, update)
		UPDATE_TIME = update
	else:
		print "Arguments lower than minimum values, going with default values 2 reqs every second, updates every 10 seconds"
		rate = 2
		UPDATE_TIME = 10
else:
	print "Setting default sleeping value to 0.5 seconds"
	#self.sleeping = 0.03125
	rate = 1
	mods_nr = 5
	UPDATE_TIME = 10

SLEEPING = 1/rate
MODS_NR = mods_nr




class RPM(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(RPM, self).__init__(*args, **kwargs)
		# used by RyuApp
		self.datapaths = {} 

		#self.net = app_manager._CONTEXTS['network']	#fetch graph object of physical network

		# TODO HARDCODED, should be recived from controller by CONTEXT or events.
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

		# TODO communication with DM
		# TODO proper format
		self.DICT_TO_DB = {'module':'rpm', 'id': -1, 'delays':{}}	#prepare a dictionary for updating and sending to Database
		
		self.switches_DPIDs = {}	#dict to store all datapath ojects by key dpid
		
		self.start_time = 0

		# format {"dpid1": {"start_time": 100, "measured_time": 13, "xid": 1234}}
		self.switches_data = {}

	"""
	Main loop of sending  install/update/delete flow mods to the switches,
	currently max sending ca 32 request every second. i.e send request to a switch every nr_of_switches/32 seconds, 
	any faster sending rate exceeds the serving rate of the event handler and builds up the quequing times.

	TODO Send updates to DM
	"""
	def _monitor(self): 
		xid = 0
		# set of switches
		dpids = self.switches_DPIDs.viewkeys()
		# set starting time counter for sending updates to DM
		last_update_time = int(round(time.time() * 1000))
		
		# TODO minimum waiting time may change with topology changes, investigate.

		# Sending loop
		while True:			
			#self._print("SENDING FLOW MODS...")
			for dpid in dpids: 
				# Get the datapath object
				dp = self.switches_DPIDs[dpid]

				# Sending flow mods
				self.send_flow_mod(dp, 1, '00:00:00:00:00:00', '00:00:00:00:00:00', "ADD", "NORMAL")
				# number of updates to be sent is equal to toal number of messages to be sent 
				#minus the add and the delete message
				updates = MODS_NR - 2
				out_act = "FLOOD"
				while updates > 0:
					self.send_flow_mod(dp, 1, '00:00:00:00:00:00', '00:00:00:00:00:00', "UPDATE", out_act)
					# Set next update change
					if out_act == "FLOOD":
						out_act = "NORMAL"
					
					if out_act == "NORMAL":
						out_act == "FLOOD"

					updates -= 1

				self.send_flow_mod(dp, 1, '00:00:00:00:00:00', '00:00:00:00:00:00', "DELETE")

				#self._print("FLOW MODS SENT")

				# set start time for measurment
				self.switches_data[dpid]["start_time"] = int(time.time() * 1000)
				# set xid to be able to identify the response
				xid += 1
				self.switches_data[dpid]["xid"] = xid
				# send the barrier request
				self.send_barrier_request(dp, xid)
				self._print("BARRIER REQ WITH ID %d SENT" %xid)
				
				#self._print("Data before barrier req: " + str(self.switches_data.viewitems()))
				
				# if it has gone min UPDATE_TIME seconds since last update
				# send an update to DM 
				current_time = int(round(time.time() * 1000))
				if current_time - last_update_time >= UPDATE_TIME*1000:
					self._print("SEND UPDATE TO DM")
					self.DICT_TO_DB['id'] = self.DICT_TO_DB['id'] + 1
					print self.DICT_TO_DB.viewitems()
					last_update_time = int(round(time.time() * 1000))


				# wait to send new monitoring requests
				time.sleep(SLEEPING)

			#testing
			#break



	"""
	Install, update or delete a flow rule for a given switch/datapath, 
	given in port number and ethernet destination address
	"""
	def send_flow_mod(self, datapath, in_port_nr, eth_src_adr, eth_dst_adr, command_dir, out_action = "NORMAL"):
		ofp = datapath.ofproto
		ofp_parser = datapath.ofproto_parser
		
		# default values, may be changed depending on command
		cookie = cookie_mask = 0
		table_id = 0
		idle_timeout = 0
		hard_timeout = 3
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

		if out_action == "FLOOD":
			out_action = ofp.OFPP_FLOOD
		else:
			out_action = ofp.OFPP_NORMAL

	
		match = ofp_parser.OFPMatch(in_port=in_port_nr, eth_dst= eth_dst_adr, eth_src= eth_src_adr)  		# What does flows does the rule capture, flows should be dummies
		actions = [ofp_parser.OFPActionOutput(out_action, 0)]											# What action should be taken, normal not flood
		inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,actions)]							# set options and compose request
		req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask,				
									table_id, command,
									idle_timeout, hard_timeout,
									priority, buffer_id,
									ofp.OFPP_ANY, ofp.OFPG_ANY,
									ofp.OFPFF_SEND_FLOW_REM,
									match, inst)
		datapath.send_msg(req)

	"""
	Given a datapath object and an xid number send a barrier request
	"""
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
	"""
	Print message with header RPM
	"""
	def _print(self, message):
		self.logger.info("[RPM] " + message)

	"""
	Event handler for the event OFPFlowRemoved, 
	ie. this event is triggered when a flow is removed by timeouts or delete commands
	"""
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

		#self._print(reason)


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
	Event handler for the event OFPBarrierReply, 
	ie. this event is triggered when a barrier reply is sent after 
	a barrier request have forced the switch to install all quequed rules.
	"""
	@set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
	def _handle_barrier(self, ev):
		self._print('OFPBarrierReply received')
		
		msg = ev.msg
		xid = msg.xid
		datapath = msg.datapath
		# DPID from sending switch
		dpid = datapath.id
		# Last sent messages xid
		req_xid = self.switches_data[dpid]["xid"]

		if req_xid == xid:
			current_time = int(time.time() * 1000) 			# current time in milliseconds
			starting_time = self.switches_data[dpid]["start_time"] 	# also in milliseconds
			timed = current_time - starting_time					# measured time between barrier request and response
			# Store the measured time
			self.switches_data[dpid]["measured_time"] = timed
			# Store the measured time in DB message dict
			self.DICT_TO_DB['delays'][dpid] = timed
		
			# Time taken for installation of all current waiting rules and RTT 
			self._print("Timer from barrier req to resp: %d (ms) for datapath %d" % (timed, datapath.id)) # why is this longer for a slower sending rate?!
			self._print("Request xid %d, reply xid %d" % (self.switches_data[dpid]["xid"], xid))
		else:
			if xid > req_xid:
				self._print("Sending rate exceeds handling rate")
			else:
				self._print("?!? Something weird is going on")

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
				self.DICT_TO_DB['delays'][key] = -1
			self._print(str(self.switches_data.viewitems()))

			# Start monitoring thread sending flow mods and barrier requests
			self.monitoring_thread = hub.spawn(self._monitor)
			self._print("Monitoring thread started")
			
			






