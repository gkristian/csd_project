#TODO:
# Upgrade controller app to OpenFlow13. Estimate time 2 hours
TOPO_FILE=../../src/SimpleTopo.py
#TOPO_FILE=SimpleTopo.py
#TODO:

mn --custom $TOPO_FILE  --topo simpletopo --controller remote --switch ovs  --mac
#mn --custom $TOPO_FILE  --topo topo2 --controller remote --switch ovs,protocols=OpenFlow13  --mac
