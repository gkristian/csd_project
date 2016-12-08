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

def core_mpstat():
	#return core usage measurement (percent) by mpstat
	#Calculated by substracting 100 with %idle (%usage=100-%idle) to get every type of cpu usage (user,kernel,irq,etc)
	os.system("mpstat -P ALL > mpstat.log")
	with open('mpstat.log','r') as mpstatlog:
		for i, line in enumerate(mpstatlog):
			if i > 3:
				#cpu data start at line 4
				res=line[-7:] 					#read last 7 char (%idle)
				res = res[:3] + '.' + res[4:] 	#change comma to dot
				res = res.strip()				#remove space and \n
				cpu_usage = 100- float(res)
				print cpu_usage


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
	core_mpstat()
	#Insert all data to dictionary.
	DICT_TO_DB['timestamp']=timestamp()
	DICT_TO_DB['core']=core_psutil()
	DICT_TO_DB['memory']=mem_psutil()
	#print DICT_TO_DB
	#client.postme(DICT_TO_DB)
	time.sleep(1) #set measurement interval here (seconds)
