from Cache import NotCache
from dbaccess import dbaccess
import json
import time
from server import Server
from server import ServerHandler
import threading
import Queue
 
rpm_keys = []
hum_keys = []
nfm_keys = ['flow', 'delay']


cache = NotCache(nfm_keys,'nfm', hum_keys,'hum', rpm_keys, 'rpm')
db = dbaccess()

# controller format json
controller_json_data = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}

#START SERVERHANDLER THREAD HERE

# The below queue functionality we want to replace with our cache instance

# test queque to use for communicating json files 
# this we make a pointer availible to the server
test_q = Queue.Queue()

# function to start a server in another thread,
# takes a port number and a queue pointer
def start_serving(port, test):
	PORT = port
	h=ServerHandler
	httpd=Server(("",PORT), h)
	print '\nServing at Port: %d' % PORT
	httpd.serve_forever(test)

# start a thread with the function above
PORT = 8000
monitor_t = threading.Thread(target=start_serving, args=(PORT, test_q))
monitor_t.start()


# sleep  for  30 seconds to be able to test sending client requests
time.sleep(30)
# print the queue
print "\nItems in test queue: "
while not test_q.empty():
	print test_q.get()

# BREAK IN TESTED WORKFLOW, NOW ONLY TESTING CACHE TO DB,
# PRETEND WE RECEIVE DATA HERE
filling_cache_data = {'module': 'nfm', 'id': 321,'flow':88,'delay':1111} #just dummy data
filling_cache_data2 = {'module': 'nfm', 'id': 654,'flow':99,'delay':4567}
start = time.clock()

#TEMPORARY. TO DO : remove hardcoded value
# set all values in NFM cache to values dict in data
# not of any correct format, for testing purposes
try:
	cache.set_values(json.dumps(filling_cache_data))
	cache.set_values(json.dumps(filling_cache_data2))
	cache.set_values(json.dumps(filling_cache_data))

	print "\nSet values finished"
except Exception as e:
    print "\nEXCEPTION SET"


#PRETEND CONTROLLER REQUEST DATA HERE
try:
	print "\nGet the specified subset of values from NFM:"
    #returns a subset of  specified module values
	print cache.get_values(json.dumps(controller_json_data))
	print "Get success"
except BaseException as e:
    print e

try:
	print "\nData pushed from cache:"
	datatosql = cache.push()
	db.insert(datatosql)
	print "Pushed finished \n"
except BaseException as e:
	print e

end = time.clock()


print "\nexecution time in seconds:", end - start
