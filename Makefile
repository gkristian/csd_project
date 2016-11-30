modules:
	sh run_ik2200.sh
simple:
#	 ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py rpm.py > /tmp/cc.log &
	 ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py rpm.py


DM:
	rm -f /var/www/html/spacey/dm.log
	#python ./dm/dm_main.py > /var/www/html/spacey/dm.log 2>&1
	python ./dm/dm_main.py 
topology:
	#cd ~/ryu/ && sudo python SimpleTopoMain.py 127.0.0.1 6633
	python SimpleTopoMain.py 127.0.0.1 6633

# the dash below before the command is very important. It causes make to still continue run all the commands that start with the - . Without dash if the first command fails to run i.e. return a bad exit code, the make will not run the rest of the commands in that block. Another way is to use make -k that works for gnu make and causes make to keep running despite a command failure, however. make documentation recommends the dash based approach to be better.
stopall:
	-rm -f /var/www/html/spacey/* 
	-killall -9 python
	-killall -9 ryu-manager
	-mn -c


