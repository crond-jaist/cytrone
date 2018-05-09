#!/bin/bash

################################
# Configure parameters
SCRIPT_DIR="/home/cyuser/cytrone/code"
CYRIS_PATH="/home/cyuser/cyris/"
CYLMS_PATH="/home/cyuser/cylms/"
CYLMS_CONFIG="/home/cyuser/cytrone/moodle/cylms_config"

TRAINING_HOST=172.16.1.7
TRAINING_PORT=8082
INSTANTIATION_HOST=172.16.1.7
INSTANTIATION_PORT=8083
CONTENT_HOST=172.16.1.7
CONTENT_PORT=8084

SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error"


echo "# Start CyTrONE server modules and tunnels."

################################
# Create tunnels
# This functionality is needed if training is managed on a gateway, not the training server itself;
# altough this is not absolutely necessary, we recommend the use of a gateway for security purposes
echo "* Create tunnel from gateway to ${TRAINING_HOST} (port ${TRAINING_PORT})..."
bash -c "exec -a tunnel_trngsrv ssh ${SSH_OPTIONS} -f -L 0.0.0.0:${TRAINING_PORT}:${TRAINING_HOST}:${TRAINING_PORT} localhost -N"

################################
# Start servers
echo "* Start training server on ${TRAINING_HOST} (port ${TRAINING_PORT})."
ssh ${SSH_OPTIONS} ${TRAINING_HOST} "cd ${SCRIPT_DIR}; bash -c 'exec -a cytrone_trngsrv python -u ${SCRIPT_DIR}/trngsrv.py'" &

echo "* Start instantiation server on ${TRAINING_HOST} (port ${INSTANTIATION_PORT})."
ssh ${SSH_OPTIONS} ${INSTANTIATION_HOST} "cd ${SCRIPT_DIR}; bash -c 'exec -a cytrone_instsrv python -u ${SCRIPT_DIR}/instsrv.py --path ${CYRIS_PATH}'" &

echo "* Start content server on ${CONTENT_HOST} (port ${CONTENT_PORT})."
ssh ${SSH_OPTIONS} ${CONTENT_HOST} "cd ${SCRIPT_DIR}; bash -c 'exec -a cytrone_contsrv python -u ${SCRIPT_DIR}/contsrv.py --path ${CYLMS_PATH} --config ${CYLMS_CONFIG}'" &

sleep 3
