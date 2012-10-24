#!/bin/bash

# Passive plugin runner

CWD="`dirname $0`/";

. ${CWD}functions.sh
. ${CWD}local_config.sh

for c in $COMMANDS; do

    # check_disk = 'Check Disk'
    #NAME=`echo ${c} | sed 's@_@ @g;s@\<.@\u&@g'`

    # Get name from first line in file
    NAME=`head -n 1 ${NRPE_CFG}/${c}.cfg | sed 's@# @@g'`

    CMD=`tail -n 1 ${NRPE_CFG}/${c}.cfg | sed -e "s@command\[$c\]=@@g"`
    MSG=`${CMD}`
    RC=$?

    raiseAlert "${NAME}" $RC "${MSG}"

done

