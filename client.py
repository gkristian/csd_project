#!/usr/bin/python
import requests
import json
import time
from repeattimer import RepeatedTimer

x1 = {'module': 'nfm', 'id': 10,'flow':88,'delay':1111} #just dummy data
x2 = {'module': 'nfm', 'id': 20,'flow':99,'delay':4567}

class client_side:
    url='http://127.0.0.1:8000/Tasks.txt'
    def __init__(self,jsonfile):
        print '**Client_Side Server has been initiated**'
        print '\n'
        self.jsonfile=jsonfile

    def postme(self,jsonfile):
        self.jsonfile=jsonfile
        resp=requests.post(client_side.url,json=self.jsonfile)
        if resp.status_code !=201:
            print 'Sending POST req: recieved error code 201 '
        else:
            print 'POST request successful'

    def getme(self, data_dict):
        payload = data_dict
        resp=requests.get('http://127.0.0.1:8000/Tasks.txt', params=payload)
        if resp.status_code !=200:
            print ' No response for GET'
        else:
            # sift out our data
            json_text_list = resp.text.split("200 ")[1]
            json_text_list = json_text_list.split("Server")[0]
            tuple_list = json.loads(json_text_list)
            
            #for x in tuple_list: print x

            # return these values in some format

            return tuple_list

            print 'Positive response for GET'

# TESTING 

def monitorer(data):
    data['id'] += 1
    c=client_side(data)
    c.postme(data)

# NOT USABLE AS OF YET, SERVER NOT READY
def controller(data):
    c=client_side(data)
    print "Data to the controller, a tuple list: "
    print c.getme(data)


rt_monitor_module = RepeatedTimer(1, monitorer, x1)
x3 = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}

rt_controller = RepeatedTimer(1, controller, x3) 

try:
    time.sleep(3) # your long-running job goes here...
finally:
    rt_monitor_module.stop()
    rt_controller.stop()


