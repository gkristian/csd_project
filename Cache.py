import json
from functools import partial
import threading
from cache_exceptions import JsonFormatException
from cache_exceptions import ModuleNotFoundException
from cache_exceptions import MonitoringKeyvalueNotFoundException


class NotCache:
    """Our "cache" according to TA instructions:
    Have to be able to hold all the monitored data all the time and when new data comes; change it out, this means that
    we do not age out seldom used data, if fact we do not care how often it is used. We will always have hit never
    misses (for data that exists).
    What we are left with is a data structure that quickly can put in and retrieve values, making this our NotCache
    Our not cache takes json serialized dicts from monitoring modules of format described in monitorformat.txt,
    json serialized dicts fr om controller in format described in controllerformat.txt, and pushes json serialized
    dicts of dicts, containing old values.
    """

    def __init__(self, *args, **kwargs):
    	self.initialized = False

        nfm_keys = ["key1", "key2", "key3"]
        hum_keys = ["key1", "key2", "key3"]
        rpm_keys = ["key1", "key2", "key3"]

        # current layer of values
        nfm_dict = dict.fromkeys(nfm_keys) #all except module is dummy value keys
        nfm_dict.update({k : 0 for k in nfm_dict.iterkeys()}) # set default values
        nfm_dict['module'] = 'nfm'
        nfm_dict['id'] = 0
 
        hum_dict = dict.fromkeys(hum_keys) #TODO
        hum_dict.update({k : 0 for k in hum_dict.iterkeys()}) # set default values
        hum_dict['module'] = 'hum'
        hum_dict['id'] = 0
    
        rpm_dict = dict.fromkeys(rpm_keys) #TODO
        rpm_dict.update({k : 0 for k in rpm_dict.iterkeys()}) # set default values
        rpm_dict['module'] = 'rpm'
        rpm_dict['id'] = 0
  
        # json string of dicts containing older values
        nfm_old = nfm_dict # TODO change to ordinary dicts 
        hum_old = hum_dict
        rpm_old = rpm_dict

        # define a lock for enabling concurrency
        self.lock = threading.Lock()

        # dict listing current and old layers of values
        self.module_caches = {'nfm': nfm_dict, 'hum': hum_dict, 'rpm': rpm_dict}
        self.module_caches_old = {'nfm': nfm_old, 'hum': hum_old, 'rpm': rpm_old}

    def __print_module_cache_keys(self, module_name):
        """Prints the keys in the cache dictionary with name module_name
        :rtype: dictview
        :type module_name: str
        """
        dict_view = None
        with self.lock:
            if module_name in self.module_caches.viewkeys():
                dict_view = self.module_caches[module_name].viewkeys()
            else:
                raise ModuleNotFoundException("module by name %s does not exists" % module_name)

        print "Unsorted list of keys in sub-cache for %s" % module_name
        for key in dict_view:
            print key

    def print_module_cache_items(self, module_name):
        """Prints the keys in the cache dictionary with name module_name
        :type module_name: str
        """
        dict_view = None

        with self.lock:
            if module_name in self.module_caches.viewkeys():
                dict_view = self.module_caches[module_name].viewitems()
            else:
                raise ModuleNotFoundException("module by name %s does not exists" % module_name)

        print dict_view

    def __set_value(self, key_value_tuple, module_name):
        """Sets the specified key to value in module module
        :type module_name: module name
        :type key_value_tuple: tuple containing (key, value)
        """
        if module_name in self.module_caches.viewkeys():
            current_dict = self.module_caches[module_name]
            key = key_value_tuple[0]
            value = key_value_tuple[1]
            if key in current_dict.viewkeys():
                current_dict[key] = value
            else:
                raise MonitoringKeyvalueNotFoundException("No key %s" % key)
        else:
            raise ModuleNotFoundException("module by name %s does not exists" % module_name)

    def set_values(self, json_string):
        """Set all the values specified for the specified module, retrieved from a json serialized dict
        :type json_string: json serialized dict
        """
        with self.lock:
            json_dict = json.loads(json_string)
            # Fetching monitoring module's values into the module variable
            if 'module' in json_dict:
                module_name = json_dict['module']
                new_id = json_dict['id']
                if module_name in self.module_caches:
                    # create a list of key value tuples out of the dict
                    # to do so remove module name and id, then call items()
                    json_dict.pop('module')
                    json_dict.pop('id')
                    list_tuples = json_dict.items()

                    # set previous data to old
                    self.module_caches_old[module_name] = json.dumps(self.module_caches[module_name])

                    # update id
                    current_dict = self.module_caches[module_name]
                    current_dict['id'] = new_id

                    # create a partial function with module name set
                    # in setvalues, partial function acts as an "adder"
                    # to the self.__set_value according to the given module.
                    setsvalues = partial(self.__set_value, module_name=module_name)

                    # set values with according to (key,value)
                    # List_tuples: key and values that are fetched from json.
                    # setvalues: the latest added key - & -values
                    # MAP goes to apply funciton of setvalues to all sequences of list_tuples
                    map(setsvalues, list_tuples)

                    # for testing purposes, return a view  of the changed dict
                    return json.dumps(self.module_caches[module_name])
                else:
                    raise ModuleNotFoundException("module by name %s does not exists" % module_name)
            else:
                raise JsonFormatException("json string is of incorrect form, refer to monitorformat.txt")

    def set_all_values(self, json_obj):
        """Converts a json string to a dictionary and adds it to the cacheself.module_caches_old[module_name] = new_dict  #initializing 
        :type json_obj: json string of format in format.txt
        """
        with self.lock:
            new_dict = json.loads(json_obj)
            if 'module' in new_dict:
                module_name = new_dict['module']
                if module_name in self.module_caches:
                    # changes places of pointers
                    if self.initialized == False:
                    	self.module_caches_old[module_name] = json.dumps(new_dict)  #initializing 
                    	self.module_caches[module_name] = new_dict
                    	self.initialized = True
                    	print "cAche initialized"
                    else:
                    	self.module_caches_old[module_name] = self.module_caches[module_name]  # set previous current to old
                    	self.module_caches[module_name] = new_dict  # set current to the new dict
                else:
                    raise ModuleNotFoundException("No module %s" % module_name)
            else:
                raise JsonFormatException("json string is of incorrect form, refer to monitorformat.txt")

    def __get_value(self, key, module_name):
        """Get a value from the cache given module name and value key,
        if no such module or key exists it returns an error string
        :param module_name: module name
        :param key: module monitoring value name
        :return: key, value tuple or exception"""

        if module_name in self.module_caches.viewkeys():
            current_dict = self.module_caches[module_name]
            if key in current_dict.viewkeys():
                return key, current_dict.get(key)
            else:
                raise MonitoringKeyvalueNotFoundException("No key %s" % key)
        else:
            raise ModuleNotFoundException("No module %s" % module_name)

    def get_values(self, data_dict):
        """Get the specified values from the dicts of the given module names,
        if no such module exists it returns an error string
        :return: list"""
        data = data_dict

        if 'module' and 'keylist' in data:
            module_name = data['module']
            keylist = data['keylist']

            with self.lock:
                if module_name in self.module_caches:
                    # create a partial func with module set
                    getsvalues = partial(self.__get_value, module_name=module_name, )
                    values = map(getsvalues,
                                 keylist)  # apply this function on every name in the list, eg get all values
                    return values
                else:
                    raise ModuleNotFoundException("No module %s" % module_name)
        else:
            raise JsonFormatException("json string is of incorrect form reefer to controllerformat.txt")

    def get_all_values(self):
        """Get the all values from the dicts,
        if no such module exists it returns an error string
        :return: list"""
        with self.lock:
            return json.dumps(self.module_caches)

    def get_all_module_values(self, module_name):
        """Get all the values from the cache of a given module name,
        if no such module exists it returns an error string
        :param module_name: module name
        :return: json dict or string"""

        with self.lock:
            if module_name in self.module_caches.viewkeys():
                current_dict = self.module_caches[module_name]
                return json.dumps(current_dict)
            else:
                raise ModuleNotFoundException("No module %s" % module_name)

    def push(self):
        """push returns the old set of data,
        a json string serializing a dict containing 3 dicts
        :rtype: json string
        """
        data = {'nfm' : json.loads(self.module_caches_old['nfm']), 'rpm' : json.loads(self.module_caches_old['rpm']), 'hum' : json.loads(self.module_caches_old['hum'])}
        return data

    def get_state(self):
    	return self.initialized

