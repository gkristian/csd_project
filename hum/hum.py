#!/usr/bin/python
import psutil, os, sys, time
from client import client_side
from datetime import datetime
from subprocess import check_output

url = 'http://127.0.0.1:8000/Tasks.txt'
DICT_TO_DB = {'module':'hum', 'timestamp': -1, 'core':{},'memory':-1}
dict_core = {}

def core_usage():
	cpu_perc = psutil.cpu_percent(interval=0, percpu=True)
	for i in range(len(cpu_perc)):
		dict_core[i]=str(cpu_perc[i])
	DICT_TO_DB['core']=dict_core

def mem_usage():
	memory=psutil.virtual_memory()
	memory_usage=memory.percent
	DICT_TO_DB['memory']=memory_usage

def timestamp():
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
	DICT_TO_DB['timestamp']=timestamp


client = client_side(url)
while True:
	timestamp()
	core_usage()
	mem_usage()
#	print DICT_TO_DB.items()
#	nothing here. just so I can do code review
	client.postme(DICT_TO_DB)
	time.sleep(2)
