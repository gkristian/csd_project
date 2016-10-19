#!/usr/bin/python
import plotly.plotly as py
import plotly as pl
import plotly.graph_objs as go
from plotly.plotly import *

import numpy as np

pl.tools.set_credentials_file(username='itnewclass', api_key='z7oztw4rft')


N=100
#random_y0=np.random.randn(N)+5
random_x=np.linspace(0,10,N)
random_y0=np.random.randn(N)+5
random_y1=np.random.randn(N)
random_y2=np.random.randn(N)-5

#create traces
trace0=go.Scatter(x= random_x, y=random_y0, mode='markers', name='Switch-S1: eth0')
trace1=go.Scatter(x=random_x,y=random_y1, mode= 'lines+markers',name='Switch-S1: eth1')
trace2=go.Scatter(x=random_x, y=random_y2, mode='lines', name='Switch-S1: eth2')

#trace1=go.Scatter(x=random_x)
#data=[trace0, trace1, trace2]
data=[trace0, trace2, trace1]
py.iplot(data, filename='scatter-mode')
