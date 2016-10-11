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
 
try:
	rpm_keys = []
	hum_keys = []
	nfm_keys = ['flow', 'delay']


	cache = NotCache(nfm_keys,'nfm', hum_keys,'hum', rpm_keys, 'rpm')
	db = dbaccess()


	# controller format json
	controller_data = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}


	#START SERVERHANDLER THREAD HERE

	# The below queue functionality we want to replace with our cache instance

	# test queque to use for communicating json files 
	# this we make a pointer availible to the server
	test_q = Queue.Queue()

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

	# TODO: NOT USED AS OF YET, SERVER CODE NOT READY
	# try:
	# 	# start thread for listening to controller module
	# 	PORT = 8080
	# 	controller_t = threading.Thread(target=start_serving, args=(PORT, test_q, "controller module"))
	# 	controller_t.daemon = True
	# 	controller_t.start()
	# except KeyboardInterrupt: # to exit 
	# 	os._exit(0) # ugly but working way to kill threads after we interrupt the server
	# except BaseException as e:
	#     print e


	print "\nThe current view of  the nfm cache"
	cache.print_module_cache_items("nfm")

	print json.loads(cache.get_all_values())

	#  TODO ONLY FOR TESTING, TO BE REMOVED
	#PRETEND CONTROLLER REQUEST DATA HERE
	try:
		print "\nGet the specified subset of values from NFM:"
	    #returns a subset of  specified module values
		print cache.get_values(controller_data)
		print "Get success"
	except BaseException as e:
	    print e

	# TODO ABOVE IS ONLY FOR TESTING, TO BE REMOVED, NORMAL CODE BELOW


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
	rt_push = RepeatedTimer(2, push_from_cache) 

	# sleep until we have no more threads, or interupt is called
	while threading.active_count() > 0:
		time.sleep(0.1)

	rt_push.stop()

except KeyboardInterrupt: # to exit 
	os._exit(0) # ugly but working way to kill threads after we interrupt the server

