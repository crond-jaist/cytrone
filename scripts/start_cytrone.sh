#!/bin/bash

################################
# Configure parameters
SCRIPT_DIR="/home/cyuser/cytrone/code"
CYRIS_PATH="/home/cyuser/cyris/"
CNT2LMS_PATH="/home/cyuser/moodle/cnt2lms/"
SETTINGS_PATH="/home/cyuser/moodle/settings/"

TRAINING_HOST=172.16.1.7
TRAINING_PORT=8082
INSTANTIATION_HOST=172.16.1.7
INSTANTIATION_PORT=8083
CONTENT_HOST=172.16.1.3
CONTENT_PORT=8084
MOODLE_HOST=moodle

SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"


echo "# Start CyTrONE server modules and tunnels."

################################
# Create tunnels
# This functionality is needed if training is managed on a gateway, not the training server itself;
# altough this is not absolutely necessary, we recommend the use of a gateway for security purposes
echo "* Create tunnel from gateway to ${TRAINING_HOST} (port ${TRAINING_PORT})..."
bash -c "exec -a tunnel_trngsrv ssh ${SSH_OPTIONS} -f -L 0.0.0.0:${TRAINING_PORT}:${TRAINING_HOST}:${TRAINING_PORT} cyuser@localhost -N"

echo "* Create tunnel from ${TRAINING_HOST} to Moodle VM (port ${CONTENT_PORT})..."
ssh ${SSH_OPTIONS} ${TRAINING_HOST} "bash -c 'exec -a tunnel_contsrv ssh ${SSH_OPTIONS} -f -L 0.0.0.0:${CONTENT_PORT}:192.168.122.22:${CONTENT_PORT} cyuser@${CONTENT_HOST} -N'" &

################################
# Start servers
echo "* Start training server on ${TRAINING_HOST} (port ${TRAINING_PORT})."
ssh ${SSH_OPTIONS} ${TRAINING_HOST} "cd ${SCRIPT_DIR}; bash -c 'exec -a start_trngsrv python -u ${SCRIPT_DIR}/trngsrv.py'" &

echo "* Start instantiation server on ${TRAINING_HOST} (port ${INSTANTIATION_PORT})."
ssh ${SSH_OPTIONS} ${INSTANTIATION_HOST} "cd ${SCRIPT_DIR}; bash -c 'exec -a start_instsrv python -u ${SCRIPT_DIR}/instsrv.py --path ${CYRIS_PATH}'" &

echo "* Start content server on ${CONTENT_HOST} (port ${CONTENT_PORT})."
ssh ${SSH_OPTIONS} ${CONTENT_HOST} "ssh ${MOODLE_HOST} 'cd ${SCRIPT_DIR}; bash -c \"exec -a start_contsrv python -u ${SCRIPT_DIR}/contsrv.py --path ${CNT2LMS_PATH} --settings ${SETTINGS_PATH}\"'" &

sleep 3
