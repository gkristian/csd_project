import sys
import os
import time

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from client import client_side


def clamp(n, smallest, largest): return max(smallest, min(n, largest))

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
####dict1={'module':'nfm', 'timestamp':0,'keylist':['link_utilization']}
dict1={'module':'nfm', 'keylist':['link_utilization']}

#RPM dict
#rpmdict = {'module':'rpm', 'timestamp': -1, 'delays':{}, 'max_delay': -1, 'min_delay': -1, 'mean_delay': -1}

#old before unicode discussion that worked
#nfm_keylist = ['link_utilization','packet_dropped']
#######nfm_keylist = ['keylist']

#rest_query_dict_rpm = {'module':'rpm','timestamp': -1, 'keylist':rpm_keylist }
#old that worked
#rest_query_dict_nfm = {'module':'nfm','timestamp': 0, 'keylist':nfm_keylist }
#####rest_query_dict_nfm = {'module':'nfm', 'timestamp': 0 ,'keylist': nfm_keylist }
#rest_query_dict_nfm = {'module':'nfm', 'keylist': nfm_keylist }

response = DMclient.getme(dict1)
#######response = DMclient.getme(rest_query_dict_nfm)
print "request is"

"""
Output I got was:
request is
{'keylist': ['link_utilization'], 'module': 'nfm'}
And response is
[[u'link_utilization', {u'2-1': 0.0, u'1-2': 0.0}]]

"""

print  dict1
print "And response is "
print response

response1 = response[0]
graph = response1[1]
del response1
del response

print 'graph = ',graph
#tthe output in log was : 
#graph =  {u'2-1': 0.0, u'1-2': 0.0}

for gkey in graph:
	gkey = gkey.encode('ascii','ignore')
	print gkey, 'corresponds to', graph[gkey]
	src_dpid,dst_dpid =gkey.split('-') #returns a lista
	src_dpid = src_dpid.strip() #default to removing white spaces 
	dst_dpid = dst_dpid.strip() #defaults to removing white spaces
	
	value = clamp(graph[gkey],0,100) #the link_utilization value must be between 0 to 100
	#value = clamp(-300.0023,0,100) #the link_utilization value must be between 0 to 100
	#value2 = clamp(300.0023,0,100) #the link_utilization value must be between 0 to 100
	
	print src_dpid,'-',dst_dpid,'====',value
	

	#self.net.edge[src_dpid][dst_dpid]['link_utilization'] = graph[gkey]
	

	

	
	
	
	
	
	
