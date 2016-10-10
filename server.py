#!/usr/bin/python
import SimpleHTTPServer
#import SimpleHTTPRequestHandler
import SocketServer
import json
#a class for communication that estabish
PORT=8000

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    manam={}
    def _set_headers(self):
        self.send_response(201)
        self.send_header('content-type','text/html')
        self.end_headers()

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        print 'Get worked properly'; print

    def do_POST(self):
        print 'hello'
        self._set_headers()
        print "it is in POST mode"
        self.data=self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(201)
        self.end_headers()
        j_data=json.loads(self.data)
        print "{}".format(j_data)
        ServerHandler.manam= j_data
        return


class sending_json(ServerHandler):
    def __init__(self):
        self.do_POST()
        print 'inam akharish %s ' % j_data

h=ServerHandler
httpd=SocketServer.TCPServer(("",PORT), h)
print 'Serving at Port: ', PORT
print 'outside variable is : %s ' % ServerHandler.manam
httpd.serve_forever()
