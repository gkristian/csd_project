import os, sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from client import client_side
import time


def __compute_rpm__weight_value_for_node(node_dpid,rpm_metrics_data):
    """

    :param node_dpid: dpid of the node
    :param rpm_metrics_data:  rpm metric data read from the Cache out of which the specified dpid 's RPM weight is to be extracted
    :return: return the RPM weight contributed by this node into the topology graph
    """
    latency_topo_dict = rpm_metrics_data[0][1]
    # Below are values specified by the teacher as a requirement (see metrics spec. document)
    WEIGHTAGE_LATENCY_25 = 0.25
    WEIGHTAGE_LATENCY_75 = 0.25
    WEIGHTAGE_LATENCY_MEDIAN = 0.5

    key_latency_25 = unicode('25th_latency')
    key_latency_75 = unicode('75th_latency')
    key_latency_median = unicode('median_latency')

    switch_dpid_in_unicode = unicode(node_dpid)

    try:
        node_25_value = latency_topo_dict[switch_dpid_in_unicode][key_latency_25]
    except Exception:
        node_25_value = 0
        print "25 value exception hit but its expected as RPM metric data may not contain value for that node"

    try:
        node_75_value = latency_topo_dict[switch_dpid_in_unicode][key_latency_75]
    except Exception:
        node_75_value = 0
        print "75 value exception hit but its expected as RPM metric data may not contain value for that node"

    try:
        node_median_value = latency_topo_dict[switch_dpid_in_unicode][key_latency_median]
    except Exception:
        node_median_value = 0
        print "Median value exception hit but its expected as RPM metric data may not contain value for that node"

    print "computed 25,75,median values are:"
    print node_25_value
    print node_75_value
    print node_median_value

    total_rpm_node_value = node_25_value * WEIGHTAGE_LATENCY_25 + node_75_value * WEIGHTAGE_LATENCY_75 + node_median_value * WEIGHTAGE_LATENCY_MEDIAN
    return total_rpm_node_value


url = 'http://127.0.0.1:8000/Tasks.txt'
DMclient = client_side(url)
"""
currentMillis = int(round(time.time()*1000))

#Every 10 seconds, update flow table

if currentMillis - self.lastTimeRequest > 10000:
	self.lastTimeRequest = currentMillis
	response = self.DMclient.getme({'module':'nfm', 'timestamp':0,'keylist':['link_utilization']})
	self.logger.info("REQUEST FLOW DATA")
"""

#response = self.DMclient.getme({'module':'nfm', 'timestamp':0,'keylist':['link_utilization']})
dict1={'module':'nfm', 'timestamp':0,'keylist':['link_utilization']}

#RPM dict
rpmdict = {'module':'rpm', 'timestamp': -1, 'delays':{}, 'max_delay': -1, 'min_delay': -1, 'mean_delay': -1}

#rpm_keylist = ['delays', 'max_delay', 'min_delay', 'mean_delay']
rpm_keylist = ['delays', 'timestamp','max_delay', 'min_delay', 'mean_delay']

#rest_query_dict_rpm = {'module':'rpm','timestamp': -1, 'keylist':rpm_keylist }
#rest_query_dict_rpm = {'module':'rpm','timestamp': 0, 'keylist':rpm_keylist }
rest_query_dict_rpm = {'module':'rpm','keylist':rpm_keylist }
#__________________________________________________________ignore above___________________________

rpm_what_metrics_to_fetch = {'module': 'rpm', 'keylist': ['latencies']}
"""sample response
[[u'latencies',
  {u'11': {u'25th_latency': 381.9, u'75th_latency': 899.6166666666668, u'median_latency': 609.6222222222221},
   u'24': {u'25th_latency': 158.52222222222224, u'75th_latency': 285.31666666666666,
           u'median_latency': 213.93333333333337},
   u'13': {u'25th_latency': 409.5444444444444, u'75th_latency': 997.8666666666667,
           u'median_latency': 628.7666666666667},
   u'12': {u'25th_latency': 401.3277777777778, u'75th_latency': 953.6777777777777,
           u'median_latency': 632.6444444444444},
   u'21': {u'25th_latency': 412.77222222222224, u'75th_latency': 976.8499999999999,
           u'median_latency': 634.1333333333333},
   u'22': {u'25th_latency': 412.80555555555554, u'75th_latency': 1037.1833333333334,
           u'median_latency': 653.9555555555555},
   u'23': {u'25th_latency': 417.6277777777778, u'75th_latency': 950.2222222222223,
           u'median_latency': 643.1111111111111},
   u'1': {u'25th_latency': 316.97777777777776, u'75th_latency': 845.8166666666667,
          u'median_latency': 556.5666666666667}}]]



"""
#response = self.DMclient.getme(dict1)
rpm_metrics_data = DMclient.getme(rpm_what_metrics_to_fetch)
print "request is"
print rpm_what_metrics_to_fetch
print "And response is "
print rpm_metrics_data

#


node1='21'
node_weight = __compute_rpm__weight_value_for_node(node1,rpm_metrics_data)

node2='11'
node_weight = __compute_rpm__weight_value_for_node(node2,rpm_metrics_data)


node2='non-existen'
node_weight = __compute_rpm__weight_value_for_node(node2,rpm_metrics_data)

print "node weight computed is ",node_weight



# node_rpm_value = latency_topo_dict.get(unicode_src_node,False)
# #If not false
# if node_rpm_value:
#     node_rpm_value.get[unicode_src_node].get()


