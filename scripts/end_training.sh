#!/bin/bash

###########################################################
# End one or more active sessions in CyTrONE
###########################################################

###########################################################
# Usage information

# $ ./end_training.sh [session_id] [session_id] ...
#
# NOTE: If a session id is provided as argument, the value will be
#       used to identify the session to be ended, otherwise a default
#       session id is used. Multiple session ids separated by spaces
#       are accepted as arguments.


###########################################################
# Load configuration

: CROND_PREFIX=${CROND_PREFIX:=/home/cyuser}
CYTRONE_SCRIPTS_CONFIG=$CROND_PREFIX/cytrone/scripts/CONFIG

if [ -f $CYTRONE_SCRIPTS_CONFIG ]; then
        . $CYTRONE_SCRIPTS_CONFIG
else
    echo "end_training: ERROR: Configuration file not found: ${CYTRONE_SCRIPTS_CONFIG}"
    exit 1
fi

# Use default session id if necessary
DEFAULT_SESSION_ID=1
if [ $# -ge 1 ];
then
    SESSION_IDS="$@"
else
    SESSION_IDS=${DEFAULT_SESSION_ID}
fi

###########################################################
# Process each session based on its id

for session_id in ${SESSION_IDS}
do
    # Display training settings
    echo -e "# End training using CyTrONE."
    echo -e "* Training settings:"
    echo -e "  - USER:\t${USER}"
    echo -e "  - PASSWORD:\t******"
    echo -e "  - SESSION_ID:\t${session_id}"

    # Execute action via CyTrONE (in the background)
    ACTION="end_training"
    ../code/trngcli.py ${TRAINING_HOST}:${TRAINING_PORT} "user=${USER}&password=${PASSWORD}&action=${ACTION}&range_id=${session_id}" &

done

# Wait for all commands to end
wait
