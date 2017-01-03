#!/usr/bin/python
import linux_metrics as lm
from linux_metrics import cpu_stat
import multiprocessing

def main():
    print '****CPU****'
#    f=multiprocessing.cpu_count()
    for i in range(multiprocessing.cpu_count()):
        cpu= cpu_stat.cpu_percents()
        cpuusage=(100-cpu['idle'])
        print ' CPU usage: %.2f' % cpuusage + '%'

    print '\n'
    print '****Memory****'

    used, total, _, _, _, _ = lm.mem_stat.mem_stats()
    print 'mem Used: %s' % used
    print 'mem total:  %s' % total
    fl=(used*100)/total
    print 'Percent of usage: ',fl ,'%'
    print 'Done!'

if __name__=='__main__':
    while 1:
        main()
