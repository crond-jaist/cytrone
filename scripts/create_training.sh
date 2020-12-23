#!/bin/bash

###########################################################
# Create a training session in CyTrONE
###########################################################

###########################################################
# Usage information

# $ ./create_training.sh [training_choice]
#
# NOTE: If a training choice is provided as argument, the value will
#       be used to identify the type of session to be created;
#       otherwise a menu with available choice will be displayed, and
#       user input will be requested.


###########################################################
# Load configuration

: CROND_PREFIX=${CROND_PREFIX:=/home/cyuser}
CYTRONE_SCRIPTS_CONFIG=$CROND_PREFIX/cytrone/scripts/CONFIG

if [ -f $CYTRONE_SCRIPTS_CONFIG ]; then
        . $CYTRONE_SCRIPTS_CONFIG
else
    echo "create_training: ERROR: Configuration file not found: ${CYTRONE_SCRIPTS_CONFIG}"
    exit 1
fi

###########################################################
# Prepare session information

# Set default number of cyber range instances to be created
COUNT=2

# Set choice to argument, or display selection menu
if [ $# -ge 1 ];
then
    CHOICE=$1
else
    DONE=false
    until ${DONE} ;
    do
	echo "# Please select the training type."
	echo "  1) NIST Level 1 (English)"
	echo "  2) NIST Level 2 (English)"
	echo "  3) NIST Level 1 (Japanese)"
	echo "  4) NIST Level 2 (Japanese)"
	echo "  5) User defined"
	read -p "Enter the number of your choice: " CHOICE

	if [ ${CHOICE} -ge 1 -a ${CHOICE} -le 5 ];
	then
	    DONE=true
	else
	    echo "ERROR: Unrecognized choice, try again."
	fi
    done
fi

# Configure parameters depending on choice
case "${CHOICE}" in

1)  LANGUAGE="en"
    TYPE="Scenario-Based Training"
    SCENARIO="Information Security Testing and Assessment"
    LEVEL="Level 1"
    ;;
2)  LANGUAGE="en"
    TYPE="Scenario-Based Training"
    SCENARIO="Information Security Testing and Assessment"
    LEVEL="Level 2"
    ;;
3)  LANGUAGE="ja"
    TYPE="シナリオに基づいた演習"
    SCENARIO="情報セキュリティテスト＆評価"
    LEVEL="レベル 1"
    ;;
4) LANGUAGE="ja"
   TYPE="シナリオに基づいた演習"
   SCENARIO="情報セキュリティテスト＆評価"
   LEVEL="レベル 2"
   ;;
5) LANGUAGE="en"
   TYPE="Scenario-Based Training"
   SCENARIO="Information Security Testing and Assessment"
   LEVEL="Demo Level"
   ;;
*) echo "Unrecognized choice, try again."
   ;;
esac

###########################################################
# Display training settings

echo -e "# Create training using CyTrONE."
echo -e "* Training settings:"
echo -e "  - USER:\t${USER}"
echo -e "  - PASSWORD:\t******"
echo -e "  - TYPE:\t${TYPE}"
echo -e "  - SCENARIO:\t${SCENARIO}"
echo -e "  - LEVEL:\t${LEVEL}"
echo -e "  - COUNT:\t${COUNT}"
echo -e "  - LANGUAGE:\t${LANGUAGE}"

###########################################################
# Execute action via CyTrONE

ACTION="create_training"
../code/trngcli.py ${TRAINING_HOST}:${TRAINING_PORT} "user=${USER}&password=${PASSWORD}&action=${ACTION}&count=${COUNT}&lang=${LANGUAGE}&type=${TYPE}&scenario=${SCENARIO}&level=${LEVEL}"

exit $?
