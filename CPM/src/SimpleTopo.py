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



class SimpleTopo( Topo ):
	def __init__( self ):
		Topo.__init__( self )
		# Add backbone switches
		#b1 = self.addSwitch('b1', dpid=int2dpid(1))
		"""
				   S5 -- u3
				   / \
		   S1 --- S2 --- S3  S6
		  /		   \ /
		 u1		   S4 -- u2

		"""
		s1 = self.addSwitch('s1', dpid=int2dpid(1))
		s2 = self.addSwitch('s2', dpid=int2dpid(2))
		s3 = self.addSwitch('s3', dpid=int2dpid(3))
		s4 = self.addSwitch('s4', dpid=int2dpid(4))
		s5 = self.addSwitch('s5', dpid=int2dpid(5))
		s6 = self.addSwitch('s6', dpid=int2dpid(6))

		# Add client zone 1
		u1 = self.addHost('u1', ip='10.1.0.1/8', mac='00:00:00:00:01:01')
		u2 = self.addHost('u2', ip='10.4.0.1/8', mac='00:00:00:00:04:01')
		u3 = self.addHost('u3', ip='10.5.0.1/8', mac='00:00:00:00:05:01')




        #Link Capacity definitions:
        #lopt1=dict(bw=10000)
        #lopt2=dict(bw=1000)
        #lopt3=dict(bw=100)

		# connect backbone and spine switches, 1 Gbps
		try:
			#self.addLink(b1, s1)
			#self.addLink(b1, s2)

			self.addLink(s1, s2)
			self.addLink(s2, s3)
			self.addLink(s3, s4)
			self.addLink(s3, s5)
			self.addLink(s4, s6)
			self.addLink(s5, s6)
			self.addLink(s1, u1)
			self.addLink(s4, u2)
			self.addLink(s5, u3)
		except:
			print("ERROR")



# make topoology name availiable to command line mininet
topos = { 'simpletopo': ( lambda: SimpleTopo() ) }
