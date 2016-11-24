#!/usr/bin/python
import psutil, os, sys, time
print "-"*15
print "Core Utilization"
print "-"*15
def core_usage():
    cpu_perc = psutil.cpu_percent(interval=1, percpu=True)
    for i in range(len(cpu_perc)):
        print "Usage of Core", str(i+1),":", str(cpu_perc[i]), "%"
#core_usage()

for i in range(10):
    time.sleep(5)
    core_usage()


print "-"*15
