#!/bin/bash

###########################################################
# Stop the CyTrONE framework
###########################################################

###########################################################
# Usage information

# $ ./stop_cytrone.sh


###########################################################
# Load configuration

: CROND_PREFIX=${CROND_PREFIX:=/home/cyuser}
CYTRONE_SCRIPTS_CONFIG=$CROND_PREFIX/cytrone/scripts/CONFIG
if [ -f $CYTRONE_SCRIPTS_CONFIG ]; then
        . $CYTRONE_SCRIPTS_CONFIG
fi

echo "# Stop CyTrONE server modules and tunnels."


###########################################################
# Stop CyTrONE

# Destroy tunnels (only needed if they were created)
if ! [ x"$MANAGED_ON_GATEWAY"x = xx ]
then
echo "* Destroy the tunnel from gateway to ${TRAINING_HOST}."
pkill -f tunnel_trngsrv
if [ $? -eq 1 ];
then
    echo "  => No tunnel matches."
fi
fi

# Stop the internal server modules
echo "* Stop the training server on ${TRAINING_HOST}."
ssh ${CYTRONE_USER}@${TRAINING_HOST} "pkill -f cytrone_trngsrv"
if [ $? -eq 1 ];
then
    echo "  => No process matches."
fi

echo "* Stop the instantiation server on ${INSTANTIATION_HOST}."
ssh ${CYTRONE_USER}@${INSTANTIATION_HOST} "pkill -f cytrone_instsrv"
if [ $? -eq 1 ];
then
    echo "  => No process matches."
fi

echo "* Stop the content server on ${CONTENT_HOST}."
ssh ${CYTRONE_USER}@${CONTENT_HOST} "pkill -f cytrone_contsrv"
if [ $? -eq 1 ];
then
    echo "  => No process matches."
fi

exit 0
