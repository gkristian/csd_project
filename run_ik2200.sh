mkdir -p /var/log/spacey
RYU_APP='netflowmodule.py testController3.py rpm.py'
LOG_FILE=/var/log/spacey/ryu_apps.log

ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  --verbose --log-file $LOG_FILE --default-log-level 3 $RYU_APP &> /tmp/cc.log &
python ./hum/hum.py &

