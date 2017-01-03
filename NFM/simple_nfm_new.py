from operator import attrgetter


import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.lib import hub
import json


class SimpleNFM(simple_switch_13.SimpleSwitch13):	
	

	neighbourDict = {}

	def __init__(self, *args, **kwargs):
		super(SimpleNFM, self).__init__(*args, **kwargs)
		self.datapaths = {}
		self.monitor_thread = hub.spawn(self._monitor)
		self.topology_api_app = self

	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		datapath = ev.datapath
		if ev.state == MAIN_DISPATCHER:
			if datapath.id not in self.datapaths:
				self.logger.info('registered datapath: %016x', datapath.id)
				self.datapaths[datapath.id] = datapath
		elif ev.state == DEAD_DISPATCHER:
			if datapath.id in self.datapaths:
				self.logger.info('unregister.datapath: %016x', datapath.id)
				del self.datapaths[datapath.id]
	
	@set_ev_cls(event.EventSwitchEnter)
	def get_topology_data(self, ev):
		switch_list = get_switch(self.topology_api_app, None)
		switches = [switch.dp.id for switch in switch_list]
		links_list = get_link(self.topology_api_app, None)
		links = [(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]
		
		#global self.neighbourDict
		#print "one round"		
		for link in links:
			#self.logger.info("%d %d %s", link[0], link[1], link[2])
			#self.logger.info("Neighbours of switch %s are: ", link[0])
			
			if str(link[0]) in self.neighbourDict:
				nList = self.neighbourDict[str(link[0])]
				nList.append({str(link[1]): link[2]})
				self.neighbourDict[str(link[0])] = nList
			else:
				nList = []
				nList.append({str(link[1]): link[2]})
				self.neighbourDict[str(link[0])] = nList
			#self.logger.info(self.neighbourDict)
		#self.logger.info(switches)
		#self.logger.info(links)
		#self.logger.info(self.neighbourDict)

	

	def _monitor(self):
		while True:
			self.logger.info("REQUESTING...")
			hub.sleep(10)
			#self.logger.info(self.datapaths.values())
			for dp in self.datapaths.values():
				self._request_stats(dp)
			

	def _request_stats(self, datapath):
		self.logger.debug('send stats....')
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)
		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
		datapath.send_msg(req)

	def print_flow_table(self, ev):
		body = ev.msg.body
		self.logger.info('datapath	'
						 ' in-port  eth-dst	    '
						 'out-port packets  bytes')
		self.logger.info('---------------- '
						 '-------- ----------------- '
						 '-------- -------- --------')
		#self.logger.info(body)
		table_list = []
		for stat in [flow for flow in body if flow.priority >= 0]:
			in_port = -1
			eth_dest = -1
			if 'in_port' in stat.match:
				in_port = stat.match['in_port']
			if 'eth_dst' in stat.match:
				eth_dest = stat.match['eth_dst']
			self.logger.info('%016x %8x %17s %8x %8d %8d',
							ev.msg.datapath.id,
							in_port, eth_dest,
							stat.instructions[0].actions[0].port,
							stat.packet_count, stat.byte_count)
			table_list.append([in_port, eth_dest, stat.instructions[0].actions[0].port, stat.packet_count, stat.byte_count])
		self.logger.info(table_list)
		self.logger.info('\n')


	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
#		body = ev.msg.body

#		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
#						indent=3, sort_keys=True))
#		self.logger.info('datapath		'
#						 'in-port	eth-dst			'
#						 'out-port	packets	bytes')
#		self.logger.info('------------------'
#						 '--------  --------------'
#						 '--------  ------- ------')
#		for stat in sorted([flow for flow in body if flow.priority == 1],
#						key=lambda flow: (flow.match['in_port'],
#										  flow.match['eth_dst'])):
#			self.logger.info('%016x %8x %17s %8x %8d %8d',
#							ev.msg.datapath.id,
#							stat.match['in_port'], stat.match['eth_dst'],
#							stat.instructions[0].actions[0].port,
#							stat.packet_count, stat.byte_count)
		
		self.print_flow_table(ev)
		#self.print_json(ev)		
		#a = 10

	def getFlows(table):
		global neighbourDict
		#DO SOMETHING

	def print_json(self, ev):
		self.logger.info('datapath id: %016x', ev.msg.datapath.id)
		self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
						indent=3, sort_keys=True))

	def print_port_table(self, ev):
		body = ev.msg.body

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


	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def _port_stats_reply_handler(self, ev):
		#self.print_port_table(ev)
		self.logger.info('\n\n\n')







