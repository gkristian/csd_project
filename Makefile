modules:
	cd ryu/ && sh run_ik2200.sh
topology:
	cd ryu/ && sudo python SimpleTopoMain.py 127.0.0.1 6633
