from Cache import NotCache
from dbaccess import dbaccess
import json
import time
 

cache = NotCache()
db = dbaccess()

#for x in range(1, 100, 1):
#    key = 'nfm%s' % x
#    value = x
#    filling_cache_data[key] = value

# controller format json
list_keys = ['nfm%s' % x for x in range(1, 100, 2)]
controller_json_data = {'module': 'nfm', 'id':000, 'keylist': ['flow','delay']}

# monitor format json
#monitoringmodule_json_data = {'module': 'NFM', 'id': 222}
#for x in range(1, 100, 3):
#    key = 'nfm%s' % x
#   value = 3
#    monitoringmodule_json_data[key] = value


#START SERVERHANDLER THREAD HERE

#PRETEND WE RECEIVE DATA HERE
filling_cache_data = {'module': 'nfm', 'id': 000,'flow':77,'delay':3245} #just dummy data
start = time.clock()

#TEMPORARY. TO DO : remove hardcoded value
# set all values in NFM cache to values dict in data
# not of any correct format, for testing purposes
try:
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
