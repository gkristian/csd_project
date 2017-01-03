#!/usr/bin/python
#import MySQLdb
from dbaccess import dbaccess

db = dbaccess()

#Create dummy dictionary
#inputdict = {'module': 'nfm', 'id': 222, 'flow': 68, 'delay': 534 }
nfmdict = {'timestamp':'201610221144','link_utilization':{'1-2':0.5,'4-5':0.4}}
rpmdict = {'timestamp':'0000'}
humdict = {'timestamp':'0000'}
inputdict = {'nfm':nfmdict,'rpm':rpmdict,'hum':humdict}

#insert dictionary. dbaccess decide which table to insert to
db.insert(inputdict)

print  "HELL YEAH"

# disconnect from server
#db.close()
