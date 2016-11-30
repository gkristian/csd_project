modules:
	sh run_ik2200.sh
simple:
	 ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow netflowmodule.py testController3.py rpm.py > /tmp/cc.log &

DM:
	python ./dm/dm_main.py
topology:
	#cd ~/ryu/ && sudo python SimpleTopoMain.py 127.0.0.1 6633
	python SimpleTopoMain.py 127.0.0.1 6633
stopall:
	killall -9 python
	killall -9 ryu-manager
	mn -c


