#!/bin/bash

###########################################################
# Get information about active sessions in CyTrONE
###########################################################

###########################################################
# Usage information

# $ ./get_sessions.sh


###########################################################
# Load configuration

: CROND_PREFIX=${CROND_PREFIX:=/home/cyuser}
CYTRONE_SCRIPTS_CONFIG=$CROND_PREFIX/cytrone/scripts/CONFIG

if [ -f $CYTRONE_SCRIPTS_CONFIG ]; then
        . $CYTRONE_SCRIPTS_CONFIG
else
    echo "get_sessions: ERROR: Configuration file not found: ${CYTRONE_SCRIPTS_CONFIG}"
    exit 1
fi

###########################################################
# Display training settings

echo -e "# Get active training sessions from CyTrONE."
echo -e "* Training settings:"
echo -e "  - USER:\t${USER}"
echo -e "  - PASSWORD:\t******"


###########################################################
# Execute action via CyTrONE

ACTION="get_sessions"
../code/trngcli.py ${TRAINING_HOST}:${TRAINING_PORT} "user=${USER}&password=${PASSWORD}&action=${ACTION}"

exit $?
