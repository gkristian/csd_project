# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet


class TestNFM1(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(TestNFM1, self).__init__(*args, **kwargs)
        self.netnfm = app_manager._CONTEXTS['network']
        #self.netnfm_k = kwargs['network']

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.logger.debug("TESTNFM1, self.net.nodes() = %r ||| self.net.edge() = %r",self.netnfm.nodes(), self.netnfm.edges())
        # self.logger.debug("TESTNFM1, self.net_k.nodes() = %r ||| self.net_k.edge() = %r", self.netnfm_k.nodes(),self.netnfm_k.edges())