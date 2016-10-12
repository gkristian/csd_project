import threading
import Queue
import json
import time
from Cache import NotCache
from dbaccess import dbaccess
from server import Server
from server import ServerHandler
from repeattimer import RepeatedTimer
import os
import sys
 
try:

	# TODO, structure to quit threads cleanly

	time_intervall = 2 # set time between pushes to db
	rpm_keys = []
	hum_keys = []
	nfm_keys = ['flow', 'delay']


	cache = NotCache(nfm_keys,'nfm', hum_keys,'hum', rpm_keys, 'rpm')
	db = dbaccess()


	# controller format json
	controller_data = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}


	#START SERVERHANDLER THREAD
	# function to start a server in another thread,
	# takes a port number and a queue pointer
	def start_serving(port, cache, name):
		PORT = port
		h=ServerHandler
		httpd=Server(("",PORT), h)
		print '\nServing %s at Port: %d' % (name, PORT)
		httpd.serve_forever(cache)

	try:
		# start thread for listening to monitoring modules
		PORT = 8000
		monitor_t = threading.Thread(target=start_serving, args=(PORT, cache, "monitoring modules"))
		monitor_t.daemon = True
		monitor_t.start()
	except KeyboardInterrupt: # to exit
		os._exit(0) # ugly but working way to kill threads after we interrupt the server
	except BaseException as e:
	    print e

	try:
		# start thread for listening to controller module
		PORT = 8070
		controller_t = threading.Thread(target=start_serving, args=(PORT, cache, "controller module"))
		controller_t.daemon = True
		controller_t.start()
	except KeyboardInterrupt: # to exit
		os._exit(0) # ugly but working way to kill threads after we interrupt the server
	except BaseException as e:
	    print e

	# function to push from cache, used in our repeattimer
	def push_from_cache():
		try:
			print "\nData pushed from cache:"
			datatosql = cache.push()
			db.insert(datatosql)
			print "Push finished \n"
		except BaseException as e:
			print e

	# start pushing old data from the cache to the db, every 2 seconds
	rt_push = RepeatedTimer(time_intervall, push_from_cache) 

	# sleep until we have no more threads, or interupt is called
	while threading.active_count() > 0:
		time.sleep(0.1)

	rt_push.stop()

except KeyboardInterrupt: # to exit 
	#sys.exit(0)
	os._exit(0) # ugly but working way to kill threads after we interrupt the server

