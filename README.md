# monitoring_SDN 
branch : controller_core
This branch implements a RYU controller app that build the network topology including the host mac addresses without flooding the network.
It uses networkx library to store the network graph.

RECENT_CHANGE:
-mac_to_port now has mac addresses only of the hosts attached to the edge switches. It automatically detects from the network which switches have these hosts located and builds the table.

TODO:
-add the hosts to the graph
-use the link.to_dict() to add out_port to each switch so that from the graph the path can be built

-compute shortest path with info about switch and its out_port for which src mac 

-install the above computed path using flow mod into all the switches in the path. This shall cause the ping to work

-add weights to graphs. a weight shows the link utilization

-read weights from the database
