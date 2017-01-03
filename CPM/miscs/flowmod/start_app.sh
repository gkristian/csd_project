killall -9 ryu-manager
sleep 1
RYU_CC_APP=flowmod_experiments
LOG_FILE=./app.log
ryu-manager --observe-links --install-lldp-flow  --verbose --log-file $LOG_FILE --default-log-level 3 $RYU_CC_APP
