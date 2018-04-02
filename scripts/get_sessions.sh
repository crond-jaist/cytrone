#!/bin/bash

###########################################################
# Usage information

# > ./get_sessions.sh


###########################################################
# Configure action settings

#ACTION="fetch_content"
ACTION="get_sessions"
#ACTION="get_configurations"

TRAINING_SERVER=cytrone_host_name_or_ip
TRAINING_PORT=8082

USER="john_doe"
PASSWORD="john_passwd"

###########################################################
# Display training settings

echo -e "# Get active training sessions from CyTrONE."
echo -e "* Training settings:"
echo -e "  - USER:\t${USER}"
echo -e "  - PASSWORD:\t******"


###########################################################
# Execute training creation command
../code/trngcli.py ${TRAINING_SERVER}:${TRAINING_PORT} "user=${USER}&password=${PASSWORD}&action=${ACTION}"
