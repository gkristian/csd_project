#import libraries and topology
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSBridge
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.link import OVSLink
from mininet.link import Link
import sys
import os
from mininet.term import makeTerm
from mininet.topo import Topo

sys.path.append(os.getcwd())

try:
	import SimpleTopo
except:
	sys.path.append(os.path.dirname(SimpleTopo.py))
	try:
		import SimpleTopo
	finally:
		sys.path.remove(os.path.dirname(SimpleTopo.py))

ip=sys.argv[1]
port=sys.argv[2]

#print(ip, port)



#create the mininet object
try:
	net = Mininet( topo=SimpleTopo.SimpleTopo(), switch=OVSSwitch, link=TCLink, controller=RemoteController('c0', ip=ip, port=int(port)))
	#print("SUCCESS")
except:
	print("NO NET")

net.start()
#start every node in the network



#Set commands on switches to use OF v 1.3 and adding a flow
def command_switch(name, priority=None):
	switch_obj = net.get(name)
	
	try:
		switch_obj.cmd('ovs-vsctl set Bridge '+name+' protocols=OpenFlow13')
		#print("Setting protocol correctly")
	except:
		print("Error setting protocol on switch:", name)
	
	try:
		
		if name == 's1':
			switch_obj.cmd('ovs-ofctl -O Openflow13 add-flow '+name+
					' idle_timeout=0,priority=1,in_port=1,actions=output:2')
			switch_obj.cmd('ovs-ofctl -O Openflow13 add-flow '+name+
					' idle_timeout=0,priority=1,in_port=2,actions=output:1')
				
		if name == 's2':
			switch_obj.cmd('ovs-ofctl -O Openflow13 add-flow '+name+
					' idle_timeout=0,priority=1,in_port=1,actions=output:2')
			switch_obj.cmd('ovs-ofctl -O Openflow13 add-flow '+name+
					' idle_timeout=0,priority=1,in_port=2,actions=output=1')
		
	except:
		print("ERROR")	
		
#prio = 1000
#command_switch('b1', prio)
#prio += 1
command_switch('s1')
#prio += 1
command_switch('s2')
#command_switch('s3')
#command_switch('s4')
#command_switch('s5')
#command_switch('s6')
#command_switch('s7')

CLI(net)
net.stop()
