#!/usr/bin/python
import MySQLdb as my
import pandas as pd
import plotly as pl
import plotly.plotly as py
from plotly.graph_objs import *

pl.tools.set_credentials_file(username='itnewclass', api_key='z7oztw4rft')
conn=my.connect(host="localhost", user="root", passwd="123456", db="nfmdb")

cur=conn.cursor()
query=("""select customer_id, flows, flow_size from nfm1""")
cur.execute(query)
data=[];
c_id=[];
flows=[];
flow_size=[];

for q in cur:
    data.append((q))

conn.close()

for q in range(len(data)):
    flows.append(data[q][0]);
    flow_size.append(data[q][1]);
    c_id.append(data[q][2]);
    text1=['Flow01','Flow02','Flow03','Flow04','Flow05','Flow06','Flow07','Flow08','Flow09','Flow10','Flow11','Flow12','Flow13','Flow14']

#data = [go.]
trace1=Scatter(x=flows, y=flow_size, text=text1, mode='markers')

layout=Layout(title='Size of FLows', xaxis=XAxis(type='log', title='GNP'), yaxis=YAxis(title= 'Flow ID'), )
data1=Data([trace1])
fig=Figure(data=data1, layout=layout)
py.plot(fig, filename='datetime-heatmap2')


print 'Done!'
