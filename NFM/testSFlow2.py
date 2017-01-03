# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from ryu import cfg
from ryu.base import app_manager
from ryu.lib import hub
from ryu.lib.xflow import sflow


opts = [cfg.StrOpt('address', default='127.0.0.1',
                   help='sFlow Collector bind address'),
        cfg.IntOpt('port', default=6343,
                   help='sFlow Collector port'),
        cfg.IntOpt('max_udp_msg_size', default=1472,
                   help='Maximum size of UDP messages')]

cfg.CONF.register_opts(opts, 'plow')


"""
RUN THIS COMMAND ON SWITCH(ES) 
ovs-vsctl -- --id=@sflow create sflow agent=eth0 target=\"127.0.0.1:6343\" header=128
sampling=10 polling=20 -- set bridge SWITCH sflow=@sflow

"""


class SFlow(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(SFlow, self).__init__(*args, **kwargs)
        self._address = self.CONF.plow.address
        self._port = self.CONF.plow.port
        self._udp_msg_size = self.CONF.plow.max_udp_msg_size
        self._udp_sock = None

    def _handle(self, buf, addr):
        packet = sflow.sFlow.parser(buf)

        if not packet:
            return

        #print packet.__dict__['samples'][0]
	sampleObject = packet.__dict__['samples'][0]
	#print("SampleObject", sampleObject.__dict__)
	sampleFormat = sampleObject.__dict__['sample_format']
	counterSample = sampleObject.__dict__['sample']
	#print("Countersample", counterSample.__dict__)
	if sampleFormat == 2:
		counterRecords = counterSample.__dict__['counters_records']
		for counterRecord in counterRecords:
			#print("CounterRecord", counterRecord.__dict__)
			counter_data_format = counterRecord.__dict__['counter_data_format']
			if counter_data_format == 1:
				counter_data = counterRecord.__dict__['counter_data']
				print("Counter_Data", counter_data.__dict__)
	elif sampleFormat == 1:
		flowRecords = counterSample.__dict__['flow_records']
		for flowRecord in flowRecords:
			print("FlowRecord", flowRecord.__dict__)
			flow_data_format = flowRecord.__dict__['flow_data_format']
			flow_data = flowRecord.__dict__['flow_data']
			print("Flow Data", flow_data.__dict__)
			

    def _recv_loop(self):
        self.logger.info('Listening on %s:%s for sflow agents' % (self._address, self._port))
	while True:
		buf, addr = self._udp_sock.recvfrom(self._udp_msg_size)
		self.logger.info("RECV")
		t = hub.spawn(self._handle, buf, addr)
		self.threads.append(t)
		t.link(self.done)
		"""
        while True:
            buf, addr = self._udp_sock.recvfrom(self._udp_msg_size)
	    	#(data, port) = self._tcp_sock.recvfrom(512)
			self.logger.info("RECV")
	    	#message = sflow.sFlow.parser(data)
	    	#self.logger.info(message)
			t = hub.spawn(self._handle, buf, addr)
            self.threads.append(t)
	    	t.link(self.done)
		"""

    def start(self):
        self._udp_sock = hub.socket.socket(hub.socket.AF_INET,
                                           hub.socket.SOCK_DGRAM)
        self._udp_sock.bind((self._address, self._port))

	#self._tcp_sock = hub.socket.socket(hub.socket.AF_INET,
	#					hub.socket.SOCK_STREAM)
	#self._tcp_sock.bind(("127.0.0.1", 6343))

        t = hub.spawn(self._recv_loop)
        super(SFlow, self).start()
	return t

    def done(self, gt, *args, **kwargs):
		if gt in self.threads:
			self.threads.remove(gt)

