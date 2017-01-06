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
	# function to start a server in another thread,
	# takes a port number and a queue pointer
	def start_serving(port, cache, name, quit):
		PORT = port
		h=ServerHandler
		httpd=Server(("",PORT), h)
		print 'Serving %s at Port: %d' % (name, PORT)
		httpd.serve_forever(cache, quit)

	# function to push from cache, used in our repeattimer
	def push_from_cache():
		starttime = time.time()
		if cache.get_state() == True:
			try:
				print "\nPush data from cache to DB:"
				datatosql = cache.push()
				#print "-------------"
				#print "NFM :"; print datatosql['nfm']
				#print "RPM :"; print datatosql['rpm']
				#print "HUM :"; print datatosql['hum']
				#print "-------------"
				db.insert(datatosql)
				#print "Push finished \n"
			except BaseException as e:
				#rt_push.stop()
				print e
		else:
			print "Cache not initialized"
		pushtime = time.time() - starttime
		print "PUSH done. Time needed : %.4f secs" % pushtime

	server_quit = {'interrupted' : False}

	time_intervall = 5 # set time between pushes to db
	#rpm_keys = []
	#hum_keys = []
	#nfm_keys = ['flow', 'delay']

	cache = NotCache()
	db = dbaccess()

	# start pushing old data from the cache to the db, every 2 seconds
	rt_push = RepeatedTimer(time_intervall, push_from_cache) 

	# controller format json
	controller_data = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}

	try:
		# start thread for listening to monitoring modules
		PORT = 8000
		monitor_t = threading.Thread(target=start_serving, args=(PORT, cache, "monitoring modules", server_quit))
		monitor_t.daemon = True
		monitor_t.start()
	except KeyboardInterrupt: # to exit
		rt_push.stop()
		quit['interrupted'] = True
		sys.exit
		#os._exit(0) # ugly but working way to kill threads after we interrupt the server
	except BaseException as e:
		print e
		rt_push.stop()
		server_quit['interrupted'] = True 
		sys.exit

	try:
		# start thread for listening to controller module
		PORT = 8070
		controller_t = threading.Thread(target=start_serving, args=(PORT, cache, "controller module", server_quit))
		controller_t.daemon = True
		controller_t.start()
	except KeyboardInterrupt: # to exit
		rt_push.stop()
		server_quit['interrupted'] = True
		sys.exit
	except BaseException as e:
		print e
		rt_push.stop()
		server_quit['interrupted'] = True 
		sys.exit

	# sleep until we have no more threads , or interupt is called
	while threading.active_count() > 0:
		if server_quit['interrupted']:
			var = 1
			rt_push.stop()
		time.sleep(0.1)

except KeyboardInterrupt: # to exit 
	rt_push.stop()
	server_quit['interrupted'] = True 
	sys.exit
