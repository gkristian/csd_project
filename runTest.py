import stanfordVisulization
from Tkinter import Tk
import random
from client import client_side

root = Tk()
ts = stanfordVisulization.UI(root)

#ts.updateUI(0)
#ts.setLinkUtilization(1, 0.4)
#ts.setLinkUtilization(5, 0.7)
#ts.setLinkUtilization(8, 1)
#ts.setSwitchUtilization(6, 0.436)

f = open('stanfordlinks.txt')
linkList = []
mapLinks = {}
for line in f:
	#print(line, len(line))
	line = line.split(' ')
	mapLinks[line[0]] = line[1]
	switches = line[0].split('-')
	linkList.append(switches)
	#linkID = int(line[1].split('\n')[0])
	#print(switches, linkID)
	#[FROM, TO] = direction.split('-')
	#oppositDirection = TO+'-'+FROM
	#testDict[direction] = linkID
	#testDict[oppositDirection] = linkID


localurl = 'http://127.0.0.1:8000/Tasks.txt'
url = 'http://130.229.146.35:8000/Tasks.txt'
nfm_data = {'module': 'nfm', 'timestamp': 000,'keylist':['link_utilization','packet_dropped']}
hum_data = {'module': 'hum', 'timestamp': 000,'keylist':['core','memory']}
rpm_data = {'module': 'rpm', 'keylist':['latencies']}

def fetchDataFromDM():
	cl = client_side(localurl)
	nfm_result = cl.getme(nfm_data)
	link_utilization = nfm_result[0]
	packet_dropped = nfm_result[1]
	mapp = link_utilization[1]
	for key,value in mapp.iteritems():
		encoded_key = key.encode('utf-8')
		#print key, value
		testLinkUtil(encoded_key, value)
	#rpm_result = cl.getme(rpm_data)
	#latencies = rpm_result[1]
	#for dpid, value in latencies:
	#	normalized = value['normalized_current_latency']
	#	ts.setRPMUtilization(int(dpid), float(normalized))
def testLinkUtil(key, value):

	if key in mapLinks:
		k = mapLinks[key].split('\n')[0]
		k = int(k) - 1
		ts.setLinkUtilization(k, int(value))
	#hum_result = cl.getme(hum_data)

def updateUtilizations():
    #linkUtilization = random.uniform(0.0, 1.0)
    fetchDataFromDM()
    #switchUtilization = random.uniform(0.0, 1.0)
    #linkID = random.randint(0, len(linkList)-1)
    #print linkID
    #[FROM, TO] = linkList[linkID]
    #switchID = random.randint(1,26)
    #ts.setLinkUtilization(int(FROM), int(TO), linkUtilization)
    #print("Switch: ",switchID, "Utilization: ",switchUtilization)
    #ts.setLinkUtilization(linkID, linkUtilization)
    #ts.setSwitchUtilization(switchID, switchUtilization)
    #print utilization
    root.after(1000, updateUtilizations)

def testUtilization():

	ts.setLinkUtilization(1, 27, 0.7)

#root.after(0, fetchDataFromDM)
#root.after(0, testUtilization)
root.after(0, updateUtilizations)
root.mainloop()
