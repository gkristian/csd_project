#!/usr/bin/python
import plotly.plotly as py
import plotly as pl
import plotly.graph_objs as go
#from plotly.graph_objs import *
from plotly.plotly import *
import numpy as np
pl.tools.set_credentials_file(username='itnewclass', api_key='z7oztw4rft')
num=40
x=[28,29,30,40,46,47,50,65]
y=[18,29,23,32,36,37,50,55]

x1=[40,40,50,52,69,80,82,85]
y1=[28,39,40,45,56,57,60,65]

trace01=go.Scatter(x=x, y=y, name='Switch-S1')
trace02=go.Scatter(x=x1, y=y1, name='Switch-S2')

data=go.Data([trace01,trace02])
#data=go.Data([trace01])
layout=go.Layout(autosize=False, width=500, height=600, margin=go.Margin(l=50, r=50, b=100, t=100, pad=4))
fig=go.Figure(data=data, layout=layout)
plot_me=py.plot(fig)

print 'done! \n'
