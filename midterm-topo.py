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
		# Add spine switches
		s1 = self.addSwitch('s1', dpid=int2dpid(11))
		s2 = self.addSwitch('s2', dpid=int2dpid(12))
		s3 = self.addSwitch('s3', dpid=int2dpid(13))
		# Add leaf switches
		l1 = self.addSwitch('l1', dpid=int2dpid(21))
		l2 = self.addSwitch('l2', dpid=int2dpid(22))
		l3 = self.addSwitch('l3', dpid=int2dpid(23))
		l4 = self.addSwitch('l4', dpid=int2dpid(24))
		# Add client zone 1
		u1 = self.addHost('u1', ip='10.1.0.1/8', mac='00:00:00:00:01:01')
		u2 = self.addHost('u2', ip='10.1.0.2/8', mac='00:00:00:00:01:02')
		# Add server zone h
		h1 = self.addHost('h1', ip='10.2.0.1/8', mac='00:00:00:00:02:01')
		h2 = self.addHost('h2', ip='10.2.0.2/8', mac='00:00:00:00:02:02')
        #Link Capacity definitions:
        #lopt1=dict(bw=10000)
        #lopt2=dict(bw=1000)
        #lopt3=dict(bw=100)
		# connect backbone and spine switches, 1 Gbps
		self.addLink(b1, s1, bw=1000)
		self.addLink(b1, s2, bw=1000)
		self.addLink(b1, s3, bw=1000)

		# interconncet spine switches, 100 Mbps
		self.addLink(s1, s2, bw=100)
		self.addLink(s2, s3, bw=100)

		# Connect leaf switches to spine switches, 100 Mbps
		self.addLink(s1, l1, bw=100)
		self.addLink(s1, l2, bw=100)
		self.addLink(s2, l2, bw=100)
		self.addLink(s2, l4, bw=100)
		self.addLink(s3, l3, bw=100)
		self.addLink(s3, l4, bw=100)

		# connect hosts to leaf switches, 10 mbps
		self.addLink(l1, l2, bw=10)
		self.addLink(l2, l3, bw=10)
		self.addLink(l1, u1, bw=10)
		self.addLink(l1, u2, bw=10)
		self.addLink(l3, h1, bw=10)
		self.addLink(l3, h2, bw=10)

# make topoology name availiable to command line mininet
topos = { 'topo2': ( lambda: Topology2() ) }
