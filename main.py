from Cache import NotCache
import json
import time

cache = NotCache()

filling_cache_data = {'module': 'NFM', 'id': 000}

for x in range(1, 100, 1):
    key = 'nfm%s' % x
    value = x
    filling_cache_data[key] = value

# controller format json
list_keys = ['nfm%s' % x for x in range(1, 100, 2)]
controller_json_data = {'module': 'NFM', 'keylist': list_keys}

# monitor format json
monitoringmodule_json_data = {'module': 'NFM', 'id': 222}
for x in range(1, 100, 3):
    key = 'nfm%s' % x
    value = 3
    monitoringmodule_json_data[key] = value

start = time.clock()

try:
    # set all values in NFM cache to values dict in data
    # not of any correct format, for testing purposes
    cache.set_all_values(json.dumps(filling_cache_data))
except Exception as e:
    print e

try:
    print "Get the specified subset of values from NFM:"
    # returns a subset of  specified module values
    print cache.get_values(json.dumps(controller_json_data))
except BaseException as e:
    print e

try:
    # set a subset of the values for the specified
    print "Set subset of values from NFM, returns the changed dict:"
    print cache.set_values(json.dumps(monitoringmodule_json_data))
except BaseException as e:
    print e


try:
    print "Data pushed from cache:"
    print json.loads(cache.push())

except BaseException as e:
    print e

end = time.clock()

print "execution time in seconds:", end - start
