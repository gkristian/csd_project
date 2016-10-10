#import libraries and topology
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSBridge
from mininet.link import TCLink
import sys
import os
from mininet.term import makeTerm
from mininet.topo import Topo

# Add current working directory (home/../mininet/custom) to python path
# to get import of modules working from sudo mn
sys.path.append(os.getcwd())

try:
	import Topology2
except:
	sys.path.append(os.path.dirname(Topology2.py))
	try:
		import Topology2
	finally:
		sys.path.remove(os.path.dirname(Topology2.py))

ip=sys.argv[1]
port=sys.argv[2]

print ip
print port

#create the mininet object
net = Mininet( topo=Topology2.Topology2(), switch=OVSBridge, 
	link=TCLink, controller=RemoteController('c0', ip=ip, port=int(port)))

net.start()
#start every node in the network



#Set commands on switches to use OF v 1.3 and enable STP
def command_switch(name, priority, ):
	switch_obj = net.get(name)
	switch_obj.cmd('ovs-vsctl set Bridge '+name+' protocols=OpenFlow13')
	switch_obj.cmd('ovs-vsctl set Bridge', name, 'stp_enable=true', 'other_config:stp-priority=%d' % priority)
	
	#FOR CONNECTIVITY TESTS ONLY
	#switch_obj.cmd('ovs-vsctl add-port '+name+' 

prio = 1000
command_switch('b1', prio)
prio += 1
command_switch('b2', prio)

for x in range(4):
	c = x+1
	switch_name = 's' + `c`
	prio += 1
	command_switch(switch_name, prio)

for x in range(8):
	c = x+1
	switch_name = 'l' + `c`
	prio += 1
	command_switch(switch_name, prio)


def command_host(name):
	host = net.get(name)
	#host.cmd('route add -net 10.0.0.0 netmask 255.0.0.0 dev ' + name + '-eth0')
	#st = host.cmd('ifconfig')
	#print(st)

for x in range(6):
	host = 'u'+`(x+1)`
	command_host(host)
for x in range(3):
	serverH = 'h'+`(x+1)`
	serverF = 'f'+`(x+1)`
	command_host(serverH)
	command_host(serverF)

CLI(net)
net.stop()
