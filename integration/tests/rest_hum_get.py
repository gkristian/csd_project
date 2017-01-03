from client import client_side
import time

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
#dict1={'module':'nfm', 'timestamp':0,'keylist':['link_utilization']}

#RPM dict
#rpmdict = {'module':'rpm', 'timestamp': -1, 'delays':{}, 'max_delay': -1, 'min_delay': -1, 'mean_delay': -1}

nfm_keylist = ['core','memory','timestamp']

#rest_query_dict_rpm = {'module':'rpm','timestamp': -1, 'keylist':rpm_keylist }
rest_query_dict_nfm = {'module':'hum','timestamp': 0, 'keylist':nfm_keylist }

rpm_keylist = []
nfm_keylist = []
hum_keylist = []
#response = self.DMclient.getme(dict1)
response = DMclient.getme(rest_query_dict_nfm)
print "request is"
print rest_query_dict_nfm
print "And response is "
print response
