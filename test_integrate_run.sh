rm -f /var/www/html/spacey/cpm.log

 ryu-manager  --ofp-tcp-listen-port 6633 --observe-links --install-lldp-flow --verbose --default-log-level 3  --log-file /var/www/html/spacey/cpm.log ../controller_core/src/controller_core_of13.py
