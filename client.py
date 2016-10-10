#!/usr/bin/python
import requests
import json
import time
from repeattimer import RepeatedTimer

x1={"summary":"NFM status", "description":"1000 packets comes"}

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

    def getme(self):
        resp=requests.get('http://127.0.0.1:8000/Tasks.txt')
        if resp.status_code !=200:
            print ' No response for GET'
        else:
            print 'Positive response for GET'

# TESTING 

def monitorer(data):
    c=client_side(data)
    c.postme(data)

# NOT USABLE AS OF YET, SERVER NOT READY
def controller(data):
    c=client_side(data)
    c.getme(data)


rt_monitor_module = RepeatedTimer(1, monitorer, x1) 
#rt_controller = RepeatedTimer(1, controller) # NOT USABLE AS OF YET

try:
    time.sleep(3) # your long-running job goes here...
finally:
    rt_monitor_module.stop()
    #rt_controller.stop()


