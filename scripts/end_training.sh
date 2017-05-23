#!/bin/bash

###########################################################
# Usage information

# > ./end_training.sh [range_id]
#
# Note: If range id is provided as argument, the value will
#       be used to identify the session to be ended,
#       otherwise a default range id is used.

DEFAULT_RANGE_ID=1


###########################################################
# Configure training settings

#TRAINING_SERVER=127.0.0.1
TRAINING_SERVER=gateway

USER="john_doe"
#USER="jane_roe"

if [ $# -ge 1 ];
then
    RANGE_IDS="$@"
else
    RANGE_IDS=${DEFAULT_RANGE_ID}
fi

for range_id in ${RANGE_IDS}
do

    ###########################################################
    # Display training settings

    echo -e "# End training using CyTrONE."
    echo -e "* Training settings:"
    echo -e "  - USER:\t${USER}"
    echo -e "  - RANGE_ID:\t${range_id}"


    ###########################################################
    # Execute end training command (in the background)
    ../code/trngcli.py http://${TRAINING_SERVER}:8082 "user=${USER}&action=end_training&range_id=${range_id}" &

done

# Wait for all commands to end
wait
