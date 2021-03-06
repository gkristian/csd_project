#!/usr/bin/python


import MySQLdb
import json

class dbaccess(object):
    """Classes to access SQL database that contains monitoring data
    @Purwidi 2016
    CURRENT PROGRESS : Just to insert data to SQL database
    input example :
    {'nfm':nfmdict,'rpm':rpmdict,'hum':humdict}
    
    nfmdict : {'timestamp':'201610221144','link_utilization':{'1-2':0.5,'4-5':0.4}, 'packet_dropped': {DPID, %}}
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
        nfmdict = json.loads(inputdict['nfm'])
        rpmdict = json.loads(inputdict['rpm'])
        humdict = json.loads(inputdict['hum'])
        #print "NFM Dict";print nfmdict


        #Predefined queries
        #Table structure. Primary key : composite of timestamp and link
        """ |timestamp|link |util|dropped|
            |'0033'   |'1-2'|0.7 |0.1   |
            |'0033'   |'3-4'|0.3 |0.3   |
            |'0034'   |'1-2'|0.6 |0.2   |
        """
        q1_nfm_util = "CREATE TABLE IF NOT EXISTS nfm_util(timestamp VARCHAR(30),link VARCHAR(20),util FLOAT, CONSTRAINT timelink PRIMARY KEY (timestamp,link))"
        q1_nfm_dropped = "CREATE TABLE IF NOT EXISTS nfm_dropped(timestamp VARCHAR(30),DPID VARCHAR(20),dropped FLOAT, CONSTRAINT timelink PRIMARY KEY (timestamp,DPID))" 
        q1_rpm = "CREATE TABLE IF NOT EXISTS rpm(timestamp VARCHAR(30),switch VARCHAR(20),median FLOAT, 25th FLOAT, 75th FLOAT, CONSTRAINT timelink PRIMARY KEY (timestamp,switch))"
        #q1_rpm_stat = "CREATE TABLE IF NOT EXISTS rpm_stat(timestamp VARCHAR(30), max FLOAT, min FLOAT, mean FLOAT, median FLOAT, 25th FLOAT, 75th FLOAT, CONSTRAINT timelink PRIMARY KEY (timestamp))" 
        q1_hum = "CREATE TABLE IF NOT EXISTS hum(timestamp VARCHAR(30),core LONGTEXT,memory FLOAT, PRIMARY KEY (timestamp))"

        #Create table
        try:
            cursor.execute(q1_nfm_util)
            #print "Table created : nfm_util"
        except: pass
        
        try:
            cursor.execute(q1_nfm_dropped)
            #print "Table created : nfm_dropped"
        except: pass
        
        try:
            cursor.execute(q1_rpm)
            #print "Table created : rpm"
        except: pass
        
        try:
            cursor.execute(q1_hum)
            #print "Table created : hum"
        except: pass
        
        #Parsing NFM data dictionary and insert to table
        try:
            timestamp = nfmdict['timestamp']
            link_utilization = nfmdict['link_utilization']
            for key in link_utilization:
                q3 = "INSERT INTO nfm_util(timestamp,link,util) VALUES ('%s','%s',%f)" %(timestamp,key,link_utilization[key])
                cursor.execute(q3)
                #Commit changes in the database
                db.commit()
            #print "SUCCESS : Insert NFM util into SQL DB"


            timestamp = nfmdict['timestamp']
            dropped = nfmdict['packet_dropped']
            for key in dropped:
                q3 = "INSERT INTO nfm_dropped(timestamp,DPID,dropped) VALUES ('%s','%s',%f)" %(timestamp,key,dropped[key])
                cursor.execute(q3)
                # Commit changes in the database
                db.commit()
                #print "SUCCESS : Insert NFM dropped into SQL DB"

        except MySQLdb.Error, e:
            print "ERROR : NFM insertion failed %s" % str(e)
            # Rollback in case there is any error
            db.rollback()

        #Parsing HUM data dictionary and insert to table
        try:
            timestamp = humdict['timestamp']
            core_usage = json.dumps(humdict['core'])
            memory_usage = humdict['memory']
            q4 = "INSERT INTO hum(timestamp,core,memory) VALUES ('%s','%s',%f)" %(timestamp,core_usage,memory_usage)
            cursor.execute(q4)
            #Commit changes in the database
            db.commit()
            #print "SUCCESS : Insert HUM into SQL DB"
        except MySQLdb.Error, e:
            print "ERROR : HUM insertion failed %s" % str(e)
            # Rollback in case there is any error
            db.rollback()

        # Parsing RPM data dictionary and insert to table
        try:
            timestamp = rpmdict['timestamp']
            #q_insert = "INSERT INTO rpm_stat(timestamp,max,min,mean,median,25th,75th) VALUES ('%s','%f','%f','%f','%f','%f','%f')" % (timestamp, rpmdict['max_latency'],rpmdict['min_latency'], rpmdict['mean_latency'], rpmdict['median_latency'], rpmdict['25th_latency'], rpmdict['75th_latency'])
            #cursor.execute(q_insert)
            #Commit changes in the database
            #db.commit()

            latencies = rpmdict['latencies']
            for dpid in latencies:
                latency = latencies[dpid]["median_latency"]
                # -1 means no latency yet recorded
                if latency != -1:
                    q_insert = "INSERT INTO rpm(timestamp,switch,median,25th,75th) VALUES ('%s','%s',%f,%f,%f)" % (timestamp, dpid, latencies[dpid]["median_latency"], latencies[dpid]["25th_latency"], latencies[dpid]["75th_latency"])
                    cursor.execute(q_insert)
                    #Commit changes in the database
                    db.commit()
        except MySQLdb.Error, e:
            print "ERROR : RPM insertion failed %s" % str(e)
            # Rollback in case there is any error
            db.rollback()

        #disconnect from server
        db.close()
