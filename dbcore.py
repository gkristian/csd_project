#!/usr/bin/python
#import MySQLdb
from dbaccess import dbaccess

db = dbaccess()

#Create dummy dictionary
inputdict = {'module': 'nfm', 'id': 222, 'flow': 68, 'delay': 534 }

#insert dictionary. dbaccess decide which table to insert to
db.insert(inputdict)

print  "HELL YEAH"

# disconnect from server
#db.close()
