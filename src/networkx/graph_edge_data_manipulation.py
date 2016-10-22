
import networkx as nx

G = nx.DiGraph()

edge_src_node_name = 1
edge_dst_node_name = 2
edge_data_dict = dict()
edge_data_dict = {'k1':'v1', 'k2':'v2'}

G.add_edge(edge_src_node_name,edge_dst_node_name,edge_data_dict)
#print G.edge(data=True) ### THIS DOESNT WORK FOR EDGE - SO NEVER USE
#instead you use
print "edge before k1 change"
print "print edge dict data", G.get_edge_data(edge_src_node_name, edge_dst_node_name)
print "another way accessing edge dict data"
print G.edge[edge_src_node_name][edge_dst_node_name]


G.add_edge(edge_src_node_name, edge_dst_node_name, k1='changedv1')
#above could also been
G.edge[edge_src_node_name][edge_dst_node_name]['k1'] = 'again_changedv1_arraystyle'

print "edge after k1 change \n", G.get_edge_data(edge_src_node_name, edge_dst_node_name)


#print "_________________________EDGE data manipulation______________________"

#each edge is a tuple (FROM_NODE_NAME, TO_NODE_NAME, EDGE_DICTIONARY)

