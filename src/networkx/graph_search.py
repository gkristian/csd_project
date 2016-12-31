import graph_basics as g
import logging
import networkx as nx
G = nx.DiGraph()

G.add_weighted_edges_from([(1,2,12)]) # this will add key of 'weight' with value 12 to the edge (1,2)
G.add_weighted_edges_from([(2,1,12)])


G.add_weighted_edges_from([(1,3,13)])
G.add_weighted_edges_from([(3,1,13)])

G.add_weighted_edges_from([(1,4,14)])
G.add_weighted_edges_from([(4,1,14)])

G.add_weighted_edges_from([(3,4,34)])
G.add_weighted_edges_from([(4,3,34)])

#g.show_graph_stats(G)
#g.show_graph(G)
logger = logging.getLogger(__name__)
logging.basicConfig(

    # filename='app.log',#if this filename not given then all logging goes to STDERR
    level=logging.DEBUG,#filename='check.log',
    format='%(asctime)s:%(levelname)s:%(message)s')  # <------------------ formatter - latest hot thing in town ;)

#logger = logging.getLogger("hmm" + __name__)
#logger.setLevel(logging.DEBUG)
if 2 in G:
    logger.info("2 found in graph") #printing G or G.__str__ just printed object address

if G.has_edge(1,2):
    logger.info("G has edge 1,2 which has weight = %r",G.edge[1][2])

if G.has_node(1):
    logger.info("G has node 1")

logger.info("_______when the edge or node does not exist_____________________________")

if 's' in G:
    logger.info("s foundin graph")
if 41 in G:
    logger.info("2 found in graph") #printing G or G.__str__ just printed object address

if G.has_edge(41,2):
    logger.info("G has edge 1,2 which has weight = %r",G.edge[1][2])

if G.has_node(41):
    logger.info("G has node 1")

#logger.info("G.__len__ = %r", G.__len__) #this was useless to print as we only got object address

logger.info("_______when the edge exits but its associated data object is missing the key that is searched_____________________________")

G.edge[1][2]['nfm'] = 10
G.edge[1][2]['rpm'] = 5
G.edge[1][2]['hum'] = 10

G.edge[1][2]['bw'] = 1
G.edge[1][2]['bw'] = 2
G.edge[1][2]['bw'] = 3

logger.info("G.edge[1][2] = %r",G.edge[1][2])

if 'nfm' in G.edge[1][2]:
    logger.info("nfm key foundin graph")
if 'missing_key' in G.edge[1][2]:
    logger.info("this message is impossible")
if 41 in G.edge[1][2]:
    logger.info("41 found in graph") #printing G or G.__str__ just printed object address

a='nfm'
logger.info("G[1][2][<var_with_valid_key>] = %r", G.edge[1][2][a]) # it works, python aint like C
key = 'nfm'
if key in G.edge[1][2]:
    logger.info("nfm key foundin graph")
#________________________________________________________________________________
#key3 is not intialized so it throws exception NameError : name 'key3' is not defined
try:
    if key in G.edge[1][2]:
        logger.info("nfm_key foundin graph")
except (NameError):
    logger.error("key3 is not defined")


logger.info("hmm")


## Iterating a graph over edges
#for node, data in G.nodes_iter(data=True):
for src,dst,data in G.edges_iter(data=True):
    logger.info("EDGE_ITERATOR node = %r,%r and bw value = %r", src,dst,data)
    #if (data['weight'] == 1):


# get all edges out from these nodes
# then recursively follow using a filter for a specific statement_id

# or get all edges with a specific statement id
# look for  with a node attribute of "cat"


