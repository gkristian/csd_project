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
			     u4
			     |
			    -S7--   S5 -- u3
			   /     \ / \
		   S1 --- S2 --- S3  S6
		  /		   \ /
		 u1		   S4 -- u2

		"""
		s1 = self.addSwitch('s1', dpid=int2dpid(1))
		s2 = self.addSwitch('s2', dpid=int2dpid(2))
		s3 = self.addSwitch('s3', dpid=int2dpid(3))
		#s4 = self.addSwitch('s4', dpid=int2dpid(4))
		#s5 = self.addSwitch('s5', dpid=int2dpid(5))
		#s6 = self.addSwitch('s6', dpid=int2dpid(6))
		#s7 = self.addSwitch('s7', dpid=int2dpid(7))

		# Add client zone 1
		u1 = self.addHost('u1', ip='10.1.0.1/8', mac='00:00:00:00:01:01')
		u2 = self.addHost('u2', ip='10.2.0.1/8', mac='00:00:00:00:02:01')
		u3 = self.addHost('u3', ip='10.3.0.1/8', mac='00:00:00:00:03:01')
		#u4 = self.addHost('u4', ip='10.7.0.1/8', mac='00:00:00:00:07:01')




        #Link Capacity definitions:
        #lopt1=dict(bw=10000)
        #lopt2=dict(bw=1000)
        #lopt3=dict(bw=100)

		# connect backbone and spine switches, 1 Gbps
		try:
			#self.addLink(b1, s1)
			#self.addLink(b1, s2)

			self.addLink(s1, s2, bw=10)
			self.addLink(s2, s3, bw=20)
			self.addLink(s1, s3, bw=30)
			#self.addLink(s3, s4)
			#self.addLink(s3, s5)
			#self.addLink(s4, s6)
			#self.addLink(s5, s6)
			#self.addLink(s2, s7)
			#self.addLink(s3, s7)
			self.addLink(s1, u1, bw=5)
			self.addLink(s2, u2, bw=5)
			self.addLink(s3, u3, bw=5)
			#self.addLink(s4, u2)
			#self.addLink(s5, u3)
			#self.addLink(s7, s4)
			#self.addLink(s7, s5)			
			#self.addLink(s7, u4)
		except:
			print("ERROR")



# make topoology name availiable to command line mininet
topos = { 'simpletopo': ( lambda: SimpleTopo() ) }
