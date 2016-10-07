#!/usr/bin/python
#Classes to access SQL database that contains monitoring data
#@Gregorius 2016

#CURRENT PROGRESS : Just to insert data
#TODO : read sql table
#TODO : modify column name

import MySQLdb
import json

class dbaccess(object):
    def __init__ (self):
	#Database connection
	self.server = "localhost"
	self.user = "root"
	self.password = "12345678"
	self.dbname = "testdb"

    def insert(self, inputdict):
	 # Open database connection
        db = MySQLdb.connect(self.server,self.user,self.password,self.dbname)
        # prepare a cursor object using cursor() method
	cursor = db.cursor()

	print("Inside INSERT. Received input :")
	print(type(inputdict) is str)
	print(inputdict)
	
	#Do insertion to db based on module type. Create table first if it doesnt exist
	nfmdict = json.loads(inputdict['nfm'])
	rpmdict = json.loads(inputdict['rpm'])
	humdict = json.loads(inputdict['hum'])
	
	print (type(nfmdict) is str)	

	print "NFM Dict";print nfmdict
	print "RPM Dict";print rpmdict
	print humdict
#	if nfmdict == 'nfm':
	print "HAHAHA"
	id = nfmdict['id']
	flow = nfmdict['flow']
	delay = nfmdict['delay']
	print "HELLO FROM ADELE"
	print id
	print flow
	print delay
	q1 = "CREATE TABLE IF NOT EXISTS nfm(id INTEGER(30),flow INTEGER(20), delay INTEGER(20), PRIMARY KEY (id))" 
	q2 = "INSERT INTO nfm(id,flow,delay) VALUES (%d,%d,%d)" %(id,flow,delay)
	q3 = "SELECT * FROM nfm"
#	elif table == 'rpm':
#		print "TODO LATER"
#	elif table == 'hum':
#		print "TODO LATER"
#	else:
#		print('Error: module name does not exist')

	try:
		cursor.execute(q1)
	except:
		print "Table exist"
	
	try:
		print "Inserting now"
		cursor.execute(q2)
		cursor.execute(q3)
		#Commit changes in the database
		db.commit()
		return "Insert success!"
	except:
		# Rollback in case there is any error
		db.rollback()

	#disconnect from server
	db.close()
