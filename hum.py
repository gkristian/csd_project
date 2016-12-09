#!/usr/bin/python
import psutil
import time
#import subprocess
import os
import re
from client import client_side
from datetime import datetime
#from subprocess import check_output

url = 'http://127.0.0.1:8000/Tasks.txt'
DICT_TO_DB = {'module':'hum', 'timestamp': -1, 'core':{},'memory':-1}

#FUNCTION DEFINITION
def timestamp():
	#return timestamp
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def core_manual():
	#return core usage measurement by manually calculating value in /proc/stat
	#reference :http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux?noredirect=1&lq=1
	previdle = 0
	prevnonidle = 0
	prevtotal = 0
	with open('/proc/stat','r') as f:
		#print "opened"
		key1="cpu"
		n=0
		for i,line in enumerate(f):
			key="".join((key1,str(n)))
			#get only the line with cpu[i]
			if key in line:
				valuestr = str(line).split()		#split one line to list. delimiter : space
				del valuestr[0]						#delete the name cpu[n]
				val = [int(x) for x in valuestr]	#integer conversion
				#print val
				#calculation of cpu usage in percent
				idle = val[3] + val[4]
				nonidle = val[0]+val[1]+val[2]+val[5]+val[6]+val[7]
				total = idle + nonidle
				totald = total - prevtotal
				idled = idle - previdle
				cpu_percent = (totald-idled)/totald
				print cpu_percent
				previdle = idle
				prevnonidle = nonidle
				prevtotal = total
				n = n+1

def core_mpstat():
	#return core usage measurement (percent) by mpstat
	#Calculated by substracting 100 with %idle (%usage=100-%idle) to get every type of cpu usage (user,kernel,irq,etc)
	dict_core = {}
	os.system("mpstat -P ALL > mpstat.log")
	with open('mpstat.log','r') as mpstatlog:
		n=0
		for i, line in enumerate(mpstatlog):
			if i > 3:
				#cpu data start at line 4
				res=line[-7:] 					#read last 7 char (%idle)
				res = res[:3] + '.' + res[4:] 	#change comma to dot
				res = res.strip()				#remove space and \n
				cpu_usage = 100-float(res)
				#print cpu_usage
				dict_core[n]=str(cpu_usage)
				n=n+1
	return dict_core

def core_psutil():
	#return core usage measurement (percent) by psutil
	dict_core = {}
	cpu_perc = psutil.cpu_percent(interval=0, percpu=True)
	for i in range(len(cpu_perc)):
		dict_core[i]=str(cpu_perc[i])
	return dict_core

def mem_psutil():
	#return percentage of AVAILABLE physical memory. measurement by psutil
	memory=psutil.virtual_memory()
	memory_usage=memory.percent
	return memory_usage

#MAIN PROGRAM
#client = client_side(url)
print "|CPU:psutil	|CPU:mpstat	|MEM:psutil	|MEM:mpstat	|"

while True:
	core_manual()
	#Insert all data to dictionary.
	DICT_TO_DB['timestamp']=timestamp()
	DICT_TO_DB['core']=core_mpstat()
	DICT_TO_DB['memory']=mem_psutil()
	#print DICT_TO_DB
	#client.postme(DICT_TO_DB)
	time.sleep(1) #set measurement interval here (seconds)
