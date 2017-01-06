Branch for DM stuff  

MAIN FILES:  
dm_main.py : Main file to run DM function. Import other classes  
dbaccess.py : Class to access to SQL database.  
Cache.py : Class for cache function  
cache_exception : handle exception in cache  

Dependencies :
repeattimer.py  
server.py : for dm_main  
client.py : Handle Modules

To export nfm_util:  
1. Open sql prompt
2. Run this command   
SELECT * INTO OUTFILE '/var/lib/mysql-files/out.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' FROM nfm_util; 
3. Do > sudo su 
4. Copy out.csv to your local machine
5. Use "Get external data" wizard in excel to get the correct result
