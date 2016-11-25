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


class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #self.logger.info("key params: type(ev.msg)=%r , dir(ev.msg)=%r", type(ev.msg), dir(ev.msg), (ev.msg))
        self.logger.info("key params: type(ev.msg)=%r , dir(ev.msg)=%r", type(ev.msg), dir(ev.msg))
        self.logger.info("key params: ev.msg=%r", ev.msg)
        self.logger.info("key params: type(ofproto)=%r , ofproto=%r", type(ofproto), ofproto)
        self.logger.info("key params: type(parser)=%r , parser=%r", type(parser), parser)

        self.logger.info("key params: dir(ofproto)=%r", dir(ofproto))
        self.logger.info("key params: dir(parser)=%r", dir(parser))
        """
        Above logger showed below output:
        key params: type(ev.msg)=<class 'ryu.ofproto.ofproto_v1_3_parser.OFPPacketIn'> ,
         dir(ev.msg)=['_TYPE', '__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_base_attributes', '_class_prefixes', '_class_suffixes', '_decode_value', '_encode_value', '_get_decoder', '_get_default_decoder', '_get_default_encoder', '_get_encoder', '_get_type', '_is_class', '_restore_args', '_serialize_body', '_serialize_header', '_serialize_pre', 'buf', 'buffer_id', 'cls_from_jsondict_key', 'cls_msg_type', 'cookie', 'data', 'datapath', 'from_jsondict', 'match', 'msg_len', 'msg_type', 'obj_from_jsondict', 'parser', 'reason', 'serialize', 'set_buf', 'set_classes', 'set_headers', 'set_xid', 'stringify_attrs', 'table_id', 'to_jsondict', 'total_len', 'version', 'xid']
        key params: ev.msg=OFPPacketIn(buffer_id=260,cookie=0,data='33\x00\x00\x00\xfb\xfa\x19\x0b-2\xb7\x86\xdd`\x04F\x1f\x005\x11\xff\xfe\x80\x00\x00\x00\x00\x00\x00\xf8\x19\x0b\xff\xfe-2\xb7\xff\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfb\x14\xe9\x14\xe9\x005\xa0\xba\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x05_ipps\x04_tcp\x05local\x00\x00\x0c\x00\x01\x04_ipp\xc0\x12\x00\x0c\x00\x01',match=OFPMatch(oxm_fields={'in_port': 4}),reason=0,table_id=0,total_len=107)
        key params: type(ofproto)=<type 'module'> , ofproto=<module 'ryu.ofproto.ofproto_v1_3' from '/usr/local/lib/python2.7/dist-packages/ryu/ofproto/ofproto_v1_3.pyc'>
        key params: type(parser)=<type 'module'> , parser=<module 'ryu.ofproto.ofproto_v1_3_parser' from '/usr/local/lib/python2.7/dist-packages/ryu/ofproto/ofproto_v1_3_parser.pyc'>


        """
        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']
	
        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)
