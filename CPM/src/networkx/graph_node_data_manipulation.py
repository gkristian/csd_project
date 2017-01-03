import networkx as nx
G = nx.DiGraph()

dictN = dict()
dictN1= {'k1':'v1','k2':'v2'}
dictN2= {'l1':'w1','l2':'w2'}

#a node is a typle of two values, node name and its data dictionary (NODE_NAME, DICT)
#G.nodes(data=True) returns a list of such tuples
#G.nodes() returns a list with each element as the NODE_NAME

G.add_node(1,dictN1)
G.add_node(2,dictN2)
print "This is what the data stored in node (always as LIST) looks like"
print G.nodes(data=True)


## below node data gets appended and not overwritten to above node
G.add_node(1,{'k3':'v3','k4':'v4'}) ##THIS APPENDS TO THE NODE DATA <---------------

print "This is what the data stored in node (LIST) looks like"
print G.nodes(data=True)

print "total nodes we have "
print G.nodes()

print "______________Another way to store data in nodes recommended when u want to overwrite node_data instead of append_______________"

print "CLEARING THE GRAPH G"
G.clear()
print "Nodes in graph G", G.nodes(data=True)
G.add_node(1,k1='v1')
G.add_node(1,k2='v2')
G.add_node(1,k1='changev1') #THIS OVERWRITES k1 's value <----------------
print "Graph G after data add is ", G.nodes(data=True)
G.add_node(2,l1='w1')
G.add_node(2,l2='w2')
G.add_node(2,l3='w3',l4='w4') #this is also legal
#G.add_node(2,'kkkey1','vallue1') ## BUT NEVER USE THIS

print "Graph G after data add is ", G.nodes(data=True)

print "Each key is called the node attributed"

print "_____ACCESSSING NODE DATA______"
print G.node[1]['k1'] #node 1's dictionary's key1's value.

print "______________Updating NODE_DATA dictionary e.g. if all or some of the values are read from an external source"
####
#G.clear()
node1_name=1
node1_datadict = {'CCk1':'CCv1', 'CCk2':'CCv2', 'CCk3':'CCv3'}

G.add_node(1 , attr_dict=node1_datadict)
print "node 1 data after update is ", G.node[1] ### THIS AGAIN JUST APPENDED

#print "Clearing the Graph G"
#G.clear()

node1_name=1
node1_datadict = {'weight':1,'age':100}
NODE1=(node1_name,node1_datadict)
NODE2=(2,{'w2':2, 'age2':200})
ALL_NODES= [NODE1,NODE2]
G.add_nodes_from(ALL_NODES) #### THIS AGAIN JUST APPENDED, not overwriting the existing graph
print "node 1 data after update is ", G.node[1] ### THIS AGAIN JUST APPENDED
###
G.node[1]=node1_datadict  #### <-------------------------THIS OVERWRITES --------------------------<<<<<<-------------


print "node 1 data after (changed) update is ", G.node[1] ### THIS overwrites


#node2=(2    ,   {'l1':'w1', 'l2':'w2', 'l3':'w3'}   )
#ALL_NODES = [ node1 , node2]
#G.add_node_from()
