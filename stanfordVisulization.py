from Tkinter import *
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
from time import sleep
import numpy as np
import math
import copy

import dictionary


"""
Graphical class that creates nodes and links
It contains color managament and update functions
for handling all visulization of utilization
"""
class UI(Frame):

    #Constructor
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.parent = parent
        self.switchPic = Image.open("switch2.jpg")    #open switch image file
        self.clientPic = Image.open("client.jpg")   #open client image file
        self.serverPic = Image.open("server.jpg")   #open server image file
        self.switchColormap = Image.open("colormap1.jpg")
        self.linkColormap = Image.open("colormap2.jpg")
        self.switchColormapPhoto = None
        self.linkColormapPhoto = None
        self.switchPhotos = {}                      #dictionary of switch photo objects
        self.clientPhotos = {}                      #dictionary of client photo objects
        self.serverPhotos = {}                      #dictionary of server photo objects
        self.canvasImages = {}                      #dictionary of canvas image objects
        self.pictures = {}                          #dictionary of image file objects

        self.DataDictionary = dictionary.Dictionary()
        self.load_map = self.DataDictionary.load_map
        self.switchMap = self.DataDictionary.switchMap
        self.linkMap = self.DataDictionary.linkMap
        self.totalLinks = self.DataDictionary.totalLinks
        self.clientCoordinates = self.DataDictionary.clientCoordinates
        self.totalClients = self.DataDictionary.totalClients
        self.serverCoordinates = self.DataDictionary.serverCoordinates
        self.totalServers = self.DataDictionary.totalServers
        self.linkSwitchMap = self.DataDictionary.linkSwitchMap
        self.currentLoads = {}                      #dictionary of switches' current rgb values

        

        
        self.switches = {}                      #dictionary of switches and index
        self.links = {}                         #dictionary of links and index
        self.linksReverse = {}
        self.initLoad()                         #initate pictures' rgb value to 'no utilization'"
        self.initUI()                           #initate all graphical components
        self.resetLinks()                       #set init colors of links
        self.parent.geometry("1850x1000+0+0")   #set window size


    def initLoad(self):
        width, height = self.switchPic.size
        load = self.load_map[0]
        for x in range(width):
            for y in range(height):
                r,g,b = self.switchPic.getpixel( (x,y) )
                if r < 20 and g > 100 and g < 200 and b > 200 and b < 255: 
                    self.switchPic.putpixel( (x,y), load)
        for i in range(26):
            self.currentLoads[i] = load
            self.pictures[i] = copy.copy(self.switchPic)
        

    def addCurveLine(self, index, reverseIndex):
        if reverseIndex == 1:
            if index == 38:
                x_increment = 6
                x_factor = 0.04
                y_amplitude = 430
                center = 503
                xy1 = []
                for x in range(120,170):
                   # x coordinates
                   xy1.append((x * x_increment)-170)
                   # y coordinates
                   xy1.append(int(math.sin(x * x_factor) * y_amplitude) + center)
                return xy1
            if index == 39:
                x_increment = 9
                x_factor = 0.04
                y_amplitude = 430
                center = 506
                xy1 = []
                for x in range(224,274):
                    # x coordinates
                    xy1.append((x * x_increment)-1160)
                    # y coordinates
                    xy1.append(int(math.sin(x * x_factor) * y_amplitude) + center)
                return xy1
        elif reverseIndex == 2:
            if index == 38:
                x_increment = 6
                x_factor = 0.04
                y_amplitude = 430
                center = 503
                xy1 = []
                for x in range(120, 170):
                   xy1.append((x * x_increment)-180)
                   xy1.append(int(math.sin(x * x_factor) * y_amplitude) + center)
                return xy1
            if index == 39:
                x_increment = 9
                x_factor = 0.04
                y_amplitude = 430
                center = 506
                xy1 = []
                for x in range(224,274):
                    xy1.append((x*x_increment)-1150)
                    xy1.append(int(math.sin(x * x_factor) * y_amplitude) + center)
                return xy1
    def initUI(self):
        self.parent.title("Shapes")        
        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self)

        #add switches to GUI
        for i in range(26):
            xy = self.getSwitchXY(i+1)
            x = xy[0]
            y = xy[1]
            photo = ImageTk.PhotoImage(self.switchPic)
            self.switchPhotos[i] = photo
            switchImage = self.canvas.create_image(x,y,image=self.switchPhotos[i])
            self.canvasImages[i] = switchImage

        #add clients to GUI
        for i in range(self.totalClients):
            xy = self.getClientXY(i+1)
            x = xy[0]
            y = xy[1]
            photo = ImageTk.PhotoImage(self.clientPic)
            self.clientPhotos[i] = photo
            self.canvas.create_image(x,y,image=self.clientPhotos[i])

        #add servers to GUI
        for i in range(self.totalServers):
            xy = self.getServerXY(i+1)
            x = xy[0]
            y = xy[1]
            photo = ImageTk.PhotoImage(self.serverPic)
            self.serverPhotos[i] = photo
            self.canvas.create_image(x,y,image=self.serverPhotos[i])

        #add links to GUI
        for i in range(37):
            link = self.getLinkXY(i+1)
            startX = link[0]
            startY = link[1]
            endX = link[2]
            endY = link[3]
            print (i+1), link
            linkID = self.canvas.create_line(startX, startY, endX, endY, width=1)
            linkIDReverse = None
            if i+1==37:
               linkIDReverse = self.canvas.create_line(startX, startY+8, endX, endY+8, width=1)
            else:
               linkIDReverse = self.canvas.create_line(startX+10, startY, endX+10, endY, width=1)
            print linkID
            self.links[i] = linkID
            self.linksReverse[i] = linkIDReverse
        b1_curve = self.canvas.create_line(self.addCurveLine(38, 1), width=1)
        self.links[37] = b1_curve
        b1_curve_reverse = self.canvas.create_line(self.addCurveLine(38, 2), width=1)
        self.linksReverse[37] = b1_curve_reverse
        b2_curve = self.canvas.create_line(self.addCurveLine(39, 1), width=1)
        self.links[38] = b2_curve
        b2_curve_reverse = self.canvas.create_line(self.addCurveLine(39, 2), width=1)
        self.linksReverse[38] = b2_curve_reverse
        for i in range(39,self.totalLinks):
            link = self.getLinkXY(i+1)
            startX = link[0]
            startY = link[1]
            endX = link[2]
            endY = link[3]
            linkID = self.canvas.create_line(startX, startY, endX, endY, width=1)
	    linkIDReverse = None
            if i+1 >= 40 and i+1 < 47:
                linkIDReverse = self.canvas.create_line(startX, startY+8, endX, endY+8, width=1)
            else:
                linkIDReverse = self.canvas.create_line(startX+10, startY, endX+10, endY, width=1)
            self.links[i] = linkID
            self.linksReverse[i] = linkIDReverse


        #text and colorcharts
        self.canvas.create_text(1550,10,anchor='nw',text="Colormap", fill='white', font=("Times",20))
        self.canvas.create_text(1400,48,anchor='nw',text=" Links utilization: ", fill='white',font=("Times", 14))
        self.canvas.create_text(1400,80,anchor='nw',text="Switch utilization: ",fill='white',font=("Times", 14))
        self.switchColormapPhoto = ImageTk.PhotoImage(self.switchColormap)
        self.canvas.create_image(1680,90,image=self.switchColormapPhoto)
        self.linkColormapPhoto = ImageTk.PhotoImage(self.linkColormap)
        self.canvas.create_image(1680,55,image=self.linkColormapPhoto)
        
        self.canvas.config(background='black')        
        self.canvas.pack(fill=BOTH, expand=1)

    #Crop the colormap to defined as parameters
    def truncate_colormap(self, cmap, minval=0.0, maxval=1.0, n=100):
        new_cmap = colors.LinearSegmentedColormap.from_list(
            'trunc({n},{a:.2f},{b:.2f})'.format(n="RdYlGn", a=minval, b=maxval),
            cmap(np.linspace(minval, maxval, n)))
        return new_cmap            

    def resetLinks(self):
        ryg = plt.get_cmap('YlOrRd')
        ryg_cut = self.truncate_colormap(ryg, 0, 0.75)
        cNorm = colors.Normalize(vmin=0, vmax=1)
        self.scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=ryg_cut)
        rgba0 = self.scalarMap.to_rgba(0)
        l = [250*n for n in rgba0]
        mycolor = '#%02x%02x%02x' % (l[0],l[1],l[2])
        for i in range(self.totalLinks):
            self.canvas.itemconfig(self.links[i], fill=mycolor)
            self.canvas.itemconfig(self.linksReverse[i], fill=mycolor)

    def getSwitchXY(self, dpid):
        return self.switchMap[dpid]

    def getClientXY(self, dpid):
        return self.clientCoordinates[dpid]

    def getServerXY(self, dpid):
        return self.serverCoordinates[dpid]

    def getLinkXY(self, nr):
        return self.linkMap[nr]

    def setLinkUtilization(self, linkID, utilization):
        utilization = float(utilization)/float(100)
        if utilization >= 0 and utilization <= 1:
            #print "UTILIZATION SET ON: ", self.links[linkID]
            rgba0 = self.scalarMap.to_rgba(utilization)
            l = [250*n for n in rgba0]
            mycolor = '#%02x%02x%02x' % (l[0],l[1],l[2])
            self.canvas.itemconfig(self.links[linkID], fill=mycolor)
    """
    def setLinkUtilization(self, from_dpid, to_dpid, utilization):
        if utilization >= 0 and utilization <= 1:
            rgba0 = self.scalarMap.to_rgba(utilization)
            l = [250*n for n in rgba0]
            mycolor = '#%02x%02x%02x' % (l[0],l[1],l[2])
            linkString = str(from_dpid)+'-'+str(to_dpid)
            linkID = self.linkSwitchMap[linkString]-1
            self.canvas.itemconfig(self.links[linkID], fill=mycolor)
    """
    def setRPMUtilization(self, switchID, latency):
        latency = latency/float(10)
        print "RPM", switchID, latency
        load = self.load_map[int(latency)]
        r_previous,g_previous,b_previous = self.currentLoads[switchId-1]
        switchPicture = self.pictures[switchID-1]
        width, height = switchPicture.size

        
        for x in range(width):
            for y in range(height):
                r,g,b = switchPicture.getpixel( (x,y) )
                if r == r_previous and g == g_previous and b == b_previous:
                    switchPicture.putpixel( (x,y), load)
        self.currentLoads[switchID-1] = load
        self.switchPhotos[switchID-1] = ImageTk.PhotoImage(switchPicture)
        self.canvas.itemconfig(self.canvasImages[switchID-1], image=self.switchPhotos[switchID-1])

    def setSwitchUtilization(self, switchID, utilization):
        if utilization >= 0 and utilization <= 1:
            load = self.load_map[int(utilization*10)]
            r_previous,g_previous,b_previous = self.currentLoads[switchID-1]
            switchPicture = self.pictures[switchID-1]
            width, height = switchPicture.size

        
            for x in range(width):
                for y in range(height):
                    r,g,b = switchPicture.getpixel( (x,y) )
                    if r == r_previous and g == g_previous and b == b_previous:
                        switchPicture.putpixel( (x,y), load)
            self.currentLoads[switchID-1] = load
            self.switchPhotos[switchID-1] = ImageTk.PhotoImage(switchPicture)
            self.canvas.itemconfig(self.canvasImages[switchID-1], image=self.switchPhotos[switchID-1])
