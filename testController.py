from ryu.base import app_manager
import networkx as nx







class TestController(app_manager.RyuApp):
	
	app_manager._CONTEXTS = {
		'network' : nx.DiGraph([('1-1','2-1',{'bw':10}),('2-1','1-1',{'bw':10}),('1-2','3-2',{'bw':30}),('3-2','1-2',{'bw':30}),('2-2','3-1',{'bw':20}),('3-1','2-2',{'bw':20})])
		}
	
	def __init__(self, *args, **kwargs):
		super(TestController, self).__init__(*args, **kwargs)




