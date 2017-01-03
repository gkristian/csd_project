#!/usr/bin/python
import SimpleHTTPServer
#import SimpleHTTPRequestHandler
import SocketServer
import BaseHTTPServer
import json
import time
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
        self.RequestHandlerClass.initialized['init_cache'] = False
        # listen to modules while not interruped
        while not quit['interrupted']:
            self.handle_request()



class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    # Empty uninitialized varable for holding the cache
    cache = {} #currently an empty dict, will be replaced with our caceh as soon as the server starts
    # key whose value is true of false on main thread receving keybordinterrupt
    quit = {} 
    initialized = {}


    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('content-type','text/html; "charset"="ascii"')
        self.end_headers()


    def do_GET(self):
        get_start_time = time.time()

        self.quit['interrupted']
        if not self.quit['interrupted']:
            print "\nAccepting GET req"
            #print("HEADERS: ", self.headers)
            # Create GET repsponse, standart 1A so to speak
            #SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
            #print 'Get worked properly'; print

            # parse URL key value string into a dict with list of values ie our key names
            query_components = parse_qs(urlparse(self.path).query)
        
            print "view get the GET dict"
            print query_components.viewitems()

            module_name = query_components["module"][0] 
            print module_name

            try:
                if 'keylist' in query_components:

                    keylist = query_components["keylist"]
                    print keylist

                    # create a dict in the format chache wants
                    data = {'module': module_name, 'keylist': keylist}
                
                    cache_get_start_time = time.time()
                    cache_data = json.dumps(self.cache.get_values(data), ensure_ascii=True, encoding='ascii')
                    print cache_data
           
                else:
                    # if no keylist, return a dict of module values
                    cache_data = self.cache.get_all_module_values(module_name)
                    print cache_data

                self._set_headers(200)
                self.send_response(200, cache_data)
                #self.send_header('content-type','text/html ; "charset"="'ascii'"')
                self.end_headers()
                print "GET handling done"

            except BaseException as e:
                print e
                # No key module or keylist
                print "Not correct structure of GET components"
                self._set_headers(400)
                self.send_response(400)
                self.end_headers()


            # if 'module' and 'keylist' in query_components:
            #     # get the module name
            #     module_name = query_components["module"][0] 
            #     #get required keys from list
            #     keylist = query_components["keylist"]

            #     #sent_timestamp = query_components["timestamp"][0]
            #     print module_name
            #     print keylist[0]
                
            #     if keylist[0] == '0':
            #         # if no keylist, return a dict of module values
            #         cache_data = self.cache.get_all_module_values(module_name)
            #     else:
            #         # create a dict in the format chache wants
            #         data = {'module': module_name, 'keylist': keylist}
                
            #         #cache_get_start_time = time.time()
            #         cache_data = json.dumps(self.cache.get_values(data), ensure_ascii=True, encoding='ascii')
            #         print cache_data
            #         #print("Time for cache get %s seconds ---" % (time.time() - cache_get_start_time))

            #     self._set_headers(200)
            #     self.send_response(200, cache_data)
            #     #self.send_header('content-type','text/html ; "charset"="'ascii'"')
            #     self.end_headers()
            #     print "GET handling done"
            # else:
            #     # No key module or keylist
            #     print "Not correct structure of GET components"
            #     self._set_headers(400)
            #     self.send_response(400)
            #     self.end_headers()
        else:
            print "get interrupted"
            sys.exit
        print("Time to process a GET request %s seconds ---" % (time.time() - get_start_time))


    def do_POST(self):
        post_start_time = time.time()

        print self.quit['interrupted']
        if not self.quit['interrupted']:
            print "\nAccepting POST"
            # create response to POST req
            self.send_response(201)
            self.send_header('content-type','text/html ; "charset"="ascii"')
            self.end_headers()

            # Read 
            self.data=self.rfile.read(int(self.headers['Content-Length']))
            #print "DATA FROM RPM IN SERVER"
            #print type(self.data)
            #print self.data 

            if self.cache == None:
                print "No cache!"

            # initialized = {}

            # initialized['nfm'] = False 
            # initialized['rpm'] = False
            # initialized['hum'] = False

            # Load json from POST req
            j_data=json.loads(self.data, encoding='ascii')
            #print type(j_data)
            #print type(j_data['module'])
            #j_data=json.loads(j_data)
            #print "MORE DATA FROM RPM IN SERVER"
            #print j_data.viewitems()
 

            if 'module' in j_data:
                module_name = j_data['module']

                # put the json data in the cache
                #if first time from module x use set_all_values, module name and timestamp 1?
                if 'timestamp' in j_data:
                    #print self.initialized
                    if not self.initialized['init_cache']:
                        all_start_time = time.time()
                        self.cache.set_all_values(self.data)
                        self.initialized['init_cache'] = True
                        #print("Time to initialize cache: %s seconds ---" % (time.time() - all_start_time))
                    else:
                        some_start_time = time.time()
                        self.cache.set_values(self.data)
                        #print("Time to set values cache: %s seconds ---" % (time.time() - some_start_time))
                else:
                    print "1 not a correct json dict"

            else:
                print "2 not a correct json dict"
            #print  self.initialized
            #print "{}".format(j_data)
            print module_name
            ServerHandler.manam= j_data

            print "POST handling done"
            return

        else:
            print "post interrupted"
            sys.exit
        #print("Time to process a POST request %s seconds ---" % (time.time() - post_start_time))



