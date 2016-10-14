#!/usr/bin/python
import SimpleHTTPServer
#import SimpleHTTPRequestHandler
import SocketServer
import BaseHTTPServer
import json
import Queue
import threading
import Cache
from urlparse import urlparse, parse_qs 
import sys


#a class for communication that estabish
PORT=8000

# Define a new kind of HTTP sever
class Server(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def serve_forever(self, cache, quit):
        # Get the queue to set data in, to be able to pass it to main
        self.RequestHandlerClass.cache = cache
        self.RequestHandlerClass.quit = quit
        # listen to modules while not interruped
        while not quit['interrupted']:
            self.handle_request()



class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    # Empty uninitialized varable for holding the cache
    cache = {} #currently an empty dict, will be replaced with our caceh as soon as the server starts
    quit = {} 

    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('content-type','text/html')
        self.end_headers()

    def do_GET(self):
        self.quit['interrupted']
        if not self.quit['interrupted']:
            print "\nAccepting GET req"
            # Create GET repsponse, standart 1A so to speak
            #SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
            #print 'Get worked properly'; print

            # parse URL key value string into a dict with list of values ie our key names
            query_components = parse_qs(urlparse(self.path).query)
        
            print "view get the GET dict"
            print query_components.viewitems()

            # get the values
            module_name = query_components["module"][0] #get value from list
            sent_id = query_components["id"][0]
            keylist = query_components["keylist"]

            # create a dict in the format chache wants
            data = {'module': module_name, 'id':sent_id, 'keylist': keylist}

            print module_name
            print keylist
 
            cache_data = json.dumps(self.cache.get_values(data))

            self._set_headers(200)
            self.send_response(200, cache_data)
            self.end_headers()
            print "GET handling done"
        else:
            print "get interrupted"
            sys.exit

    def do_POST(self):
        print self.quit['interrupted']
        if not self.quit['interrupted']:
            print "\nAccepting POST req"
            # create response to POST req
            self._set_headers(201)
            self.send_response(201)
            self.end_headers()

            # Read 
            self.data=self.rfile.read(int(self.headers['Content-Length']))

            if self.cache == None:
                print "No cache!"

            # Load json from POST req
            j_data=json.loads(self.data)

            # put the json data in the cache
            #if first time from module x use set_all_values, module name and id 0?
            self.cache.set_values(self.data)
        
            print "{}".format(j_data)
            ServerHandler.manam= j_data

            print "POST handling done"
            return

        else:
            print "post interrupted"
            sys.exit
        

