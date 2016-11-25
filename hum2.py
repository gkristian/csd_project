#!/usr/bin/python
import psutil, os, sys, time
from subprocess import check_output

def core_usage():
    cpu_perc = psutil.cpu_percent(interval=0, percpu=True)
    for i in range(len(cpu_perc)):
        print "-"*15
        print "Core Utilization"
        print "Usage of Core", str(i+1),":", str(cpu_perc[i]), "%"
        print "-"*15
def mem_usage():
    memory=psutil.virtual_memory()
    memory_usage=memory.percent
    print "-"*15
    print "Memory Utilization"
    print "Memory:  ",memory_usage, "% "
    print "-"*15


while True:
    time.sleep(5)
    core_usage()
    mem_usage()

