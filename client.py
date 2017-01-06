#!/usr/bin/python
import requests
import json
import time
#from repeattimer import RepeatedTimer

class client_side:
    def __init__(self,url):
        print '**Client_Side Server has been initiated**'
        print '\n'
        self.jsonfile=""
        self.url = url

    def postme(self,jsonfile):
        self.jsonfile=jsonfile
        resp=requests.post(self.url,json=self.jsonfile)
        if resp.status_code !=201:
            print 'Sending POST req: recieved error code %s' % resp.status_code
        else:
            print 'POST request successful'

    def getme(self, data_dict):
        payload = data_dict
        resp=requests.get(self.url, params=payload)
        if resp.status_code !=200:
            print ' Sending GET req: recieved error code %s' % resp.status_code
        else:
            # sift out our data
            json_text_list = resp.text.split("200 ")[1]
            json_text_list = json_text_list.split("Server")[0]
            tuple_list = json.loads(json_text_list)
            
            # return these values in some format
            return tuple_list

            print 'Positive response for GET'


#url = 'http://192.168.43.139:8070/Tasks.txt'
#x1 = {'module': 'nfm', 'timestamp': 000,'keylist':['link_utilization','packet_dropped']} #just dummy data
#x2 = {'module': 'hum', 'timestamp': 000,'keylist':['core','memory']}

#test_cl = client_side(url)
#json1 = test_cl.getme(x1)
#json2 = test_cl.getme(x2)

#print json1
#print "\n"
#print json2

