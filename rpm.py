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
from datetime import datetime
from ryu.app.ofctl import api
from ryu.ofproto import ofproto_v1_3
import simple_switch_13
import time
import sys
from client import client_side
import threading

from datetime import datetime


# calculate sleeping time for rate request rounds initiated per second
rate = 3
SLEEPING = 1/rate

# current it means that between each round it will be
# at least 3*MIN_SLEEP seconds as there are 3 switches
MIN_SLEEP = 0.03125
SLEEPING =  SLEEPING - MIN_SLEEP*3 # keep the request round rate if possible
if SLEEPING < 0:
	SLEEPING = 0
MODS_NR = 3
LOCK = threading.Lock()
UPDATE_TIME = 1




class RPM(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(RPM, self).__init__(*args, **kwargs)
		# used by RyuApp
		self.datapaths = {} 

		self.net = app_manager._CONTEXTS['network']	#fetch graph object of physical network
		
		self.totalSwitchesNr = self.determineNumberOfSwitches()	#calculate total switches by the graph topology object		
		self.logger.debug("TOTAL SWITCHES: %d", self.totalSwitchesNr)

		# Communication with DM
		url = 'http://127.0.0.1:8000/Tasks.txt'
		self.client = client_side(url)

		#prepare a dictionary for updating and sending to Database
		self.DICT_TO_DB = {'module':'rpm', 'timestamp': -1, 'delays':{}}	
		
		self.switches_DPIDs = {}	# dict to store all datapath ojects by key dpid
		
		self.start_time = 0

		# format {"dpid1": {"start_time": 100, "measured_time": 13, "xid": 1234}}
		self.switches_data = {}
		self.started_monitoring = False

	"""
	Main loop of sending  install/update/delete flow mods to the switches,
	currently max sending ca 32 request every second. i.e send request to a switch every nr_of_switches/32 seconds, 
	any faster sending rate exceeds the serving rate of the event handler and builds up the quequing times.

	TODO Send updates to DM
	"""
	def _monitor(self): 
		lock = threading.Lock()
		xid = 0
		# set of switches
		dpids = self.switches_DPIDs.viewkeys()
		# set starting time counter for sending updates to DM
		last_update_time = int(round(time.time() * 1000))
		#last_update_time = datetime.now().second
		
		# TODO minimum waiting time may change with topology changes, investigate.

		# Sending loop
		update_counter = 0
		looping = True
		while looping:

		#for n in range(100000):  #for testing purposes
			#print "Round nr %d" % n		
			#self._print("SENDING FLOW MODS...")

			for dpid in dpids:
				with lock:
					# if it has gone min UPDATE_TIME seconds since last update
					# send an update to DM 
					current_updatetime = int(round(time.time() * 1000))
					#current_updatetime = datetime.now()

					if (current_updatetime - last_update_time) >= UPDATE_TIME*1000:
						self._print("SEND UPDATE TO DM")
						self.DICT_TO_DB['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
						#print self.DICT_TO_DB.viewitems()
						self.client.postme(self.DICT_TO_DB) #kanske blockerande
						last_update_time = int(round(time.time() * 1000))
						#last_update_time = datetime.now().second
						
						# For testing, to get a specific number of samples
						update_counter += 1
						if update_counter >= 100:
							looping = False
							break

				with lock:
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
					self.switches_data[dpid]["start_time"] = int(time.time() * 1000000)
					#self.switches_data[dpid]["start_time"] = datetime.now().microsecond
					# set xid to be able to identify the response
					xid += 1
					self.switches_data[dpid]["xid"] = xid
					# send the barrier request
					self.send_barrier_request(dp, xid)
					#self._print("BARRIER REQ WITH ID %d SENT" %xid)
				
					#self._print("Data before barrier req: " + str(self.switches_data.viewitems()))

					# wait to send new monitoring requests to another switch,
					# let the other thread handle events for a while
					time.sleep(MIN_SLEEP)

			# sleep time between each request round
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
		#self._print("FLOW REMOVED")

		msg = ev.msg
		dp = msg.datapath
		ofp = dp.ofproto
		ofp_id = dp.id

		#self._print("Switch with id: %d" % ofp_id)

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
		#self._print('OFPBarrierReply received')
		
		msg = ev.msg
		xid = msg.xid
		datapath = msg.datapath
		# DPID from sending switch
		dpid = datapath.id
		# Last sent messages xid
		req_xid = self.switches_data[dpid]["xid"]

		if req_xid == xid:
			with LOCK:
				current_time = int(time.time() * 1000000) 					# current time in 
				#current_time = datetime.now().microsecond
				starting_time = self.switches_data[dpid]["start_time"] 	# also in milliseconds
				timed = current_time - starting_time					# measured time between barrier request and response 
				
				#for datetime
				#MAX = 999999
				#if timed < 0: # Timer started over from 0
				#	timed = (MAX - starting_time) + current_time

			
				# Store the measured time
				self.switches_data[dpid]["measured_time"] = timed
				# Store the measured time in DB message dict
			
				self.DICT_TO_DB['delays'][dpid] = timed
		
				# Time taken for installation of all current waiting rules and RTT 
				#self._print("Timer from barrier req to resp: %d (microsecond) for datapath %d xid %d" % (timed, datapath.id, xid)) # why is this longer for a slower sending rate?!
				#self._print("Start time %d current time %d" % (starting_time, current_time))
		else:
			if xid > req_xid:
				self._print("Sending rate exceeds handling rate")
			else:
				self._print("?!? Something weird is going on, recieving xids out of order")

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

		if len(DPIDS) == self.totalSwitchesNr and self.started_monitoring == False:
			#print DPIDS
			for key in DPIDS:
				#print key
				self.switches_data[key] = {"start_time": -1, "measured_time": -1, "xid": -1}
				self.DICT_TO_DB['delays'][key] = -1
			#self._print(str(self.switches_data.viewitems()))

			# Start monitoring thread sending flow mods and barrier requests
			self.monitoring_thread = hub.spawn(self._monitor)
			self._print("Monitoring thread started")
			self.started_monitoring = True
			
			






