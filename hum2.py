#!/usr/bin/python
import psutil, os, sys, time
from client import client_side
from datetime import datetime
from subprocess import check_output

url = 'http://127.0.0.1:8000/Tasks.txt'
DICT_TO_DB = {'module':'hum', 'timestamp': -1, 'core':{},'memory':-1}

def core_usage():
	cpu_perc = psutil.cpu_percent(interval=0, percpu=True)
	for i in range(len(cpu_perc)):
		print "Usage of Core", str(i+1),":", str(cpu_perc[i]), "%"
	return 

def mem_usage():
	memory=psutil.virtual_memory()
	memory_usage=memory.percent
	print "Memory Utilization"
	print "Memory:  ",memory_usage, "% "

def timestamp():
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
	print timestamp

client = client_side(url)
while True:
	timestamp()
	core_usage()
	mem_usage()
	client.postme(DICT_TO_DB)
	time.sleep(1)
