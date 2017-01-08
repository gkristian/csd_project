import networkx as nx
import matplotlib.pyplot as plt

class GrapTest():
    def __init__(self):
        self.net = nx.read_graphml("./CPM_built_topology.graphml", node_type=type('int'))

    def export_to_png(self):
        A = nx.nx_agraph.to_agraph(G)
        A.layout('dot', args='-Nfontsize=10 -Nwidth=".2" -Nheight=".2" -Nmargin=0 -Gfontsize=8')
        A.draw('CPM_built_topplogy_dot_graphviz.png')


    def show_graph(self,net):
        # nx.draw(self.net, with_labels=True)

        ###
        # pos = nx.random_layout(self.net)
        ###pos = nx.circular_layout(G)
        # pos = nx.shell_layout(G)
        pos = nx.spring_layout(self.net)
        # pos = nx.graphviz_layout(self.net,prog='dot')
        nx.draw(self.net, pos, with_labels=True, hold=False)
        # Below is a do it later when have time : plot one topology graph with lot of info
        # label_src_dst_allinone = nx.get_edge_attributes(self.net, 'src_dst')
        # nx.draw_networkx_edge_labels(self.net, pos, edge_labels=label_src_dst_allinone)
        # plt.savefig("network_with_src_dst_allinone.png")
        # print in_port and out_port as well
        label_src = nx.get_edge_attributes(self.net, 'src_port')
        nx.draw_networkx_edge_labels(self.net, pos, edge_labels=label_src)
        filename_src = './images/CPM_network_with_src_port.png'
        plt.savefig(filename_src)
        label_dst = nx.get_edge_attributes(self.net, 'dst_port')
        nx.draw_networkx_edge_labels(self.net, pos, edge_labels=label_dst)
        filename_dst = './images/CPM_network_with_dst_port.png'

        # nx.draw_graphviz(self.net)
        # nx.draw_circular(self.net, with_labels=True)

        # nx.draw_random(self.net, with_labels=True)
        # doesnt worknx.graphviz(self.net,prog='dot',with_labels=True)
        # A=nx.to_agraph(self.net)
        # A.layout()
        # A.draw('test.png')

        # labels = nx.get_edge_attributes(self.net, 'weight')
        # nx.draw_networkx_edge_labels(self.net, pos, edge_labels=labels) #this will draw weights as well
        ###

        plt.show() #Do not uncomment this in a realtime application. This will invoke a standalone application to view the graph.

        plt.savefig(filename_dst)
        plt.clf()  # this cleans the palette for the next time, otherwise it will keep on drawing the same image.


    def main(self):
        print self.net.nodes()

        for s,d,data in self.net.edges_iter(data=True):
            print s
            print d
            print data
            self.drop_prompt()
            #self.show_graph(self.net)

    def drop_debugger(self):
        import pdb
        pdb.set_trace()

    def drop_prompt(self):
        import code
        #code.interact(local=locals())
        code.interact(local=dict(globals(), **locals()))
        #below works for IPython
        #from IPython import embed
        #embed()


run = GrapTest()
run.main()






