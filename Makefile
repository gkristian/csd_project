#modules:
#	sh run_ik2200.sh
mstart:
	echo HUM commit in use is 0a57570
	 ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py ../RPM/rpm.py ../HUM/hum.py > /var/www/html/spacey/ryu_apps.log 2>&1 &
#	 ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py rpm.py > /tmp/cc.log &
mlog:
	tail -f /var/www/html/spacey/ryu_apps.log
mstop:
	killall -9 ryu-manager
	# ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow ../NFM/netflowmodule.py ../NFM/testController3.py ../RPM/rpm.py ../HUM/hum.py
	# ../HUM/hum.py
	# ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py


#dm: this is a compile keyword 'dm' and u wud see dm is up to date message
dmstart:
	rm -f /var/www/html/spacey/dm.log
#python ./dm/dm_main.py > /var/www/html/spacey/dm.log 2>&1
#python ./dm/dm_main.py
#source: http://tldp.org/HOWTO/Bash-Prog-Intro-HOWTO-3.html
# python test.py >test.out 2>&1; pyrg <test.out
	#export SHELL=/bin/bash
	python ../DM/dm_main.py > /var/www/html/spacey/dm.log 2>&1 &
#python ../DM/dm_main.py &> /var/www/html/spacey/dm.log
dmlog:
	tail -f /var/www/html/spacey/dm.log 
dmstop:
	kill -9 `ps a |grep DM |grep -v grep | cut -d ' ' -f 1`
topology:
#cd ~/ryu/ && sudo python SimpleTopoMain.py 127.0.0.1 6633
	sudo python SimpleTopoMain.py 127.0.0.1 6633
# the dash below before the command is very important. It causes make to still continue run all the commands that start with the - . Without dash if the first command fails to run i.e. return a bad exit code, the make will not run the rest of the commands in that block. Another way is to use make -k that works for gnu make and causes make to keep running despite a command failure, however. make documentation recommends the dash based approach to be better.
stopall:
	-rm -f /var/www/html/spacey/* 
	-killall -9 python
	-killall -9 ryu-manager
	-killall -9 tail
	-mn -c
truncate:
	 mysql -u root -p12345678 -e 'use testdb; show tables;truncate rpm;truncate rpm_stat;truncate hum;truncate nfm_dropped;truncate nfm_util;show tables; select * from nfm_util, nfm_dropped, rpm, rpm_stat, hum;'
showtables:
	 mysql -u root -p12345678 -e 'use testdb; show tables; select * from nfm_util;'
#	 mysql -u root -p12345678 -e 'use testdb; show tables; select * from nfm_util, nfm_dropped, rpm, rpm_stat, hum;'
show:
	-ps auxw |grep python |grep -v grep
	-#ps auxw |grep ryu-manager |grep -v grep

spacey:
	make dmstart;
	make mstart;
	#if below statement is commented out, then screen process shall terminate killing all child processes spawned by above make commands. Another way could have been to copy above make commands in startall and run them before make topology as then mininet cli holds the stdout preventing screen from exiting
	read wait_for_ever_so_that_screen_is_maintained 
#screen -d -m some_Command will cause screen session to exit once the command ends
startall:
	-mn -c 
	screen -S mininet -d -m make topology
	screen -S spacey -d -m make spacey


