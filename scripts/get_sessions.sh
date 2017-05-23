#!/bin/bash

###########################################################
# Usage information

# > ./get_sessions.sh


###########################################################
# Configure action settings

#ACTION="fetch_content"
ACTION="get_sessions"
#ACTION="get_configurations"

#TRAINING_SERVER=127.0.0.1
TRAINING_SERVER=gateway

USER="john_doe"
#USER="jane_roe"


###########################################################
# Display training settings

echo -e "# Get active training sessions from CyTrONE."
echo -e "* Training settings:"
echo -e "  - USER:\t${USER}"


###########################################################
# Execute training creation command
../code/trngcli.py http://${TRAINING_SERVER}:8082 "user=${USER}&action=${ACTION}"
