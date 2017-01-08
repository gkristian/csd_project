import networkx as nx
G=nx.read_graphml("./CPM_built_topology.graphml", node_type=type('int'))

print G.nodes()

for s,d,data in G.edges_iter(data=True):
    print s
    print d
    print data

A = nx.nx_agraph.to_agraph(G)
A.layout('dot', args='-Nfontsize=10 -Nwidth=".2" -Nheight=".2" -Nmargin=0 -Gfontsize=8')
A.draw('CPM_built_topplogy_dot_graphviz.png')








