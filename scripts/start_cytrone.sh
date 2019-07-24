#!/bin/bash

###########################################################
# Start the CyTrONE framework
###########################################################

###########################################################
# Usage information

# $ ./start_cytrone.sh


###########################################################
# Load configuration

# Prepare logger
trap 'logger -p daemon.warning receive SIGHUP' HUP

# Read configuration
: CROND_PREFIX=${CROND_PREFIX:=/home/cyuser}
CYTRONE_SCRIPTS_CONFIG=$CROND_PREFIX/cytrone/scripts/CONFIG

if [ -f $CYTRONE_SCRIPTS_CONFIG ]; then
	. $CYTRONE_SCRIPTS_CONFIG
fi

# Set local variables
LOG=$LOGDIR/cytrone-`date +%Y%m%dT%H%M`.log

# Switch logfile path
exec < /dev/null >> $LOG 2>&1

# ssh options
SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error"


###########################################################
# Start CyTrONE

echo "# Start CyTrONE server modules and tunnels."

# Create tunnels
# This functionality is needed if training is managed on a gateway,
# not on the training server itself; although it is not absolutely
# necessary, we recommend the use of a gateway for security purposes
if [ x"$MANAGED_ON_GATEWAY"x = xx ]
then
echo "* Skip tunnel on gateway for training server"
else
echo "* Create tunnel from gateway to ${TRAINING_HOST} (port ${TRAINING_PORT})..."
bash -c "exec -a tunnel_trngsrv ssh ${SSH_OPTIONS} -f -L 0.0.0.0:${TRAINING_PORT}:${TRAINING_HOST}:${TRAINING_PORT} localhost -N"
fi

# Start the internal CyTrONE modules (servers listening for commands)
echo "* Start training server on      ${TRAINING_HOST} (user ${CYTRONE_USER}, port ${TRAINING_PORT})."
ssh ${SSH_OPTIONS} ${CYTRONE_USER}@${TRAINING_HOST} "cd ${CODE_DIR}; bash -c 'exec -a cytrone_trngsrv python -u ${CODE_DIR}/trngsrv.py'" &

echo "* Start instantiation server on ${INSTANTIATION_HOST} (user ${CYTRONE_USER}, port ${INSTANTIATION_PORT})."
ssh ${SSH_OPTIONS} ${CYTRONE_USER}@${INSTANTIATION_HOST} "cd ${CODE_DIR}; bash -c 'exec -a cytrone_instsrv python -u ${CODE_DIR}/instsrv.py --path ${CYRIS_PATH} --cyprom ${CYPROM_PATH}'" &

echo "* Start content server on       ${CONTENT_HOST} (user ${CYTRONE_USER}, port ${CONTENT_PORT})."
ssh ${SSH_OPTIONS} ${CYTRONE_USER}@${CONTENT_HOST} "cd ${CODE_DIR}; bash -c 'exec -a cytrone_contsrv python -u ${CODE_DIR}/contsrv.py --path ${CYLMS_PATH} --config ${CYLMS_CONFIG}'" &

sleep 3

exit 0
