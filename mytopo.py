#!/usr/bin/python
from mininet.topo import Topo
from mininet.link import TCLink



class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        leftHost = self.addHost( 'h1' )
        rightHost = self.addHost( 'h2' )
        leftSwitch = self.addSwitch( 's3' )
        rightSwitch = self.addSwitch( 's4' )

        # Add links
        self.addLink( leftHost, leftSwitch,bw=10, cls=TCLink, delay='5ms', loss=10, max_queue_size=1000, use_htb=True)
        self.addLink( leftSwitch, rightSwitch, bw=10, cls=TCLink,  delay='5ms', loss=10, max_queue_size=1000, use_htb=True)
        self.addLink( rightSwitch, rightHost, bw=10, cls=TCLink, delay='5ms', loss=10, max_queue_size=1000, use_htb=True)


topos = { 'mytopo': ( lambda: MyTopo() ) }

