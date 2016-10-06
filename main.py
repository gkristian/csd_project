from Cache import NotCache
import json
import time

cache = NotCache()

data = {'module': 'NFM', 'id': 3678}

for x in range(1, 100, 1):
    key = 'nfm%s' % x
    value = x
    data[key] = value

# controller format json
list_keys = []
for x in range(1, 100, 2):
    key = 'nfm%s' % x
    list_keys.append(key)

data1 = {'module': 'NFM', 'keylist': list_keys}

# monitor format json
data2 = {'module': 'NFM', 'id': 3677}

for x in range(1, 100, 3):
    key = 'nfm%s' % x
    value = 3
    data2[key] = value

start = time.clock()

try:
    # set all values in NFM cache to values dict in data
    # not of any correct format, for testing purposes
    cache.set_all_values(json.dumps(data))
except Exception as e:
    print e

try:
    print "Current values of cache of NFM:"
    # returns a subset of  specified module values
    print cache.get_values(json.dumps(data1))
except BaseException as e:
    print e

try:
    # set a subset of the values for the specified
    cache.set_values(json.dumps(data2))
except BaseException as e:
    print e

try:
    print "Current values of cache of NFM:"
    print cache.get_values(json.dumps(data1))
except BaseException as e:
    print e

try:
    print "Data pushed from cache:"
    print json.loads(cache.push())

except BaseException as e:
    print e

end = time.clock()

print "execution time in seconds:", end - start
