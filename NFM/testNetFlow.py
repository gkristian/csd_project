import gevent
from gevent import socket
import gflags
from ryu.base import app_manager	#use ryu
from ryu.controller import event
from ryu.lib import hub
from ryu.lib.xflow import netflow
from ryu import cfg

FLAGS = gflags.FLAGS

gflags.DEFINE_string('sflow_listen_host', 'localhost', 'sflow_listen_host')
gflags.DEFINE_integer('sflow_listen_port', 9996, 'sflow_listen_port')


BUFSIZE = 65535

#cfg.CONF.register_opts(opts, 'plow')
#CONF = cfg.CONF


opts = [cfg.StrOpt('address', default='127.0.0.1',
                   help='NetFlow Collector bind address'),
        cfg.IntOpt('port', default=6343,
                   help='NetFlow Collector port'),
        cfg.IntOpt('max_udp_msg_size', default=1472,
                   help='Maximum size of UDP messages')]

cfg.CONF.register_opts(opts, 'plow')


class EventNetFlow(event.EventBase):
	def __init__(self, msg, addrport):
		super(EventNetFlow, self).__init__()
		self.msg = msg
		self.addr, self.port = addrport


#class to monitor sFlows
class NetFlowMonitor(app_manager.RyuApp):
	def __init__(self, *args):
		super(NetFlowMonitor, self).__init__()
		#self.logger.info(args)
		#args = FLAGS(args)
		#self._address = self.CONF.plow.address
		#self._port = self.CONF.plow.port
		#self._udp_msg_size = self.CONF.plow.max_udp_msg_size
		#self._udp_sock = None
		self._address = self.CONF.plow.address
		self._port = self.CONF.plow.port
		self._udp_msg_size = self.CONF.plow.max_udp_msg_size
		self._udp_sock = None
		self.name = 'netflow_monitor'
		#self.start_monitor()

	def start(self):
		self.sock = hub.socket.socket(hub.socket.AF_INET,
		                                   hub.socket.SOCK_DGRAM)
		#self._udp_sock.bind((self._address, self._port))

		#t = hub.spawn(self.recieveThread)
		#super(NetFlowMonitor, self).start()
		#return t
		self.logger.info("START")
	        self._udp_sock = hub.socket.socket(hub.socket.AF_INET,
		                                   hub.socket.SOCK_DGRAM)
		self._udp_sock.bind((self._address, self._port))
		t = hub.spawn(self.recieveThread)
		super(NetFlowMonitor, self).start()
		return t
		"""
		self.logger.info("1")
		#self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #create socket
		self.logger.info("2")
		self.sock.bind(('127.0.0.1', 6343)) #bind to sflow flags
		self.logger.info("3")
		self.monitorThread = hub.spawn(self.recieveThread)
		#self.thread = gevent.spawn_later(0, self.recieveThread)
		self.logger.info("4")
		"""
		

	def recieveThread(self):
		self.logger.info('Listening on %s:%s for sflow agents' % (self._address, self._port))
		while True:
			buf, addr = self._udp_sock.recvfrom(self._udp_msg_size)
			self.logger.info("RECV")
		"""
		self.logger.info('Listening on %s:%s for Netflow agents' % ("127.0.0.1", 6343))
		while True:
			#buf, addr = self._udp_sock.recvfrom(self._udp_msg_size)
			data, addrport = self.sock.recvfrom(BUFSIZE)			
			self.logger.info("RECV")
			msg = netflow.NetFlow.parser(data)
			if msg:
				self.logger.info(msg.__dict__)
			#t = hub.spawn(self._handle, data, addrport)
			#self.threads.append(t)
			#t.link(self.done)
		"""

    	def done(self, gt, *args, **kwargs):
		if gt in self.threads:
			self.threads.remove(gt)



