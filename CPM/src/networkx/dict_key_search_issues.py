#http://stackoverflow.com/questions/16333296/how-do-you-create-nested-dict-in-python

import logging

logging.basicConfig(level=logging.DEBUG )
logger = logging.getLogger(__name__)


d={'cars':8, 'trucks': 5, 'planes':3}

if 'cars' in d:
    logger.info("cars found")


if 'flyingsaucers' in d:
    logger.info("cars found")

#___________________________________________________________________________
#**** You can use get() method if you dont want to get KeyError exception **
d = {"a":1, "b":2}
x = d.get("A",None) #None is the default value
print "x = ",x #if key "A" is not a valid key, x = None

#____________________________________________________________________________
#https://www.tutorialspoint.com/python/dictionary_setdefault.htm

d = {'Name': 'kido', 'Age': 7}

print "Value : %s" %  d.setdefault('Age', None)
print "Value : %s" %  d.setdefault('Country', None)

# ____________________________________________________________________________
students_dict={'me':1, 'him':2, 'their':3}
students_dict['me']=5
logger.info("students_dict = %r",students_dict)

#____________________________below is not allowed _____________________________________

students_dict['dict_setdefaulted']=dict()


students_dict['dict']=dict()

w=dict()


students_dict['dict']['child1'] = 1
logger.info("students_dict = %r",students_dict)

import sys
sys.exit(1)

# ____________________________________________________________________________
# KeyError is thrown if we access a dictionary with a non-existen key without checking if it exists or not
try:
    d['flyingsaucers']
# except KeyError: # if it falls here then it wont end up in the other except block
#    pass
# raise
except Exception:
    # pass
    logger.error("____________________________________")
    # logger.exception("something happened = %r",e)
    logger.exception("something happened ") #program terminates
    logger.error("____________________________________")

    # logger.error('Failed to open file = %r',e, exc_info=True)
    logger.error('Failed to open file ', exc_info=True) #program terminates


