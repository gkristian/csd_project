from Cache import NotCache
from dbaccess import dbaccess
import json
import time
 
rpm_keys = []
hum_keys = []
nfm_keys = ['flow', 'delay']


cache = NotCache(nfm_keys,'nfm', hum_keys,'hum', rpm_keys, 'rpm')
db = dbaccess()

#for x in range(1, 100, 1):
#    key = 'nfm%s' % x
#    value = x
#    filling_cache_data[key] = value

# controller format json
controller_json_data = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}

#START SERVERHANDLER THREAD HERE

#PRETEND WE RECEIVE DATA HERE
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

	print "Set values finished"
except Exception as e:
    print "EXCEPTION SET"


#PRETEND CONTROLLER REQUEST DATA HERE
try:
	print "Get the specified subset of values from NFM:"
    #returns a subset of  specified module values
	print cache.get_values(json.dumps(controller_json_data))
	print "Get success"
except BaseException as e:
    print e

try:
	print "Data pushed from cache:"
	datatosql = cache.push()
	print (type(datatosql) is str)
	db.insert(datatosql)
except BaseException as e:
	print e

end = time.clock()

print "execution time in seconds:", end - start
