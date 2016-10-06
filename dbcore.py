#!/usr/bin/python
#import MySQLdb
from dbaccess import dbaccess

db = dbaccess()
db.Insert("nfm","our first data")

print  "HELL YEAH"

# disconnect from server
#db.close()
