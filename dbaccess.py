#!/usr/bin/python
#Classes to access SQL database that contains monitoring data
#@Gregorius 2016

#CURRENT PROGRESS : Just to insert data
#TODO : read sql table

import MySQLdb

class dbaccess(object):

    #define class to simulate a simple calculator

    def __init__ (self):
	#Database connection
	self.server = "localhost"
	self.user = "root"
	self.password = "12345678"
	self.dbname = "testdb"

    def Insert(self, type, text):
	 # Open database connection
        db = MySQLdb.connect(self.server,self.user,self.password,self.dbname)
        # prepare a cursor object using cursor() method
        cursor = db.cursor()

	#Create table if not exist
	q = "CREATE TABLE IF NOT EXISTS %s (data VARCHAR(50))" % (type)
	#cursor.execute(q)

        #Insert query
	q = "INSERT INTO nfm(data) VALUES ('%s')" %(text) 

	try:
		cursor.execute(q)
		# Commit your changes in the database
		db.commit()
		return "Insert success!"
	except:
		# Rollback in case there is any error
		db.rollback()

    def getCurrent(self):

        return self.current


#disconnect from server
#db.close()
