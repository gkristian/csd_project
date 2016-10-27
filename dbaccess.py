#!/usr/bin/python

import MySQLdb
import json

class dbaccess(object):
	"""Classes to access SQL database that contains monitoring data
	@Purwidi 2016
	CURRENT PROGRESS : Just to insert data to SQL database
	input example :
	{'nfm':nfmdict,'rpm':rpmdict,'hum':humdict}
	nfmdict : {'timestamp':'201610221144','link_utilization':{'1-2':0.5,'4-5':0.4}}
	"""

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
		#print("\nInside INSERT. Received input :")
		#print(inputdict)

		#Do insertion to db based on module type. Create table first if it doesnt exist
		nfmdict = inputdict['nfm']
		rpmdict = inputdict['rpm']
		humdict = inputdict['hum']
		#print "NFM Dict";print nfmdict

		#TODO Processing for other modules

		#Predefined queries
		#Table structure. Primary key : composite of timestamp and link
		"""	|timestamp|link |util|
			|'0033'	  |'1-2'|0.7 |
			|'0033'   |'3-4'|0.3 |
			|'0034'   |'1-2'|0.6 |
		"""
		q1 = "CREATE TABLE IF NOT EXISTS nfm(timestamp VARCHAR(30),link VARCHAR(20),util FLOAT, CONSTRAINT timelink PRIMARY KEY (timestamp,link))" 
		q2 = "SELECT * FROM nfm"

		#Create table
		try:
			cursor.execute(q1)
			print "Table created"
		except:
			print "Table exist"

		#Parsing NFM data dictionary and insert to table
		try:
			timestamp = nfmdict['timestamp']
			link_utilization = nfmdict['link_utilization']
			for key in link_utilization:
				q3 = "INSERT INTO nfm(timestamp,link,util) VALUES ('%s','%s',%f)" %(timestamp,key,link_utilization[key])
				cursor.execute(q3)
				#Commit changes in the database
				db.commit()
			print "SUCCESS : Insert into SQL DB"
		except MySQLdb.Error, e:
			print "ERROR : Insertion failed %s" % str(e)
			# Rollback in case there is any error
			db.rollback()

		#disconnect from server
		db.close()
