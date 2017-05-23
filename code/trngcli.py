#!/usr/bin/python

#############################################################################
# Classes related to the CyTrONE training client operation
#############################################################################

# External imports
import sys
import urllib

import logging
#logging.basicConfig(level=logging.DEBUG, format='* %(levelname)s: %(filename)s: %(message)s')
logging.basicConfig(level=logging.INFO, format='* %(levelname)s: %(filename)s: %(message)s')

# Internal imports
import sessinfo
import trnginfo
import query


#############################################################################
# Constants
#############################################################################

# Various constants
SEPARATOR = "----------------------------------------------------------------"

# Debugging constants
DATABASE_DIR = "../database/"
INSTANTIATE_RANGE_FROM_FILE = False
SAMPLE_INSTANTIATE_RANGE = DATABASE_DIR + "NIST-level1-range.yml"

    
#############################################################################
# Main program
#############################################################################
try:

    # Initialize variables
    POST_parameters = None

    # Test whether any arguments (besides the script name) are provided;
    # if so, the first actual argument is considered to be the URL
    if len(sys.argv) > 2:
        server_url = sys.argv[1]
        POST_parameters = sys.argv[2]
    else:
        logging.error("Not enough arguments were provided")
        logging.info("Syntax: python trngcli.py SRV_ADDR:SRV_PORT POST_PARAMS")
        quit(-1)

    logging.info("CyTrONE training client connecting to {0}...".format(server_url))

    # Parse parameters
    params = query.Parameters()
    params.parse_parameters(POST_parameters)
    action = params.get(query.Parameters.ACTION)

    # Additional parameter needed for instantiate range action
    if action == query.Parameters.INSTANTIATE_RANGE and INSTANTIATE_RANGE_FROM_FILE:
        try:
            instantiate_file = open(SAMPLE_INSTANTIATE_RANGE, "r")
            instantiate_content = instantiate_file.read()
            instantiate_file.close()
            logging.info("Use cyber range description from file {0}.".format(SAMPLE_INSTANTIATE_RANGE))
            
            description_parameters = {query.Parameters.DESCRIPTION_FILE: instantiate_content}
            description_parameters = urllib.urlencode(description_parameters)
            POST_parameters += ("&" + description_parameters)
        except IOError:
            logging.error("Cannot read from file {0}.".format(SAMPLE_INSTANTIATE_RANGE))

    # Connect to server with the given POST parameters
    logging.info("Client POST parameters: "+ POST_parameters)
    if POST_parameters != None:
        data_stream = urllib.urlopen(server_url, POST_parameters)
    else:
        data_stream = urllib.urlopen(server_url)
    data = data_stream.read()

    # Show server response
    logging.debug("Server response: " + data)

    (status, message) = query.Response.parse_server_response(data)

    # Display detailed response data differently for each action
    # Handle training server actions
    if action == query.Parameters.FETCH_CONTENT:
        logging.info("Training server action '{0}' done => {1}.".format(action, status))

        # Parse the training information into a TrainingInfo object
        training_info = trnginfo.TrainingInfo()
        if training_info.parse_JSON_data(data):
            logging.info("Showing retrieved training content information...")
            training_info.pretty_print()
            
    elif action == query.Parameters.CREATE_TRAINING:
        logging.info("Training server action '{0}' done => {1}.".format(action, status))

        # Display message if any
        if message:
            logging.info("Showing training session creation information... ")
            print SEPARATOR
            # We use rstrip() to remove trailing end of line etc.
            print urllib.unquote(message).rstrip()
            print SEPARATOR

    elif action == query.Parameters.GET_CONFIGURATIONS:
        logging.info("Training server action '{0}' done => {1}.".format(action, status))

        # Parse the configuration information into a SessionInfo object
        session_info = sessinfo.SessionInfo()
        if session_info.parse_JSON_data(data):
            logging.info("Showing retrieved saved configuration information...")
            session_info.pretty_print()
 
    elif action == query.Parameters.GET_SESSIONS:
        logging.info("Training server action '{0}' done => {1}.".format(action, status))

        # Parse the session information into a SessionInfo object
        session_info = sessinfo.SessionInfo()
        if session_info.parse_JSON_data(data):
            logging.info("Showing retrieved active session information...")
            session_info.pretty_print()

    elif action == query.Parameters.END_TRAINING:
        logging.info("Training server action '{0}' done => {1}.".format(action, status))

        # Display message if any
        if message:
            logging.info("Showing training session termination information... ")
            print SEPARATOR
            print message
            print SEPARATOR


    # Handle instantiation server actions
    elif action == query.Parameters.INSTANTIATE_RANGE:        
        logging.info("Instantiation server action '{0}' done => {1}.".format(action, status))

        # Display message if any
        if message:
            logging.info("Showing cyber range instantiation information... ")
            print SEPARATOR
            print message
            print SEPARATOR

    elif action == query.Parameters.DESTROY_RANGE:        
        logging.info("Instantiation server action '{0}' done => {1}.".format(action, status))

        # Display message if any
        if message:
            logging.info("Showing cyber range destruction information... ")
            print SEPARATOR
            print message
            print SEPARATOR

    # Handle content server actions
    elif action == query.Parameters.UPLOAD_CONTENT:        
        logging.info("Content server action '{0}' done => {1}.".format(action, status))

        # Display message if any
        if message:
            logging.info("Showing LMS content upload information... ")
            print SEPARATOR
            print message
            print SEPARATOR

    elif action == query.Parameters.RESET_CONTENT:        
        logging.info("Content server action '{0}' done Status: {1}.".format(action, status))

        # Display message if any
        if message:
            logging.info("Showing LMS content reset information... ")
            print SEPARATOR
            print message
            print SEPARATOR

    # Handle unknown actions
    else:
        logging.error("Unrecognized action: {0}.".format(action))
        
except IOError as error:
    logging.error("{0}.".format(error))

except ValueError as error:
    logging.error("{0}.".format(error))
