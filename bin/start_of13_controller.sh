# Dependencies are:
# ryu 4.6
# python 2.7
#
# Notes:
# No need to change PYTHONPATH env variable
RYU_CC_APP=../src/controller_core_of13.py
LOG_FILE=/tmp/cclog.log
OUTPUT_LOG=/tmp/cc.log

#ryu-manager --observe-links --verbose --log-file $LOG_FILE --default-log-level 3 $RYU_CC_APP &> $OUTPUT_LOG & 
./stop_controller.sh
echo "Now starting ryu application "
ryu-manager --observe-links --install-lldp-flow  --verbose --log-file $LOG_FILE --default-log-level 3 $RYU_CC_APP &> $OUTPUT_LOG & 
ps auxw |grep ryu-manager |grep -v grep
echo "____"

echo The log files are $LOG_FILE and $OUTPUT_LOG
#echo tail -f anyone of them

# tail -f $LOG_FILE |grep -v Event

