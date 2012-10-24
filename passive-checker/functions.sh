#!/bin/bash
# Andrew Cutler, Adlibre 2009-03-24


## config

NAGIOS_DIR=/usr/sbin/
NAGIOS_CFG=/etc/nagios/
NAGIOS_SERVER='monitor.example.com'
NAGIOS_PORT=5667

PLUGINS=/etc/nagios/plugins
NRPE_CFG=/etc/nagios/nrpe.d

## end config


#
# Send passive alert information to Nagios
#
function raiseAlert {
    # $1 - Service name that has been set up on nagios/nagiosdev server
    # $2 - Return code 0=success, 1=warning, 2=critical
    # $3 - Message you want to send
    # <host_name>,<svc_description>,<return_code>,<plugin_output>
    if [ -f ${NAGIOS_DIR}send_nsca ]; then
        echo "`hostname`,$1,$2,$3" | ${NAGIOS_DIR}send_nsca -H ${NAGIOS_SERVER} \
        -p ${NAGIOS_PORT} -d "," -c ${NAGIOS_CFG}send_nsca.cfg > /dev/null;
        #echo "Debug: Message Sent to Nagios: $1 $2 $3.";
    else
        echo "Warning: Nagios Plugin not found.";
    fi
}

