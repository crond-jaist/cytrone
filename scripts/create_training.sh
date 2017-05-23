#!/bin/bash

###########################################################
# Usage information

# > ./create_training.sh [training_choice]
#
# Note: If a training choice is provided as argument, the value will
#       be used to identify the type of session to be created;
#       otherwise a menu with available choice will be displayed,
#       and user input will be requested.


###########################################################
# Configure training settings

#TRAINING_SERVER=127.0.0.1
TRAINING_SERVER=gateway

USER="john_doe"
#USER="jane_roe"

# Number of cyber range instances to be created
COUNT=2

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

case "${CHOICE}" in

1)  LANGUAGE="en"
    TYPE="Scenario-Based Training"
    SCENARIO="Information Security Testing and Assessment"
    LEVEL="Level 1 (Easy)"
    ;;
2)  LANGUAGE="en"
    TYPE="Scenario-Based Training"
    SCENARIO="Information Security Testing and Assessment"
    LEVEL="Level 2 (Medium)"
    ;;
3)  LANGUAGE="ja"
    TYPE="シナリオに基づいた演習"
    SCENARIO="情報セキュリティテスト＆評価"
    LEVEL="レベル 1 （イージー）"
    ;;
4) LANGUAGE="ja"
   TYPE="シナリオに基づいた演習"
   SCENARIO="情報セキュリティテスト＆評価"
   LEVEL="レベル 2 （ミディアム）"
   ;;
5) LANGUAGE="en"
   TYPE="Scenario-Based Training"
   SCENARIO="Information Security Testing and Assessment"
   LEVEL="Level 1 (Easy)"
   ;;
*) echo "Unrecognized choice, try again."
   ;;
esac


###########################################################
# Display training settings
echo -e "# Create training using CyTrONE."
echo -e "* Training settings:"
echo -e "  - USER:\t${USER}"
echo -e "  - TYPE:\t${TYPE}"
echo -e "  - SCENARIO:\t${SCENARIO}"
echo -e "  - LEVEL:\t${LEVEL}"
echo -e "  - COUNT:\t${COUNT}"
echo -e "  - LANGUAGE:\t${LANGUAGE}"


###########################################################
# Execute training creation command
../code/trngcli.py http://${TRAINING_SERVER}:8082 "user=${USER}&action=create_training&count=${COUNT}&lang=${LANGUAGE}&type=${TYPE}&scenario=${SCENARIO}&level=${LEVEL}"
