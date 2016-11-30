mkdir -p /var/log/spacey
RYU_APP='netflowmodule.py testController3.py rpm.py'
#LOG_FILE=/var/log/spacey/ryu_apps.log
LOG_FILE=/var/www/html/spacey/ryu_apps.log

ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  --verbose --log-file $LOG_FILE --default-log-level 3 $RYU_APP &> /tmp/cc.log &
#ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow  --verbose --log-file $LOG_FILE --default-log-level 3 $RYU_APP  > /var/www/html/spacey/ryu_apps_redirectedlog.log 2>&1 &
#python ./hum/hum.py  > /var/www/html/spacey/hum_redirectedlog.log 2>&1 &
python ./hum/hum.py & 


