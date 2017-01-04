#author; Adnan Shafi ashafi@kth.se
#NOTES by ashafi:
#On 3 Jan 2016 : During merge, instead of manually removing all ../ relative paths, I ran a vim substitution of ../ to ./. This serves our purpose but you may see e.g. "cd ./HUM" etc.

#################################################   CLONE HELPERS ###############################################
#You can pass the branch name as the command line argument
#make clone branch=RPM
branch = RPM
clone:
	git clone git@gits-15.sys.kth.se:csd-group-4-space-y/sdn_monitoring.git
	mv sdn_monitoring $(branch)
	cd $(branch);git checkout -b $(branch) origin/$(branch)

# Notes:
# Each line below is passed to sh and executed irresepective of the other line
# So to define a variable and make it avaialble across other executions we want to knit all lines below into a one line command
# and that is done by using \ plus since its a shell variable not a makefile varaible so we use syntax $$
# source: http://stackoverflow.com/questions/1909188/define-make-variable-at-rule-execution-time

dmclone:
	branch=DM;echo branch is $$branch;\
	git clone git@gits-15.sys.kth.se:csd-group-4-space-y/sdn_monitoring.git;\
	mv sdn_monitoring $$branch;\
	cd $$branch;git checkout -b $$branch origin/"$$branch";\

#MERGE
# TODO: use fast forward merge: --no-ff 
dmmerge: 
	git merge origin/DM
nfmmerge:
	git merge origin/NFM
cpmmerge:
	git merge origin/controller_core
hummerge:
	git merge origin/hummerge
rpmmerge:
	git merge origin/rpm


	

################################################ CLONE HELPERS end ###############################################


topology:
	# *** Joakim simplest topology, does not have 4 host macs
	#sudo python SimpleTopoMain.py 127.0.0.1 6633
	# *** My midterm topology without bw params, with 4 host macs
	mn --custom ./CPM/src/midterm_topology-nobw.py  --topo topo2 --controller remote --switch ovs,protocols=OpenFlow13  --mac -v debug
	# *** Mininet default topologies with 4 host macs
	#mn  --topo linear,4 --controller remote --switch ovs,protocols=OpenFlow13  --mac -v debug

#modules:
#	sh run_ik2200.sh

setup:
	-mkdir -p /var/www/html/spacey
	-mysql -u root -p12345678 -e 'create database testdb;'
mstart:
	#echo HUM commit in use is 0a57570 > /var/www/html/spacey/ryu_apps.log
	#ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  netflowmodule-not-latest-but-works.py  testController3.py ./RPM/rpm.py ./HUM/hum.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
	#ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  netflowmodule-not-latest-but-works.py  testController3.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
	#ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  netflowmodule-not-latest-but-works.py ./CPM/src/cpm_of13.py ./RPM/rpm.py   > /var/www/html/spacey/ryu_apps.log 2>&1 &
	#below may not log properly, while above is test to work,
	#ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow --verbose --default-log-level 3  --log-file /var/www/html/spacey/cpm_nfm.log ./CPM/src/cpm_of13.py netflowmodule-not-latest-but-works.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
	#ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow --verbose --default-log-level 10  --log-file /var/www/html/spacey/cpm_nfm.log ./CPM/src/cpm_of13.py ./CPM/src/ ./RPM/rpm.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
	

#below runs latest NFM if u use relative path it compains unable to import simple_switch
#	ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  netflowmodule.py  testController3.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
mlog:
	tail -f /var/www/html/spacey/ryu_apps.log
mstop:
	killall -9 ryu-manager
	killall -9 python

	rm -f /var/www/html/spacey/*
	# ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow ./NFM/netflowmodule.py ./NFM/testController3.py ./RPM/rpm.py ./HUM/hum.py
	# ./HUM/hum.py
	# ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py


#dm: this is a compile keyword 'dm' and u wud see dm is up to date message
dmstart:
	rm -f /var/www/html/spacey/dm.log
#python ./dm/dm_main.py > /var/www/html/spacey/dm.log 2>&1
#python ./dm/dm_main.py
#source: http://tldp.org/HOWTO/Bash-Prog-Intro-HOWTO-3.html
# python test.py >test.out 2>&1; pyrg <test.out
	#export SHELL=/bin/bash
	python ./DM/dm_main.py > /var/www/html/spacey/dm.log 2>&1 &
#python ./DM/dm_main.py &> /var/www/html/spacey/dm.log
dmlog:
	tail -f /var/www/html/spacey/dm.log 
dmstop:
	kill -9 `ps a |grep DM |grep -v grep | cut -d ' ' -f 1`
	kill -9 `ps a |grep DM |grep -v grep | cut -d ' ' -f 2`
	#kill -9 `ps a |grep DM |grep -v grep |awk '{print $1}'`
# the dash below before the command is very important. It causes make to still continue run all the commands that start with the - . Without dash if the first command fails to run i.e. return a bad exit code, the make will not run the rest of the commands in that block. Another way is to use make -k that works for gnu make and causes make to keep running despite a command failure, however. make documentation recommends the dash based approach to be better.
stopall: 
	-rm -f /var/www/html/spacey/* 
	-killall -9 python;sleep 3
	-killall -9 ryu-manager
	-killall -9 tail
	-killall -9 mn
	#to kill this for now we can safely kill all prcoeeses .. sh read wait_for_ever_so_that_screen_is_maintained
	-killall -9 sh 
	-mn -c
	-make truncate
truncate:
	 mysql -u root -p12345678 -e 'use testdb; show tables;truncate rpm;truncate rpm_stat;truncate hum;truncate nfm_dropped;truncate nfm_util;show tables; select * from nfm_util, nfm_dropped, rpm, rpm_stat, hum;'
showtables:
#mysql -u root -p12345678 -e 'use testdb; show tables; select * from nfm_util;'
	-mysql -u root -p12345678 -e 'use testdb; show tables;'
	-mysql -u root -p12345678 -e 'use testdb; select * from nfm_util;'
	-mysql -u root -p12345678 -e 'use testdb; select * from nfm_dropped;'
	-mysql -u root -p12345678 -e 'use testdb; select * from rpm;'
	-mysql -u root -p12345678 -e 'use testdb; select * from rpm_stat;'
	-mysql -u root -p12345678 -e 'use testdb; select * from hum;'
show:
	-ps auxw |grep python |grep -v grep
	-ps auxw |grep screen |grep -v grep
	-ps auxw |grep mn |grep -v grep
	-screen -ls
#-ps auxw |grep ryu-manager |grep -v grep

humstart:
	cd ./HUM;make hum > /var/www/html/spacey/hum.log 2>&1 &


spacey:
	make dmstart;
	make humstart;
	make mstart;
#if below statement is commented out, then screen process shall terminate killing all child processes spawned by above make commands. Another way could have been to copy above make commands in startall and run them before make topology as then mininet cli holds the stdout preventing screen from exiting
	read wait_for_ever_so_that_screen_is_maintained 
#screen -d -m some_Command will cause screen session to exit once the command ends
#startall: setup
startall:
	-mn -c 
	screen -S mininet -d -m make topology
	sleep 2
	screen -S spacey -d -m make spacey
#testrest:
#	 python test/rest_test_nfm.py

mnfmfix:
	ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow --default-log-level 3  --log-file /var/www/html/spacey/csd.log NFM/netflowmodule-not-latest-but-works-updated.py CPM/src/cpm_of13.py

mnfmdummy:
	ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow --verbose --default-log-level 10  --log-file /var/www/html/spacey/cpm_nfm.log ./CPM/src/cpm_of13.py ./CPM/src/nfm_metric_push_tester.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
	
