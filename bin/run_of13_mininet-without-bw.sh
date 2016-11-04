#TODO:
# Upgrade controller app to OpenFlow13. Estimate time 2 hours
TOPO_FILE=../src/midterm_topology-nobw.py 
#TOPO_FILE=SimpleTopo.py
#TODO:

#mn --custom $TOPO_FILE  --topo topo2 --controller remote --switch ovs  --mac
mn --custom $TOPO_FILE  --topo topo2 --controller remote --switch ovs,protocols=OpenFlow13  --mac -v debug

#below line doesnt cause all switches to come up as if topology py is not read
##mn --switch ovs,protocols=OpenFlow13  --mac --controller remote,ip=127.0.0.1,port=6633 --custom $TOPO_FILE -v debug
