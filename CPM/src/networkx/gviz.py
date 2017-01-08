import pygraphviz
import networkx
import networkx as nx
#G = nx.Graph()
G = nx.DiGraph()
G.add_node("ROOT")
for i in xrange(5):
	G.add_node("Child_%i" % i)
	G.add_node("Grandchild_%i" % i)
	G.add_node("Greatgrandchild_%i" % i)
	G.add_edge("ROOT", "Child_%i" % i)
	G.add_edge("Child_%i" % i, "Grandchild_%i" % i)
	G.add_edge("Grandchild_%i" % i, "Greatgrandchild_%i" % i)
	G.add_edge("ROOT","New")
	G.edge['ROOT']['New']['weight']=34

#A = nx.to_agraph(G)
A = nx.nx_agraph.to_agraph(G)
A.layout('dot', args='-Nfontsize=10 -Nwidth=".2" -Nheight=".2" -Nmargin=0 -Gfontsize=8')
A.draw('test_digraph.png')




