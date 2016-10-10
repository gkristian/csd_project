#!/usr/bin/python
import SimpleHTTPServer
#import SimpleHTTPRequestHandler
import SocketServer
import BaseHTTPServer
import json
import Queue
import threading

#a class for communication that estabish
PORT=8000

# Define a new kind of HTTP sever
class Server(BaseHTTPServer.HTTPServer):
    def serve_forever(self, test):
        # Get the queue to set data in, to be able to pass it to main
        self.RequestHandlerClass.test_q = test
        # listen to monitoring modules
        BaseHTTPServer.HTTPServer.serve_forever(self)


class ServerHandler(SocketServer.ThreadingMixIn, SimpleHTTPServer.SimpleHTTPRequestHandler):
    # Empty uninitialized varable for holding the queue
    test_q = {}

    def _set_headers(self):
        self.send_response(201)
        self.send_header('content-type','text/html')
        self.end_headers()

    def do_GET(self):
        print "\nAccepting GET req"
        # Create GET repsponse, standart 1A so to speak
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        print 'Get worked properly'; print

        # TODO, fetch data from cache and send it on 
        # that is:
        # fetch data from cache,
        # create GET response and set the fetched data as content

    def do_POST(self):
        print "\nAccepting POST req"
        # create response to POST req
        self._set_headers()
        self.send_response(201)
        self.end_headers()

        # Read 
        self.data=self.rfile.read(int(self.headers['Content-Length']))


        # Load json from POST req
        j_data=json.loads(self.data)

        # put the djson data in the queue
        self.test_q.put(j_data) 
        
        print "{}".format(j_data)
        ServerHandler.manam= j_data

        print "POST handling done"
        return

