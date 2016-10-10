#!/usr/bin/python
import requests
import json

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
            print 'didnt work'
        else:
            print 'Im working as POST '
    def getme(self):
        resp=requests.get('http://127.0.0.1:8000/Tasks.txt')
        if resp.status_code !=200:
            print ' No response for GET'
        else:
            print 'Positive response for GET'

class sendout(client_side):
    def __init__(self):
        print()


c=client_side(x1)
c.postme(x1)
c.getme()

