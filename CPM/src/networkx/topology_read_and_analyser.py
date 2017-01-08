import networkx as nx
import pydot
import pygraphviz
from networkx.readwrite import graphml

G=nx.path_graph(4)

nx.write_graphml(G,"/tmp/test.graphml")


#int here means that treat each node name which is a dpid as int, default is a str.
V=nx.read_graphml("/tmp/test.graphml",node_type=type('int'))
print V.nodes()
    #("/tmp/test.graphml",node_type='int')

#
# graph = pydot.Dot(graph_type='digraph',nodesep=.75)
# graph.set_node_defaults(style="filled",fillcolor="grey")
# graph.set_edge_defaults(color="blue",arrowhead="vee",weight="0")
#



def test_create_simple_graph_with_node(self):
    g = pydot.Dot()
    g.set_type('digraph')
    node = pydot.Node('legend')
    node.set("shape", 'box')
    g.add_node(node)
    node.set('label', 'mine')

    self.assertEqual(g.to_string(), 'digraph G {\nlegend [shape=box, label=mine];\n}\n')

test_create_simple_graph_with_node()