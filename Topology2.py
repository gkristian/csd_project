from mininet.topo import Topo
from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.node import OVSBridge
from mininet.link import TCLink
import sys
import os
from mininet.term import makeTerm

def int2dpid( dpid ):
	try:
		dpid = hex( dpid )[ 2: ]
		dpid = '0' * (16 - len( dpid ) ) + dpid
		return dpid
	except IndexError:
		raise Exception( 'Unable to derive default dpid')


class Topology2( Topo ):
	def __init__( self ):
		Topo.__init__( self )
		# Add backbone switches
		b1 = self.addSwitch('b1', dpid=int2dpid(1))
		b2 = self.addSwitch('b2', dpid=int2dpid(2))

		# Add spine switches
		s1 = self.addSwitch('s1', dpid=int2dpid(11))
		s2 = self.addSwitch('s2', dpid=int2dpid(12))
		s3 = self.addSwitch('s3', dpid=int2dpid(13))
		s4 = self.addSwitch('s4', dpid=int2dpid(14))

		# Add leaf switches
		l1 = self.addSwitch('l1', dpid=int2dpid(21))
		l2 = self.addSwitch('l2', dpid=int2dpid(22))
		l3 = self.addSwitch('l3', dpid=int2dpid(23))
		l4 = self.addSwitch('l4', dpid=int2dpid(24))
		l5 = self.addSwitch('l5', dpid=int2dpid(25))
		l6 = self.addSwitch('l6', dpid=int2dpid(26))
		l7 = self.addSwitch('l7', dpid=int2dpid(27))
		l8 = self.addSwitch('l8', dpid=int2dpid(28))

		# Add client zone 1
		u1 = self.addHost('u1', ip='10.1.0.1/8', mac='00:00:00:00:01:01')
		u2 = self.addHost('u2', ip='10.1.0.2/8', mac='00:00:00:00:01:02')
		u3 = self.addHost('u3', ip='10.1.0.3/8', mac='00:00:00:00:01:03')

		# Add server zone h
		h1 = self.addHost('h1', ip='10.2.0.1/8', mac='00:00:00:00:02:01')
		h2 = self.addHost('h2', ip='10.2.0.2/8', mac='00:00:00:00:02:02')
		h3 = self.addHost('h3', ip='10.2.0.3/8', mac='00:00:00:00:02:03')

		# Add server zone f
		f1 = self.addHost('f1', ip='10.3.0.1/8', mac='00:00:00:00:03:01')
		f2 = self.addHost('f2', ip='10.3.0.2/8', mac='00:00:00:00:03:02')
		f3 = self.addHost('f3', ip='10.3.0.3/8', mac='00:00:00:00:03:03')

		# Add client zone 2
		u4 = self.addHost('u4', ip='10.4.0.1/8', mac='00:00:00:00:04:01')
		u5 = self.addHost('u5', ip='10.4.0.2/8', mac='00:00:00:00:04:02')
		u6 = self.addHost('u6', ip='10.4.0.3/8', mac='00:00:00:00:04:03')




        #Link Capacity definitions:
        #lopt1=dict(bw=10000)
        #lopt2=dict(bw=1000)
        #lopt3=dict(bw=100)
		# connect backbone switchess, 1 Gbps
		self.addLink(b1, b2, bw=1000)

		# connect backbone and spine switches, 1 Gbps
		self.addLink(b1, s1, bw=1000)
		self.addLink(b1, s2, bw=1000)
		self.addLink(b1, s3, bw=1000)
		self.addLink(b1, s4, bw=1000)
		self.addLink(b2, s1, bw=1000)
		self.addLink(b2, s2, bw=1000)
		self.addLink(b2, s3, bw=1000)
		self.addLink(b2, s4, bw=1000)

		# interconncet spine switches, 100 Mbps
		self.addLink(s1, s2, bw=100)
		self.addLink(s2, s3, bw=100)
		self.addLink(s3, s4, bw=100)

		# Connect leaf switches to spine switches, 100 Mbps
		self.addLink(s1, l1, bw=100)
		self.addLink(s1, l2, bw=100)
		self.addLink(s1, l3, bw=100)
		self.addLink(s1, l4, bw=100)
		self.addLink(s2, l1, bw=100)
		self.addLink(s2, l2, bw=100)
		self.addLink(s2, l3, bw=100)
		self.addLink(s2, l4, bw=100)
		self.addLink(s2, l5, bw=100)
		self.addLink(s3, l4, bw=100)
		self.addLink(s3, l5, bw=100)
		self.addLink(s3, l6, bw=100)
		self.addLink(s3, l7, bw=100)
		self.addLink(s3, l8, bw=100)
		self.addLink(s4, l5, bw=100)
		self.addLink(s4, l6, bw=100)
		self.addLink(s4, l7, bw=100)
		self.addLink(s4, l8, bw=100)

		# connect hosts to leaf switches, 10 mbps
		self.addLink(l1, u1, bw=10)
		self.addLink(l1, u2, bw=10)
		self.addLink(l1, u3, bw=10)
		self.addLink(l3, h1, bw=10)
		self.addLink(l3, h3, bw=10)
		self.addLink(l3, h2, bw=10)
		self.addLink(l6, f1, bw=10)
		self.addLink(l6, f2, bw=10)
		self.addLink(l6, f3, bw=10)
		self.addLink(l8, u4, bw=10)
		self.addLink(l8, u5, bw=10)
		self.addLink(l8, u6, bw=10)

# make topoology name availiable to command line mininet
topos = { 'topo2': ( lambda: Topology2() ) }
