#!/bin/sh

###########################################################
# Configure action settings

: CROND_PREFIX=${CROND_PREFIX:=/home/cyuser}
CYTRONE_SCRIPTS_CONFIG=$CROND_PREFIX/cytrone/scripts/CONFIG

if [ -f $CYTRONE_SCRIPTS_CONFIG ]; then
        . $CYTRONE_SCRIPTS_CONFIG
fi

# local vars.
CRID=$1
if [ x"$CRID"x = xx ]
then
	echo "Usage: $0 <range_id>"
	exit 1
fi
CYRIS_CYBERRANGE_PATH=$CYRIS_PATH/cyber_range
CRINFODIR=$CYRIS_CYBERRANGE_PATH/$CRID
CRNOTIFI=$CRINFODIR/range_notification-cr$CRID.txt

ssh ${SSH_OPTIONS} ${CYTRONE_USER}@${INSTANTIATION_HOST} "cat $CRNOTIFI"
exit $?

