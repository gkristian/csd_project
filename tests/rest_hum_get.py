import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
if not path in sys.path:
    sys.path.insert(1, path)
del path
import logging
logging.basicConfig(filename='hum.log', level=logging.DEBUG,
                        format='%(levelname)s:%(asctime)s:%(message)s')
logger= logging.getLogger(__name__)
logger.info("Starting HUM rest client")

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

#nfm_keylist = ['core','memory','timestamp']
nfm_keylist = ['core','memory']

#rest_query_dict_rpm = {'module':'rpm','timestamp': -1, 'keylist':rpm_keylist }
#rest_query_dict_nfm = {'module':'hum','timestamp': 0, 'keylist':nfm_keylist }
rest_query_dict_nfm = {'module':'hum', 'keylist':nfm_keylist }

rpm_keylist = []
nfm_keylist = []
hum_keylist = []
#response = self.DMclient.getme(dict1)
try:
    response = DMclient.getme(rest_query_dict_nfm)
except Exception,e:
    logger.error(" ___________Excepted: REST lookup FAILED = %r",e)
    logger.error('____________Excepted: Unable to update this key in the graph, here is the traceback', exc_info=True)

try:
    if not response:
        logger.info("response is an empty string")
except Exception,e:
    logger.error("____________Excepted: REST response threw exception = %r",e)
    #below statement will cause the exception to terminate the print and print debug
    logger.error('____________Excepted: Unable to update this key in the graph, here is the traceback', exc_info=True)



print "request is"
print rest_query_dict_nfm
#print "And response is "
#print response
