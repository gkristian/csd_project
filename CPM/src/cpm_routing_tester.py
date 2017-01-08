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
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER,DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
import networkx as nx
import logging

#REST
import sys
import os
import time
from datetime import datetime
#import REST client library here provided by DM team
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from client import client_side



class CPMRoutingTester(app_manager.RyuApp):

    time_of_last_push = 0

    def __init__(self, *args, **kwargs):
        super(CPMRoutingTester, self).__init__(*args, **kwargs)
        #self.shared_context =  app_manager._CONTEXTS['network']
        self.shared_context = kwargs['network']
        self.net = self.shared_context.learnt_topology
        #self.bcomplete = self.shared_context.bootstrap_complete
        self.epoc_starttime = int(time.time())
        #file name containing the nfm values, this can also be an absolute path e.g. /etc/cpm_tester.ini
        self.filename_containing_nfm_metrics = "cpm_tester_weights_feeder.txt"

        """
        Pitfall:
        all the variables inside init are class instance variables, while the ones outside init but inside class are class variables that are available to all instances of the class
        * instance variables must always be referred to by self. prefix even during delcaration inside the init method
        * all class methods must have self as first argument (python language requirement)
        * all class methods must be invoked within the class by using the self. prefix.
          In other language such as java, there is no need to use this.class_method() when one method is invoked by another method
          inside the same class

        """

        #NFM dict to be REST pushed to cache
        self.nfmpush = {'module': 'nfm'}
        self.nfmpush['timestamp'] = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.nfmpush['packet_dropped'] = {}
        self.nfmpush['link_utilization'] = {}
        self.NFM_PUSH_TIMER = 4 #push every 4 seconds

        #cpm_routing_tester.log
        # cpmroutinglogger
        self.cpm_test_logger = logging.getLogger("cpm_route" + __name__)
        self.cpm_test_logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler("/var/www/html/spacey/cpm_test.log")
        handler.setLevel(logging.DEBUG)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.cpm_test_logger.addHandler(handler)
        self.cpm_test_logger.info("Initializing CPM_routing_tester logger : It is a module that can change link weights on the runtime by constantly reading them from the file")
        self.cpm_test_logger.info(
            "time_of_last_push = %r",self.time_of_last_push)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        if not self.shared_context.bootstrap_complete:
            self.logger.info(
                " ----------------- NFMDUMMY  NO xxxxxxxx bootstrap NOT complete - doing nothing xxxxxxxx  ------------")
            self.logger.debug("NFMDUMMY:  self.net.nodes() = %r ||| self.net.edge() = %r", self.net.nodes(),
                              self.net.edges())
            # self.logger.debug("TESTNFM1: self.bcomplete = %r",self.bcomplete)
            self.logger.debug("NFMDUMMY: self.bcomplete = %r", self.shared_context.bootstrap_complete)
            return
        self.logger.info(" -------------- NFM  YES booooooooootstrap COMPLETE ------------- ")
        self.logger.debug("NFMDUMMY:  self.net.nodes() = %r ||| self.net.edge() = %r", self.net.nodes(),
                          self.net.edges())
        # self.logger.debug("TESTNFM1: self.bcomplete = %r",self.bcomplete)
        self.logger.debug("NFMDUMMY: self.bcomplete = %r", self.shared_context.bootstrap_complete)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.logger.debug("NFMDUMMY:  self.net.nodes() = %r ||| self.net.edge() = %r",self.net.nodes(), self.net.edges())
        #self.logger.debug("TESTNFM1: self.bcomplete = %r",self.bcomplete)
        self.logger.debug("NFMDUMMY: self.bcomplete = %r", self.shared_context.bootstrap_complete)
        # self.logger.debug("TESTNFM1, self.net_k.nodes() = %r ||| self.net_k.edge() = %r", self.netnfm_k.nodes(),self.netnfm_k.edges())

        #Check1: Is bootstrap completed?
        if not self.shared_context.bootstrap_complete:
            return

        #Check2: Is it time to post the updated topology to the Cache/DM with NFM metrics
        self.current_time = int(round(time.time() * 1000))
        # every 4 seconds
        time_max_limit = self.NFM_PUSH_TIMER * 1000

        #if not (self.current_time - self.time_of_last_fetch > time_max_limit) or self.defines_D['bootstrap_in_progress']:
        if not (self.current_time - self.time_of_last_push > time_max_limit):
            self.cpm_test_logger.debug("CPMTESTER : Time Check Failed : Not Pushing metric to DM, time_of_last_fetch = %r",
                                       self.time_of_last_push)
            return

        self.cpm_test_logger.debug("CPMTESTER : Time Check passed : Pushing metric to DM, time_of_last_fetch = %r",self.time_of_last_push)
        self.time_of_last_push = self.current_time

        #Read wegiths from file


        #self.shared_context.learnt_topology
        """
        Iterating over topology graph using edge_iter
        """
        # Iterate through the graph object
        #for node, data in self.net.nodes_iter(data=True):
        for src_node,dst_node, data in self.net.edges_iter(data=True):
            #post each data element to graph
            src_to_dst_node = str(src_node) + '-' + str(dst_node)
            dst_to_src_node = str(dst_node) + '-' + str(src_node)
            """
            Pitfall:
            One run wasted because of not remembering below:
            src_node and dst_node are of type int() and not str()
            so below threw error and could have only worked if they were str()
            src_to_dst_node = src_node '+' dst_node
            """

            #if src_to_dst_node.__contains__(':'):
            try:
                if ':' in src_to_dst_node:
                    continue
            except Exception,e:
                self.logger.error("Exception encountered when parsing a graph node =%r for : ", e)
                #exc_info causes a Trace exception details to be printed to log but it does not halt program execution
                self.logger.error("Exception encountered when parsing a graph node =%r for : ",src_to_dst_node,exc_info = True)
                #raise #raise causes program termination

            #Intialize nfm_metrics with some values
            self.nfmpush['link_utilization'][src_to_dst_node] = 1
            self.nfmpush['link_utilization'][dst_to_src_node] = 1
            self.nfmpush['packet_dropped'][src_to_dst_node] = 0
            self.nfmpush['packet_dropped'][dst_to_src_node] = 0

            # over load a certain link to test weighted routing
            try:
                self.read_nfm_metrics_from_file_and_update_nfm_metrics()
            except Exception,e:
                self.cpm_test_logger.debug("CPM_FILE_READ block : Exception encountered = %r ",e)
            self.cpm_test_logger.debug("CPM_NFM_METRICS_PRINT: After reading weights from file, this is what nfm_metrics dict to be pushed looks like : \n %r",self.nfmpush)



        self.rest_nfm_post()

            #if (data['bw'] == 10):
            #    self.logger.info("bw is 10")

            # get all edges out from these nodes
            # then recursively follow using a filter for a specific statement_id

            # or get all edges with a specific statement id
            # look for  with a node attribute of "cat"
    def rest_nfm_post(self):
        url = 'http://127.0.0.1:8000/Tasks.txt'
        DMclient = client_side(url)
        response = DMclient.postme(self.nfmpush)
        #######response = DMclient.getme(rest_query_dict_nfm)
        print "request is", self.nfmpush
        print "repsonse is", response

    def update_nfm_metrics(self,src_node_to_dst_node, src_to_dst_link_util_value, src_to_dst_drop_value):
        """
        link_util + drop_value is added and added as a weight to graph. during testing we set drop_value to 0 and use link_util to set weights on the links
        :param src_node_to_dst_node: e.g '21-11' means src_node = 21 and dste_node = 11
        :param src_to_dst_link_util_value:  link_utilization value to be assigned to the link
        :param src_to_dst_drop_value:  can be zero
        :return:
        """
        #src_to_dst_node = str(src_node) + '-' + str(dst_node)
        #dst_to_src_node = str(dst_node) + '-' + str(src_node)
        self.nfmpush['link_utilization'][src_node_to_dst_node] = src_to_dst_link_util_value
        #self.nfmpush['link_utilization'][dst_to_src_node] = dst_to_src_link_util_value
        self.nfmpush['packet_dropped'][src_node_to_dst_node] = src_to_dst_drop_value
        #self.nfmpush['packet_dropped'][dst_to_src_node] = dst_to_src_drop_value

    def read_nfm_metrics_from_file_and_update_nfm_metrics(self):
        #read from file
        try:
            with open(self.filename_containing_nfm_metrics, "r") as f:
                for line in f:
                    line = line.strip()  # remove space from start and end of line
                    # ignore lines i n file beginning with a # continue. I could have also used a pattern matcher '^#' but that would have been expensive
                    if not line or line[0] == '#':
                        continue

                    src_node_to_dst_node, nfm_values = line.split(':')
                    link_util, packet_drops = nfm_values.split(',')
                    #assign nfm values read to nfm_metrics
                    self.update_nfm_metrics(src_node_to_dst_node, link_util, packet_drops)
                    self.cpm_test_logger("NFM_VALUES_READ_FROM_FILE : node =%r , link_util = %r , packet_drops = %r", src_node_to_dst_node, link_util,packet_drops)
        except Exception,e:
            self.cpm_test_logger.error("read_nfm_metric_from_and_update function: Exception encountered = %r",e)







