from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSBridge
from mininet.link import TCLink
import sys
import os
from mininet.term import makeTerm
from mininet.topo import Topo

sys.path.append(os.getcwd())

# import topology
try:
    import StanfordTopo
except ImportError:
    sys.path.append(os.path.dirname(StanfordTopo.py))
    try:
        import StanfordTopo
    finally:
        sys.path.remove(os.path.dirname(StanfordTopo.py))

# Our main mininet file
# calls the Stanford topology, sets the switches to Open vSwitches i.e SDN capable
# and supplies where to find the controller
ip =sys.argv[1]
port = sys.argv[2]
print ip
print  port
net = Mininet( topo=StanfordTopo.StanfordTopo(), switch=OVSBridge, link=TCLink,
	controller=RemoteController('c0', ip=ip, port=int(port) ) )


net.start()

def command_switch(name, priority, ):
	switch_obj = net.get(name)
	switch_obj.cmd('ovs-vsctl set Bridge '+name+' protocols=OpenFlow13')
	switch_obj.cmd('ovs-vsctl set Bridge', name, 'stp_enable=true', 'other_config:stp-priority=%d' % priority)

prio = 1000
command_switch('b1', prio)
prio += 1
command_switch('b2', prio)



for s in range(10):
	switch_name = 's'+`(s+1)`
	prio += 1
	command_switch(switch_name, prio)


for x in range(7):
	switch_name = 'o'+`(x+1)`
	prio +=1
	command_switch(switch_name, prio)

for x in range(7):
	switch_name = 'p'+`(x+1)`
	prio +=1
	command_switch(switch_name, prio)



CLI(net)

net.stop()
