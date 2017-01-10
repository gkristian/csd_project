
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSBridge
from mininet.link import TCLink
import sys
import os
from mininet.term import makeTerm
#print current directory
from mininet.topo import Topo

def int2dpid( dpid ):
        "Create and set the dpid for a switch, takes an int and outpus a hexadecimal dpid"
        try:
                dpid = hex( dpid )[ 2: ]
                dpid = '0' * ( 16 - len( dpid ) ) + dpid
                return dpid
        except IndexError:
                raise Exception( 'Unable to derive default dpid' )

class StanfordTopo( Topo ):
        def __init__( self ):
                Topo.__init__( self )

                # Add backbone switches to the topology
                b1 = self.addSwitch('b1',dpid=int2dpid(1))
                b2 = self.addSwitch('b2',dpid=int2dpid(2))

                # Add spine switches to the topology
                s1 = self.addSwitch('s1', dpid=int2dpid(11))
                s2 = self.addSwitch('s2', dpid=int2dpid(12))
                s3 = self.addSwitch('s3', dpid=int2dpid(13))
                s4 = self.addSwitch('s4', dpid=int2dpid(14))
                s5 = self.addSwitch('s5', dpid=int2dpid(15))
                s6 = self.addSwitch('s6', dpid=int2dpid(16))
                s7 = self.addSwitch('s7', dpid=int2dpid(17))
                s8 = self.addSwitch('s8', dpid=int2dpid(18))
                s9 = self.addSwitch('s9', dpid=int2dpid(19))
                s10 = self.addSwitch('s10', dpid=int2dpid(20))

                # Add leaf switches to the topology
                o1 = self.addSwitch('o1', dpid=int2dpid(21))
                p1 = self.addSwitch('p1', dpid=int2dpid(22))
                o2 = self.addSwitch('o2', dpid=int2dpid(23))
                p2 = self.addSwitch('p2', dpid=int2dpid(24))
                o3 = self.addSwitch('o3', dpid=int2dpid(25))
                p3 = self.addSwitch('p3', dpid=int2dpid(26))
                o4 = self.addSwitch('o4', dpid=int2dpid(27))
                p4 = self.addSwitch('p4', dpid=int2dpid(28))
                o5 = self.addSwitch('o5', dpid=int2dpid(29))
                p5 = self.addSwitch('p5', dpid=int2dpid(30))
                o6 = self.addSwitch('o6', dpid=int2dpid(31))
                p6 = self.addSwitch('p6', dpid=int2dpid(32))
                o7 = self.addSwitch('o7', dpid=int2dpid(33))
                p7 = self.addSwitch('p7', dpid=int2dpid(34))

                # Add client zone a to the topology
                u1 = self.addHost('u1', ip='10.0.10.1/8', mac='00:00:00:00:01:01')
                u2 = self.addHost('u2', ip='10.0.10.2/8', mac='00:00:00:00:01:02')
                u3 = self.addHost('u3', ip='10.0.10.3/8', mac='00:00:00:00:01:03')
                u4 = self.addHost('u4', ip='10.0.10.4/8', mac='00:00:00:00:01:04')
                u5 = self.addHost('u5', ip='10.0.10.5/8', mac='00:00:00:00:01:05')
                u6 = self.addHost('u6', ip='10.0.10.6/8', mac='00:00:00:00:01:06')
                u7 = self.addHost('u7', ip='10.0.10.7/8', mac='00:00:00:00:01:07')
                u8 = self.addHost('u8', ip='10.0.10.8/8', mac='00:00:00:00:01:08')
                u9 = self.addHost('u9', ip='10.0.10.9/8', mac='00:00:00:00:01:09')
                u10 = self.addHost('u10', ip='10.0.10.10/8', mac='00:00:00:00:01:10')

                # Add client zone b to the topology
                v1 = self.addHost('v1', ip='10.0.30.1/8', mac='00:00:00:00:03:01')
                v2 = self.addHost('v2', ip='10.0.30.2/8', mac='00:00:00:00:03:02')
                v3 = self.addHost('v3', ip='10.0.30.3/8', mac='00:00:00:00:03:03')
                v4 = self.addHost('v4', ip='10.0.30.4/8', mac='00:00:00:00:03:04')
                v5 = self.addHost('v5', ip='10.0.30.5/8', mac='00:00:00:00:03:05')
                v6 = self.addHost('v6', ip='10.0.30.6/8', mac='00:00:00:00:03:06')
                v7 = self.addHost('v7', ip='10.0.30.7/8', mac='00:00:00:00:03:07')
                v8 = self.addHost('v8', ip='10.0.30.8/8', mac='00:00:00:00:03:08')
                v9 = self.addHost('v9', ip='10.0.30.9/8', mac='00:00:00:00:03:09')
                v10 = self.addHost('v10', ip='10.0.30.10/8', mac='00:00:00:00:03:10')

                # Add server zone h to the topology
                h1 = self.addHost('h1', ip='10.0.20.1/8', mac='00:00:00:00:02:01')
                h2 = self.addHost('h2', ip='10.0.20.2/8', mac='00:00:00:00:02:02')
                h3 = self.addHost('h3', ip='10.0.20.3/8', mac='00:00:00:00:02:03')
                h4 = self.addHost('h4', ip='10.0.20.4/8', mac='00:00:00:00:02:04')

                # Add server zone h to the topology
                f1 = self.addHost('f1', ip='10.0.40.1/8', mac='00:00:00:00:04:01')
                f2 = self.addHost('f2', ip='10.0.40.2/8', mac='00:00:00:00:04:02')
                f3 = self.addHost('f3', ip='10.0.40.3/8', mac='00:00:00:00:04:03')
                f4 = self.addHost('f4', ip='10.0.40.4/8', mac='00:00:00:00:04:04')

                #lopt = dict(bw=10)
                # Add link b1, b2, 1 Gbps
                self.addLink(b1, b2, bw=10)

                # Add links from backbone to spine switches, 1 Gbps
                self.addLink(b1, s1, bw=10)
                self.addLink(b1, s2, bw=10)
                self.addLink(b1, s3, bw=10)
                self.addLink(b1, s4, bw=10)
                self.addLink(b1, s5, bw=10)
                self.addLink(b2, s6, bw=10)
                self.addLink(b2, s7, bw=10)
                self.addLink(b2, s8, bw=10)
                self.addLink(b2, s9, bw=10)
                self.addLink(b2, s10, bw=10)

                # Add links from backbone switches to leaf switch o4a, 1 Gbps
                self.addLink(b1, o4, bw=10)
                self.addLink(b2, o4, bw=10)

                # link togheter spine and leaf switches
                self.addLink(s1, p1, bw=10)
                self.addLink(s1, p5, bw=10)
                self.addLink(s2, o3, bw=10)
                self.addLink(s2, p4, bw=10)
                self.addLink(s2, o6, bw=10)
                self.addLink(s3, p3, bw=10)
                self.addLink(s3, p6, bw=10)
                self.addLink(s4, o1, bw=10)
                self.addLink(s4, o2, bw=10)
                self.addLink(s4, o5, bw=10)
                self.addLink(s4, o7, bw=10)
                self.addLink(s5, p2, bw=10)
                self.addLink(s5, p7, bw=10)
                self.addLink(s6, p1, bw=10)
                self.addLink(s6, p5, bw=10)
                self.addLink(s7, o3, bw=10)
                self.addLink(s7, p4, bw=10)
                self.addLink(s7, o6, bw=10)
                self.addLink(s8, p3, bw=10)
                self.addLink(s8, p6, bw=10)
                self.addLink(s9, o1, bw=10)
                self.addLink(s9, o2, bw=10)
                self.addLink(s9, o5, bw=10)
                self.addLink(s9, o7, bw=10)
                self.addLink(s10, p7, bw=10)
                self.addLink(s10, p2, bw=10)

                # link togheter the pair leaf switches
                self.addLink(o1, p1, bw=10)
                self.addLink(o2, p2, bw=10)
                self.addLink(o3, p3, bw=10)
                self.addLink(o4, p4, bw=10)
                self.addLink(o5, p5, bw=10)
                self.addLink(o6, p6, bw=10)
                self.addLink(o7, p7, bw=10)

                # Link client zone a and server zone h to leaf switches
                self.addLink(o1, u1)
                self.addLink(o1, u2)
                self.addLink(o1, u3)
                self.addLink(o1, u4)
                self.addLink(o1, u5)
                self.addLink(o3, u6)
                self.addLink(o3, u7)
                self.addLink(o3, u8)
                self.addLink(o3, u9)
                self.addLink(o3, u10)
                self.addLink(o2, h1)
                self.addLink(o2, h2)
                self.addLink(o2, h3)
                self.addLink(o2, h4)

                # Link client zone b and server zone f to leaf switches
                self.addLink(o5, v1)
                self.addLink(o5, v2)
                self.addLink(o5, v3)
                self.addLink(o5, v4)
                self.addLink(o5, v5)
                self.addLink(p7, v6)
                self.addLink(p7, v7)
                self.addLink(p7, v8)
                self.addLink(p7, v9)
                self.addLink(p7, v10)
                self.addLink(o6, f1)
                self.addLink(o6, f2)
                self.addLink(o6, f3)
                self.addLink(o6, f4)

topos = { 'stanford': ( lambda: StanfordTopo() ) }
