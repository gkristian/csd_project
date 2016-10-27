app:
	cd /home/csd/ryu/ && sh run_ryu.sh
app_con:
	cd /home/csd/ryu/ && sh run_ryuv2.sh
app_nfm:
	cd /home/csd/ryu/ && sh run_nfm.sh
app_nfm2:
	cd /home/csd/ryu/ && sh run_nfmv2.sh
app_nfm_debug:
	cd /home/csd/ryu/ && sh run_nfm_verbose.sh
appgui:
	cd /home/csd/ryu/ && sh run_ryu_gui.sh
topo:
	cd /home/csd/mininet/custom/ && sudo python stanford_main.py
topo_ovs:
	cd /home/csd/mininet/custom/ && sudo mn --custom stanford_main.py
topo2:
	cd /home/csd/mininet/custom/ && sudo python IK2200_topo2_main.py
topo2_ovs:
	cd /home/csd/mininet/custom/ && sudo mn --custom IK2200_topo2_main.py
topo2_ovs_v2:
	cd /home/csd/mininet/custom/ && sudo mn --custom IK2200_topo2_main_v2.py 127.0.0.1 6633
simple:
	cd /home/csd/mininet/custom/ && sudo python SimpleTopoMain.py 127.0.0.1 6653
midterm:
	cd /home/csd/mininet/custom/ && sudo python MidtermTopoMain.py 127.0.0.1 6653
topo3:
	cd /home/csd/mininet/custom/ && sudo mn --custom StanfordTopo.py --switch ovs-stp --topo stanford --controller=remote,ip=127.0.0.1,port=6633
clean:
	sudo mn -c
