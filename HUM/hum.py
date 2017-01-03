#!/usr/bin/python
import linux_metrics as lm
from linux_metrics import cpu_stat
import psutil
import time
import multiprocessing
import os
import re
from decimal import *
from client import client_side
from datetime import datetime
import sys, getopt

url = 'http://127.0.0.1:8000/Tasks.txt'
DICT_TO_DB = {'module':'hum', 'timestamp': -1, 'core':{},'memory':-1}

def main(argv):
	#Processing of input argument
	try:
		opts, args = getopt.getopt(argv,"hvrc:m:")
	except getopt.GetoptError:
		print "ERROR"
		help()
		sys.exit(2)
	isVerbose = False
	isRest = False
	for opt, arg in opts:
		if opt == '-h':
			help()
			sys.exit()
		elif opt == '-v':
			isVerbose=True
		elif opt == '-r':
			isRest=True
		elif opt in ("-c"):
			cpu_opt = int(arg)
		elif opt in ("-m"):
			mem_opt = int(arg)

	#MAIN PROGRAM
	#Dictionary definition for manual calculation
	previdleval = [0] * multiprocessing.cpu_count()
	prevnonidleval = [0]* multiprocessing.cpu_count()
	prevtotalval = [0]* multiprocessing.cpu_count()
	keylist=['previdle','prevnonidle','prevtotal']
	inputprevdict = dict(zip(keylist,[previdleval,prevnonidleval,prevtotalval]))

	print "HUM Started"
	if isRest:
		client = client_side(url)
	while True:
		#Insert all data to dictionary.
		if isVerbose:
			verbose(inputprevdict)
		if isRest:
			#Insert timestamp
			DICT_TO_DB['timestamp']=timestamp()

			#Insert core usage to dict
			if cpu_opt == 1:
				DICT_TO_DB['core']=core_manual(inputprevdict)
			elif cpu_opt == 2:
				DICT_TO_DB['core']=core_mpstat()
			elif cpu_opt == 3:
				DICT_TO_DB['core']=core_psutil()
			elif cpu_opt == 4:
				DICT_TO_DB['core']=core_metrics()
			else:
				sys.exit("Wrong input arg of CPU")

			#Insert mem usage to dict
			if mem_opt == 1:
				DICT_TO_DB['memory']=mem_psutil()
			elif mem_opt == 2:
				DICT_TO_DB['memory']=mem_metrics()
			else:
				sys.exit("Wrong input arg of Mem")
			#Send to DM
			try:
				client.postme(DICT_TO_DB)
			except:
				print "Cannot connect to DM"

		time.sleep(1)

def verbose(inputprevdict2):
	print "+++++++++++++++++++++++++++"
	print "CPU USAGE"
	print "manual\t",core_manual(inputprevdict2)
	print "mpstat\t",core_mpstat()
	print "psutil\t",core_psutil()
	print "metrics\t",core_metrics()
	print "MEMORY USAGE"
	print "psutil\t",mem_psutil()
	print "metrics\t",mem_metrics()

def help():
	print 'Usage : hum.py <options> -c <cpu option> -m <memory option>'
	print "Options:"
	print "-v : verbose output"
	print "-r : enable rest api (NEED dm_main TO BE RUN)"
	print "-h : help"
	print "CPU option : 1:manual ; 2:mpstat ; 3:psutil ; 4:metrics"
	print "Memory : 1:psutil ; 2:metrics"

#FUNCTION DEFINITION
def timestamp():
	#return timestamp
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def core_manual(prevdict):
	#return core usage measurement by manually calculating value in /proc/stat
	#reference :http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux?noredirect=1&lq=1
	dict_core = {}
	previdle = prevdict['previdle']
	prevnonidle = prevdict['prevnonidle']
	prevtotal = prevdict['prevtotal']
	with open('/proc/stat','r') as f:
		key1="cpu"
		n=0
		for i,line in enumerate(f):
			key="".join((key1,str(n)))
			#get only the line with cpu[i]
			if key in line:
				valuestr = str(line).split()		#split one line to list. delimiter : space
				del valuestr[0]						#delete the name cpu[n]
				val = [float(x) for x in valuestr]	#integer conversion
				#calculation of cpu usage in percent
				idle = val[3] + val[4]
				nonidle = val[0]+val[1]+val[2]+val[5]+val[6]+val[7]
				total = idle + nonidle
				totald = total - prevtotal[n]
				idled = idle - previdle[n]
				cpu_percent = 100*(totald-idled)/totald #usage in %
				rounded = round(cpu_percent,2)
				#Save result to dictionary
				#print "CPU",n," PERCENT",cpu_percent
				dict_core[n]=rounded
				#Save data for next test
				previdle[n] = idle
				prevnonidle[n] = nonidle
				prevtotal[n] = total
				n =n+1

	#Save result for next test
	prevdict['previdle']=previdle
	prevdict['prevnonidle']=prevnonidle
	prevdict['prevtotal']=prevtotal
	return dict_core

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
				dict_core[n]=round(cpu_usage,2)
				n=n+1
	return dict_core

def core_psutil():
	#return core usage measurement (percent) by psutil
	dict_core = {}
	cpu_perc = psutil.cpu_percent(interval=0, percpu=True)
	for i in range(len(cpu_perc)):
		dict_core[i]=cpu_perc[i]
	return dict_core

def core_metrics():
	#print '****CPU****'
	dict_core = {}
	#f=multiprocessing.cpu_count()
	for i in range(multiprocessing.cpu_count()):
		cpu= cpu_stat.cpu_percents()
		cpuusage=(100-cpu['idle'])
		res=round(cpuusage,2)
		dict_core[i]=res
		#print ' CPU usage: %.2f' % cpuusage + '%'
	#print '\n'
	return dict_core

def mem_metrics():
	#print '****Memory****'
	used, total, _, _, _, _ = lm.mem_stat.mem_stats()
	#print 'mem Used: %s' % used
	#print 'mem total:  %s' % total
	fl=(used*100)/total
	#print 'Percent of usage: ',fl ,'%'
	#print 'Done!'
	return fl

def mem_psutil():
	#return percentage of USED physical memory. measurement by psutil
	mem=psutil.virtual_memory()
	memory_usage=((mem.total-mem.available)*100)/mem.total
	return memory_usage

if __name__ == "__main__":
	main(sys.argv[1:])


