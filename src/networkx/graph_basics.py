import networkx as nx
import logging
import matplotlib.pyplot as plt


logging.basicConfig(

    #filename='app.log',#if this filename not given then all logging goes to STDERR
    level=logging.DEBUG,
    format='%(levelname)s:%(asctime)s:%(message)s') #<------------------ formatter - latest hot thing in town ;)


LOG = logging.getLogger( __name__ )
#LOG.setLevel(logging.DEBUG)


def show_graph( G = nx.DiGraph() ):
    #nx.draw(G, with_labels=True)
    ###pos = nx.get_node_attributes(G, 'pos')
    #pos = nx.spectral_layout(G)
    pos = nx.random_layout(G)
    ###pos = nx.circular_layout(G)
    #pos = nx.shell_layout(G)
    #pos = nx.spring_layout(G)
    nx.draw(G,pos,with_labels=True)
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)


    #nx.draw_networkx_edge_labels(G,pos=nx.spectral_layout(G), nodecolor='r',edge_color='b',edge_labels=labels)
    #
    #nx.draw_networkx_edge_labels(G, pos=(2,3), nodecolor='r', edge_color='b', edge_labels=labels)


    #nx.draw(G, with_labels=True)
    plt.savefig("graph_test.png")
    plt.show()

def show_graph_stats(G = nx.DiGraph() ):
    LOG.debug("number_of_nodes %r", G.number_of_nodes())
    LOG.debug("number_of_edges %r", G.number_of_edges())
    LOG.debug("number_of_nodes %r", G.nodes())
    LOG.debug("number_of_edges %r", G.edges())
    LOG.debug("degree of graph %r", G.degree())

#G=nx.DiGraph() #here if we add an edge (2,3) it will overwrite an existing edge

#net=nx.MultiDiGraph() #here it wont overwrite rather add another edge so one must check if the edge exists and then add
net=nx.DiGraph() # a port cannot be connected to more than one port directly so DiGraph is fine.
link_info={'srcport':5,'dstport':10}
switch='1'
srcport='1'
wt=50
#net.add_edge(switch + '-' + srcport, '4-3',weight=wt,object=link_info)


#######################  updating weights of a graph #########################
net.add_weighted_edges_from([(2,3,23)])
# just to check if repeat edge add with same data affects the graph in anyway.
# Found out that data type of edge matters e.g.('1','2') is different from (1,2).
# Must convert node names to same format, also noted some values in link_states are unicode u'...', so convert them to ascii string and then store if necessary.
for i in xrange(25):
    net.add_edge(1,2,weight=21,object=link_info)

show_graph_stats(net) #print stats about graph
show_graph(net) #this is a blocking operation, any line after it does not get executed









#if __name__ == '__main__':
