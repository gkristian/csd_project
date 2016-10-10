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
#net = Mininet( topo=StanfordTopo.StanfordTopo(), switch=StanfordTopo.StanfordSTPBridge(),
#	controller=RemoteController('c0', ip='127.0.0.1', port=6633 ) )

#net = Mininet( topo=StanfordTopo.StanfordTopo(), switch=OVSBridge,
#	controller=RemoteController('c0', ip='127.0.0.1', port=6633 ) )

ip =sys.argv[1]
port = sys.argv[2]
print ip
print  port
net = Mininet( topo=StanfordTopo.StanfordTopo(), switch=OVSBridge, link=TCLink,
	controller=RemoteController('c0', ip=ip, port=int(port) ) )




#Get all hosts from net object to do cmd calls on
#net.start()
net.start()

def command_switch(name, priority, ):
	switch_obj = net.get(name)
	switch_obj.cmd('ovs-vsctl set Bridge '+name+' protocols=OpenFlow13')
	#switch_obj.cmd('ovs-vsctl set Bridge '+name+' stp_enable=true')
	#switch_obj.cmd('ovs-vsctl set-fail-mode', name, 'standalone')
	#switch_obj.cmd('ovs-vsctl set-controller', name, 'tcp:127.0.0.1:6633')
	switch_obj.cmd('ovs-vsctl set Bridge', name, 'stp_enable=true', 'other_config:stp-priority=%d' % priority)

	#FOR CONNECTIVITY TESTS ONLY
	#switch_obj.cmd('ovs-vsctl add-port '+name+'



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

#Get the bbr switches,
#b1 = net.get('b1')
# Set the switch to use OF v 1.3
#b1.cmd('ovs-vsctl set Bridge b1 protocols=OpenFlow13')
# Enable STP on the switch
#b1.cmd('ovs-vsctl set Bridge b1 stp_enable=true')

#b2 = net.get('b2')
#b2.cmd('ovs-vsctl set Bridge b2 protocols=OpenFlow13')
#b2.cmd('ovs-vsctl set Bridge b2 stp_enable=true')


# Do the same things described above for
# switches s1-s10

#s1 = net.get('s1')
#s1.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
#s1.cmd('ovs-vsctl set Bridge s1 stp_enable=true')
#s2 = net.get('s2')
#s2.cmd('ovs-vsctl set Bridge s2 protocols=OpenFlow13')
#s2.cmd('ovs-vsctl set Bridge s2 stp_enable=true')
#s3 = net.get('s3')
#s3.cmd('ovs-vsctl set Bridge s3 protocols=OpenFlow13')
#s3.cmd('ovs-vsctl set Bridge s3 stp_enable=true')
#s4 = net.get('s4')
#s4.cmd('ovs-vsctl set Bridge s4 protocols=OpenFlow13')
#s4.cmd('ovs-vsctl set Bridge s4 stp_enable=true')
#s5 = net.get('s5')
#s5.cmd('ovs-vsctl set Bridge s5 protocols=OpenFlow13')
#s5.cmd('ovs-vsctl set Bridge s5 stp_enable=true')
#s6 = net.get('s6')
#s6.cmd('ovs-vsctl set Bridge s6 protocols=OpenFlow13')
#s6.cmd('ovs-vsctl set Bridge s6 stp_enable=true')
#s7 = net.get('s7')
#s7.cmd('ovs-vsctl set Bridge s7 protocols=OpenFlow13')
#s7.cmd('ovs-vsctl set Bridge s7 stp_enable=true')
#s8 = net.get('s8')
#s8.cmd('ovs-vsctl set Bridge s8 protocols=OpenFlow13')
#s8.cmd('ovs-vsctl set Bridge s8 stp_enable=true')
#s9 = net.get('s9')
#s9.cmd('ovs-vsctl set Bridge s9 protocols=OpenFlow13')
#s9.cmd('ovs-vsctl set Bridge s9 stp_enable=true')
#s10 = net.get('s10')
#s10.cmd('ovs-vsctl set Bridge s10 protocols=OpenFlow13')
#s10.cmd('ovs-vsctl set Bridge s10 stp_enable=true')


# Do the same things described above for
# switches o1a-o7b
#o1a = net.get('o1a')
#o1b = net.get('o1b')
#o2a = net.get('o2a')
#o2b = net.get('o2b')
#o3a = net.get('o3a')
#o3b = net.get('o3b')
#o4a = net.get('o4a')
#o4b = net.get('o4b')
#o5a = net.get('o5a')
#o5b = net.get('o5b')
#o6a = net.get('o6a')
#o6b = net.get('o6b')
#o7a = net.get('o7a')
#o7b = net.get('o7b')


#list_leaf_switch = [o1a, o1b, o2a, o2b, o3a, o3b, o4a, o4b, o5a, o5b, o6a, o6b, o7a, o7b]

#a = 1
#count = 1
#for x in list_leaf_switch:
#	if(a%2 == 0):

#		x.cmd('ovs-vsctl set Bridge o' + `count` + 'b protocols=OpenFlow13')
#		x.cmd('ovs-vsctl set Bridge o' + `count` + 'b stp_enable=true')
# 		print('ovs-vsctl set Bridge o' + `count` + 'b protocols=OpenFlow13')
# 		count = count + 1
#
# 	else:
# 		print('ovs-vsctl set Bridge o' + `count` + 'a protocols=OpenFlow13')
# 		x.cmd('ovs-vsctl set Bridge o' + `count` + 'a protocols=OpenFlow13')
# 		x.cmd('ovs-vsctl set Bridge o' + `count` + 'a stp_enable=true')

#	a = a + 1

# Set a route to all subnets for our hots

#h1 = net.get('h1')
#h2 = net.get('h2')
#h3 = net.get('h3')
#h4 = net.get('h4')



#c = 1
#list_hosts_h = [h1, h2, h3, h4]
#for y in list_hosts_h:
#	y.cmd('route add -net 10.0.0.0 netmask 255.0.0.0 dev h' + `c` + '-eth0')
#	c = c + 1

#f1 = net.get('f1')
#f2 = net.get('f2')
#f3 = net.get('f3')
#f4 = net.get('f4')

#c = 1
#list_hosts_f = [f1, f2, f3, f4]
#for y in list_hosts_f:
#	y.cmd('route add -net 10.0.0.0 netmask 255.0.0.0 dev f' + `c` + '-eth0')
#	c = c + 1


#u1a = net.get('u1a')
#u2a = net.get('u2a')
#u3a = net.get('u3a')
#u4a = net.get('u4a')
#u5a = net.get('u5a')
#u6a = net.get('u6a')
#u7a = net.get('u7a')
#u8a = net.get('u8a')
#u9a = net.get('u9a')
#u10a = net.get('u10a')

#list_hosts_ua = [u1a, u2a, u3a, u4a, u5a, u6a, u7a, u8a, u9a]

#c = 1
#for y in list_hosts_ua:
#	y.cmd('route add -net 10.0.0.0 netmask 255.0.0.0 dev u' + `c` + 'a-eth0')
#	c = c + 1

#u1b = net.get('u1b')
#u2b = net.get('u2b')
#u3b = net.get('u3b')
#u4b = net.get('u4b')
#u5b = net.get('u5b')
#u6b = net.get('u6b')
#u7b = net.get('u7b')
#u8b = net.get('u8b')
#u9b = net.get('u9b')
#u10b = net.get('u10b')

#list_hosts_ub = [u1b, u2b, u3b, u4b, u5b, u6b, u7b, u8b, u9b]

#c = 1
#for y in list_hosts_ub:
#	y.cmd('route add -net 10.0.0.0 netmask 255.0.0.0 dev u' + `c` + 'b-eth0')
#	c = c + 1



CLI(net)

net.stop()
