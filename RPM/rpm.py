from __future__ import division
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
#import simple_switch_13
import time
import sys
from client import client_side
import threading
import numpy
from datetime import datetime


class RPM(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	"""
	Constructor; Retrieving graph object from controller and defining all necessary variables
	"""
	def __init__(self, *args, **kwargs):
		super(RPM, self).__init__(*args, **kwargs)
		# used by RyuApp
		self.datapaths = {} 

		self.shared_context = kwargs['network']


		self.net = None
		rate = None
		self.MIN_SLEEP = None
		self.UPDATE_TIME = None

		rate = 1
		self.MIN_SLEEP = 0.002
		self.UPDATE_TIME = 3


		# Fetch parameters
		# graph object of physical network
		#time.sleep(60)

		#self.net = app_manager._CONTEXTS['network']
		self.net = None
		# Sending round rate
		#rate = self.shared_context.rpm_rate
		# Sleep time between barrier requests
		#self.MIN_SLEEP = self.shared_context.rpm_min_sleep
		# Time between sending DM updates
		#self.UPDATE_TIME = self.shared_context.rpm_update_time	

		self._print("RATE: %d MIN_SLEEP: %d UPDATE_TIME: %d" % (rate, self.MIN_SLEEP, self.UPDATE_TIME))

		#sys.exit()


		
		#calculate total switches by the graph topology object
		#self.totalSwitchesNr = self.determineNumberOfSwitches()
		self.totalSwitchesNr = None		
		self.logger.debug("TOTAL SWITCHES: %d", self.totalSwitchesNr)

		# Set up communication with DM
		url = 'http://127.0.0.1:8000/Tasks.txt'
		self.client = client_side(url)

		#prepare a dictionary for updating and sending to DM
		self.DICT_TO_DB = {'module':'rpm', 'timestamp': -1, 'latencies':{}}	
		
		# dict to store all datapath ojects by key dpid
		self.switches_DPIDs = {}	

		# For latency measurments
		# format {"dpid1": {"start_time": 100, "measured_time": 13, "xid": 1234}}
		self.switches_data = {}
		self.started_monitoring = False
		# "global" value for latency measurment
		self.start_time = None

		# Set up monitoring request thread's sending rate
		# calculate self.SLEEPING time for rate request rounds initiated per second
		self.SLEEPING = 1/rate 

		# current it means that between each round it will be
		# at least 3*self.MIN_SLEEP seconds as there are 3 switches
		#self.MIN_SLEEP = 0.002 # app_manager._CONTEXTS['rpm_min_sleep']
		self.SLEEPING = self.SLEEPING - self.MIN_SLEEP*2# keep the request round rate if possible 
		if self.SLEEPING < 0:
			self.SLEEPING = 0

		self.MODS_NR = 3
		self.LOCK = threading.RLock()
		#self.UPDATE_TIME = app_manager._CONTEXTS['rpm_update_time']

		# list keeping this update sessions latencies
		# the current latency from a a certain switch of number X will be placed 
		# at index X-1 in the list
		#self.latency_array = range(self.totalSwitchesNr)
		self.latency_array = None

		# Min and max values for latency normalization
		self.MAX = 5000
		self.MIN = 500
		self.HAVE_NET = False

	def calculateStats(self):
		for dpid in self.switches_data:
			# Create a numpy array for taking statistiscs from our dynamic python list
			with self.LOCK:
				#print "VALUES LIST for switch %d" % dpid
				#print self.switches_data[dpid]["values_list"]
				if self.switches_data[dpid]["values_array"] == []: # if values array is not set
					self.switches_data[dpid]["values_array"] = numpy.array(self.switches_data[dpid]["values_list"])
					#print "FIRST VALUES ARRAY switch %d" % dpid
					#print self.switches_data[dpid]["values_array"]
				else: 
					self.switches_data[dpid]["values_array"] = numpy.append(self.switches_data[dpid]["values_array"], numpy.array(self.switches_data[dpid]["values_list"]))
					#print "VALUES ARRAY switch %d" % dpid
					#print self.switches_data[dpid]["values_array"]
				
				self.switches_data[dpid]["values_list"] = []

			
			#print self.latency_array
			#self.DICT_TO_DB['mean_latency'] = numpy.mean(self.latency_array)
			self.DICT_TO_DB["latencies"][dpid]['median_latency'] = self.normalize(numpy.median(self.switches_data[dpid]["values_array"]))
			#self.DICT_TO_DB['max_latency'] = numpy.amax(self.latency_array)
			#self.DICT_TO_DB['min_latency'] = numpy.amin(self.latency_array)
			self.DICT_TO_DB["latencies"][dpid]['25th_latency'] = self.normalize(numpy.percentile(self.switches_data[dpid]["values_array"],25))
			self.DICT_TO_DB["latencies"][dpid]['75th_latency'] = self.normalize(numpy.percentile(self.switches_data[dpid]["values_array"],75))
		#print self.DICT_TO_DB.viewitems()

	def normalize(self, value):
		#print "latency %d" % value
		#print "value - min: %d" % (value - self.MIN)
		#print "max - min: %d" % (self.MAX - self.MIN)

		normalized = ((value - self.MIN)/(self.MAX - self.MIN))*100
		#print "normalized: %d" % (normalized*100)
		return normalized

	"""
	Main loop of sending  install/update/delete flow mods to the switches,
	currently max sending ca 32 request every second. i.e send request to a switch every nr_of_switches/32 seconds, 
	any faster sending rate exceeds the serving rate of the event handler and builds up the quequing times.
	"""
	def _monitor(self): 
		lock = threading.Lock()
		xid = 0
		# set of switches
		dpids = self.switches_DPIDs.viewkeys()
		# set starting time counter for sending updates to DM
		last_update_time = int(round(time.time() * 1000))
		#last_update_time = datetime.now().second
		
		# Sending loop
		update_counter = 0
		looping = True
		while looping:
			#self._print("SENDING FLOW MODS...")

			for dpid in dpids:
				with lock:
					# if it has gone min UPDATE_TIME seconds since last update
					# send an update to DM 
					current_updatetime = int(round(time.time() * 1000))
					#current_updatetime = datetime.now()

					if (current_updatetime - last_update_time) >= self.UPDATE_TIME*1000 and self.HAVE_NET == True:
						# calculate and insert statistics into the DB dict
						


						self.calculateStats()
						#self._print("SEND UPDATE TO DM")
						# set timestamp
						self.DICT_TO_DB['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
						
						#print self.DICT_TO_DB.viewitems()
						#print "LOOK AT THE JSON"
						#print json.dumps(self.DICT_TO_DB)

						# send current values to DM

						self.client.postme(self.DICT_TO_DB) #TODO UTKOMMENTERAD
						#print self.DICT_TO_DB.viewitems()

						last_update_time = int(round(time.time() * 1000))
						#last_update_time = datetime.now().second
						
						# For testing, to get a specific number of samples
						#update_counter += 1
						#if update_counter >= self.UPDATE_COUNTER:
						#	looping = False
						#	break

				with lock:
					# Get the datapath object
					dp = self.switches_DPIDs[dpid]

					# Sending flow mods
					self.send_flow_mod(dp, 1, '00:00:00:00:00:00', '00:00:00:00:00:00', "ADD", "NORMAL")


					# number of updates to be sent is equal to toal number of messages to be sent 
					#minus the add and the delete message
					updates = self.MODS_NR - 2
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
					time.sleep(self.MIN_SLEEP)

			# sleep time between each request round
			time.sleep(self.SLEEPING)

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
			with self.LOCK:
				current_time = int(time.time() * 1000000) 					# current time in microseconds
				#current_time = datetime.now().microsecond
				starting_time = self.switches_data[dpid]["start_time"] 	
				timed = current_time - starting_time						# measured time between barrier request and response 
				#normalized_timed = round(self.normalize(timed),2)
				
				#for datetime
				#MAX = 999999
				#if timed < 0: # Timer started over from 0
				#	timed = (MAX - starting_time) + current_time

			
				# Store the measured latency time
				self.switches_data[dpid]["measured_time"] = timed
				# Store the latency value for statistics
				self.switches_data[dpid]["values_list"].append(timed)
				self.latency_array[dpid-1] = timed

				# Store the measured time in DB message dict

				#self.DICT_TO_DB['delays'][dpid] = timed
				#print "Latency: %d microsec" % timed
				#self.DICT_TO_DB['normalized_delays'][dpid] = normalized_timed
				#print "Normalized latency: %d" % normalized_timed 
		
				# Time taken for installation of all current waiting rules and RTT 
				#self._print("Timer from barrier req to resp: %d (microsecond) for datapath %d xid %d" % (timed, datapath.id, xid)) # why is this longer for a slower sending rate?!
				#self._print("Start time %d current time %d" % (starting_time, current_time))
		else:
			if xid > req_xid:
				self._print("ERROR: Sending rate exceeds handling rate")
				self._print("ERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERROR")

			else:
				self._print("ERROR: ?!? Something weird is going on, recieving xids out of order")
				self._print("ERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERRORERROR")


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
		while(True):
			#print app_manager._CONTEXTS['net_ready']
			if self.shared_context.bootstrap_complete == True:
				self._print("RPM NET READY!")
				self.HAVE_NET = True
				self.net = self.shared_context.learnt_topology
				self.totalSwitchesNr = self.determineNumberOfSwitches()
				self.latency_array = range(self.totalSwitchesNr)
				break
			else:
				self._print("RPM NET NOT READY!")
			time.sleep(1)

		if len(DPIDS) == self.totalSwitchesNr and self.started_monitoring == False:
			#print DPIDS
			for key in DPIDS:
				#print key
				self.switches_data[key] = {"start_time": -1, "measured_time": -1, "xid": -1, "values_array": [], "values_list": []}
				self.DICT_TO_DB['latencies'][key] = {"median_latency": -1, "25th_latency": -1, "75th_latency": -1}
				#self.DICT_TO_DB['normalized_delays'][key] = -1
			#self._print(str(self.switches_data.viewitems()))

			# Start monitoring thread sending flow mods and barrier requests
			self.monitoring_thread = hub.spawn(self._monitor)
			self._print("Monitoring thread started")
			self.started_monitoring = True
			
			






