
branch : controller_core
This branch implements a RYU controller app that build the network topology including the host mac addresses without flooding the network.
It uses networkx library to store the network graph.

RECENT_CHANGE:

-mac_to_port now has mac addresses only of the hosts attached to the edge switches. It automatically detects from the network which switches have these hosts located and builds the table.

TODO:

-add the hosts to the graph. Study shows using a MultiGraph is much better than DiGraph but is a MultiNode graph directional? (30 mins)

-use the link.to_dict() to add out_port to each switch so that from the graph the path can be built (5 hrs)

-compute shortest path with info about switch and its out_port for which src mac 

-install the above computed path using flow mod into all the switches in the path. This shall cause the ping to work

-add weights to graphs. a weight shows the link utilization

-read weights from the database


Usage Instructions:
0. You need to install below python libraries part of the discrete math graph daraw framework:
	pip install networkx
	
 You also need to install below libraries for graph visualization to run future versions of this application.
	pip install matplotlib
	apt-get install graphviz
	apt-get install python-pygraphviz
	pip install pydot
1. cd /bin. Run ryu script first and tail its log in one window

2. In another winow. cd bin. Run mininet script. At the CLI run pingall to initiate topology discovery without flooding.

3. When done dont forget to run stop ryu script in bin folder. Ryu runs as a background process and writes to /tmp as log file.
