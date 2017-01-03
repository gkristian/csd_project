export PATH=$PATH:/home/csd/.local/bin
ryu-manager --ofp-tcp-listen-port 6653 /home/csd/ryu/apps/nfm.py /home/csd/ryu/apps/testController2.py
