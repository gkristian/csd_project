#!/usr/bin/python
import requests
import json
import time
from repeattimer import RepeatedTimer

x0 = {'module': 'nfm', 'id': 1,'flow':99,'delay':4567}
x1 = {'module': 'nfm', 'id': 10,'flow':88,'delay':1111} #just dummy data

x2 = {'module': 'nfm', 'timestamp':'2016102212324', 'link_utilization': {'1-2' : 0.7, '4-5': 0.3, '6-7': 0.5}}
x3 = {'module': 'nfm', 'timestamp':'2016102223456', 'link_utilization': {'1-2' : 0.8, '4-5': 0.5, '6-7': 0.6}}
x4 = {'module': 'nfm', 'timestamp':'2016102234567', 'link_utilization': {'1-2' : 0.9, '4-5': 0.6, '6-7': 0.7}}

class client_side:
    def __init__(self,jsonfile, url):
        print '**Client_Side Server has been initiated**'
        print '\n'
        self.jsonfile=jsonfile
        self.url = url

    def postme(self,jsonfile):
        self.jsonfile=jsonfile
        resp=requests.post(self.url,json=self.jsonfile)
        if resp.status_code !=201:
            print 'Sending POST req: recieved error code 201 '
        else:
            print 'POST request successful'

    def getme(self, data_dict):
        payload = data_dict
        resp=requests.get(self.url, params=payload)
        if resp.status_code !=200:
            print ' No response for GET'
        else:
            # sift out our data
            json_text_list = resp.text.split("200 ")[1]
            json_text_list = json_text_list.split("Server")[0]
            tuple_list = json.loads(json_text_list)
            
            # return these values in some format
            return tuple_list

            print 'Positive response for GET'

# TESTING 
def monitorer(data):
    url = 'http://192.168.43.139:8000/Tasks.txt'
    url = 'http://127.0.0.1:8000/Tasks.txt'
    c=client_side(data, url)
    c.postme(data)

# NOT USABLE AS OF YET, SERVER NOT READY
def controller(data):
    url = 'http://192.168.43.139:8070/Tasks.txt'
    url = 'http://127.0.0.1:8000/Tasks.txt'
    c=client_side(data, url)
    print "Data to the controller, a tuple list: "
    print c.getme(data)

url = 'http://192.168.43.139:8000/Tasks.txt'
url = 'http://127.0.0.1:8000/Tasks.txt'
c=client_side(x2, url)
c.postme(x2)
time.sleep(3)
c=client_side(x3, url)
c.postme(x3)
time.sleep(3)
c=client_side(x4, url)
c.postme(x4)

#time.sleep(10)
#rt_monitor_module = RepeatedTimer(1, monitorer, x2)

x3 = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}
#rt_controller = RepeatedTimer(1, controller, x3) 

try:
    time.sleep(4) # your long-running job goes here...
finally:
	var = 1
    #rt_monitor_module.stop()
    #rt_controller.stop()


