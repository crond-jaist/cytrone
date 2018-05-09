#!/bin/bash

#################################################
# Configure parameters
TRAINING_HOST=172.16.1.7
TRAINING_PORT=8082
INSTANTIATION_HOST=172.16.1.7
CONTENT_HOST=172.16.1.7


echo "# Stop CyTrONE server modules and tunnels."

#################################################
# Destroy tunnels (only needed if they were created)
echo "* Destroy the tunnel from gateway to ${TRAINING_HOST} (port ${TRAINING_PORT})."
pkill -f tunnel_trngsrv
if [ $? -eq 1 ];
then
    echo "  => No tunnel matches."
fi

#################################################
# Stop servers
echo "* Stop the training server on ${TRAINING_HOST}."
ssh ${TRAINING_HOST} "pkill -f cytrone_trngsrv"
if [ $? -eq 1 ];
then
    echo "  => No process matches."
fi

echo "* Stop the instantiation server on ${INSTANTIATION_HOST}."
ssh ${INSTANTIATION_HOST} "pkill -f cytrone_instsrv"
if [ $? -eq 1 ];
then
    echo "  => No process matches."
fi

echo "* Stop the content server on ${CONTENT_HOST}."
ssh ${CONTENT_HOST} "pkill -f cytrone_contsrv"
if [ $? -eq 1 ];
then
    echo "  => No process matches."
fi
