#!/usr/bin/python

#############################################################################
# Classes related to the CyTrONE training server operation
#############################################################################

# External imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import ssl
import urllib
import time
import random
import sys
import getopt
from SocketServer import ThreadingMixIn
import threading
from string import Template
import yaml
import logging
import re
import os

# Internal imports
import userinfo
import trnginfo
import sessinfo
import query
from storyboard import Storyboard
from password import Password

#############################################################################
# Constants
#############################################################################

CYTRONE_VERSION = "1.1"

# Web server constants
LOCAL_ADDRESS = "127.0.0.1"
SERVER_PORT   = 8082
HTTP_STATUS_OK = 200
REQUEST_ERROR = 404
SERVER_ERROR  = 500
LOCAL_SERVER  = False
SERVE_FOREVER = True # Use serve count if not using local server?!
CONTENT_SERVER_URL = "http://127.0.0.1:8084"
INSTANTIATION_SERVER_URL = "http://127.0.0.1:8083"
MAX_SESSIONS = 100
ENABLE_THREADS = True

# Names of files containing training-related information
USERS_FILE  = "users.yml"
SCENARIOS_FILE_EN = "training-en.yml"
SCENARIOS_FILE_JA = "training-ja.yml"
DATABASE_DIR = "../database/"

# Name of file containing saved training configurations
SAVED_CONFIGURATIONS_FILE = "saved_configurations.yml"

# Name of file containing active training sessions info
ACTIVE_SESSIONS_FILE = "active_sessions.yml"

# Debugging constants
DEBUG = False
EMULATE_DELAY = False

#############################################################################
# Manage the training server functionality
#############################################################################
class RequestHandler(BaseHTTPRequestHandler):

    # List of valid actions recognized by the training server
    VALID_ACTIONS = [query.Parameters.FETCH_CONTENT,
                     query.Parameters.CREATE_TRAINING,
                     query.Parameters.GET_CONFIGURATIONS,
                     query.Parameters.GET_SESSIONS,
                     query.Parameters.END_TRAINING,
                     query.Parameters.CREATE_TRAINING_Variation,
                     query.Parameters.GET_CR_CREATION_LOG,
                     query.Parameters.END_TRAINING_Variation]

    # List of valid languages recognized by the training server
    VALID_LANGUAGES = [query.Parameters.EN,
                     query.Parameters.JA]

    # List of sessions which are pending (being instantiated, etc.)
    pending_sessions = []

    # Locks for synchronizing access to shared resources, as follows:
    # - lock_active_sessions: active sessions list (and related variables: pending_sessions, cyber_range_id)
    # - lock_saved_configurations: saved configurations list
    lock_active_sessions = threading.Lock()
    lock_saved_configurations = threading.Lock()

    #########################################################################
    # Print log messages with custom format
    # Default format is shown below:
    #     127.0.0.1 - - [22/Jun/2016 14:47:56] "POST / HTTP/1.0" 200 -
    def log_message(self, format, *args):
        (client_host, client_port) = self.client_address
        print("* INFO: trngsrv: Server response to client %s - - [%s] %s" %
              (client_host, self.log_date_time_string(), format%args))

    #########################################################################
    # Various functions for cyber range id generation

    ## Hexadecimal id [not in use]
    def generate_id_hexadecimal(self):
        # Create a 6-digit hexadecimal id
        RANDOM_ID_LENGTH = 6
        cyber_range_id = "%0*x" % (RANDOM_ID_LENGTH, random.randrange(16**RANDOM_ID_LENGTH))
        return cyber_range_id

    ## Random decimal id in given range [not in use]
    def generate_id_random(self):
        # Create a 3-digit decimal id that is fit for
        # becoming the first byte in an IPv4 address
        # Reference: https://en.wikipedia.org/wiki/Reserved_IP_addresses
        invalid_bytes = [10, 100, 127, 169, 172, 192, 198, 203]
        done = False
        while not done:
            cyber_range_id = random.randint(1,223)
            if cyber_range_id not in invalid_bytes:
                done = True
        return cyber_range_id

    ## Decimal id between 1 and MAX_SESSIONS with lowest available value [not in use]
    ## (pending session ids are avoided)
    ## NOTE: Requires synchronization for active sessions list
    def generate_id_max_sessions_lowest(self, pending_sessions):
        cyber_range_id = None
        # Read current session info
        session_info = sessinfo.SessionInfo()
        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)
        for id in range(1,MAX_SESSIONS+1):
            # Check that id (as string) is _not_ already used for an existing or pending session
            if not (session_info.is_session_id(str(id))
                    or str(id) in pending_sessions):
                cyber_range_id = id
                break
        # Returned value should be an integer
        return cyber_range_id

    ## Decimal id between 1 and MAX_SESSIONS with next available value [in use]
    ## (if next value is unavailable, use lowest; pending session ids are avoided)
    ## NOTE: Requires synchronization for active sessions list
    def generate_id_max_sessions_next(self, pending_sessions):
        cyber_range_id = None
        # Read current session info
        session_info = sessinfo.SessionInfo()
        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)
        # For set operations we need to represent ids as integer,
        # not as string as stored internally
        possible_set = set(range(MAX_SESSIONS+1)) # All possible values
        invalid_set = set([0]) # Invalid values if any
        unavailable_set = invalid_set.union(session_info.get_id_list_int()) # Union with active sessions
        pending_set = set(map(int, pending_sessions))
        unavailable_set = unavailable_set.union(pending_set) # Union with pending sessions
        max_unavailable_value = max(unavailable_set)
        available_set = possible_set.difference(unavailable_set) # Usable values
        if (max_unavailable_value+1) in available_set:
            cyber_range_id = (max_unavailable_value+1)
        elif available_set:
            cyber_range_id = min(available_set)
            # Otherwise we'll return the None value set at the beginning
        # Returned value should be an integer
        return cyber_range_id

    #########################################################################
    # Generate a cyber range id
    def generate_cyber_range_id(self, pending_sessions):

        return self.generate_id_max_sessions_next(pending_sessions)

    #########################################################################
    # Check whether a range with the given id is active for the
    # specified user_id;
    # Return the activity id if session was found, None otherwise
    # Note: Requires synchronization for active sessions list
    def check_range_id_exists(self, range_id, user_id):

        # Read current session info
        session_info = sessinfo.SessionInfo()
        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)

        # Check if the given range id (as string) is already used
        if session_info.is_session_id_user(range_id, user_id):
            return session_info.get_activity_id(range_id, user_id)
        else:
            return None

    #########################################################################
    # Check whether a range with the given id is active for the
    # specified user_id;
    # Return the activity id if session was found, None otherwise
    # Note: Requires synchronization for active sessions list
    def check_range_id_and_activity_id_exists(self, range_id, user_id):
        # Read current session info
        session_info = sessinfo.SessionInfo()
        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)

        # Check if the given range id (as string) is already used
        if session_info.is_session_id_user(range_id, user_id):
            return session_info.get_activity_id_list(range_id, user_id)
        else:
            return None

    #########################################################################
    # Handle POST message
    def do_POST(self):

        # Get the parameters of the POST request
        params = query.Parameters(self)

        print ""
        print Storyboard.SEPARATOR2
        if Storyboard.ENABLE_PASSWORD:
            print("* INFO: trngsrv: Request POST parameters: [not shown because password use is enabled]")
        else:
            print("* INFO: trngsrv: Request POST parameters: {}".format(params))

        # Get the values of the parameters for given keys
        user_id = params.get(query.Parameters.USER)
        password = params.get(query.Parameters.PASSWORD)
        action = params.get(query.Parameters.ACTION)
        language = params.get(query.Parameters.LANG) 
        instance_count = params.get(query.Parameters.COUNT)
        ttype = params.get(query.Parameters.TYPE)
        scenario = params.get(query.Parameters.SCENARIO)
        level = params.get(query.Parameters.LEVEL)
        range_id = params.get(query.Parameters.RANGE_ID)

        if DEBUG:
            print Storyboard.SEPARATOR1
            print "POST PARAMETERS:"
            print Storyboard.SEPARATOR1
            print "USER: %s" % (user_id)
            if password:
                print "PASSWORD: ******"
            print "ACTION: %s" % (action)
            print "LANGUAGE: %s" % (language)
            print "COUNT: %s" % (instance_count)
            print "TYPE: %s" % (ttype)
            print "SCENARIO: %s" % (scenario)
            print "LEVEL: %s" % (level)
            print "RANGE_ID: %s" % (range_id)
            print Storyboard.SEPARATOR1

        ## Verify user information

        # Get user information from YAML file
        # Note: Only reading data that is (potentially) modified externally =>
        #       no need for synchronization
        user_info = userinfo.UserInfo()
        if not user_info.parse_YAML_file(DATABASE_DIR + USERS_FILE):
            self.respond_error(Storyboard.USER_SETTINGS_LOADING_ERROR)
            return
        if DEBUG:
            user_info.pretty_print()

        # Check that user id is valid
        if not user_id:
            self.respond_error(Storyboard.USER_ID_MISSING_ERROR)
            return
        user_obj = user_info.get_user(user_id) 
        if not user_obj:
            self.respond_error(Storyboard.USER_ID_INVALID_ERROR)
            return

        # Check password (if enabled)
        if Storyboard.ENABLE_PASSWORD:
            # Check whether password exists in database for current user
            if not user_obj.password:
                self.respond_error(Storyboard.USER_PASSWORD_NOT_IN_DATABASE_ERROR)
                return
            # If a password was provided, verify that it matches the encrypted one from the database
            if password:
                if not Password.verify(password, user_obj.password):
                    self.respond_error(Storyboard.USER_ID_PASSWORD_INVALID_ERROR)
                    return
            else:
                self.respond_error(Storyboard.USER_PASSWORD_MISSING_ERROR)
                return

        ## Verify action information

        # Check that action is valid
        if not action:
            self.respond_error(Storyboard.ACTION_MISSING_ERROR)
            return
        if action not in self.VALID_ACTIONS:
            self.respond_error(Storyboard.ACTION_INVALID_ERROR)
            return

        # Create training database content information object
        training_info = trnginfo.TrainingInfo()

        # Check that language is valid
        if not language:
            self.respond_error(Storyboard.LANGUAGE_MISSING_ERROR)
            return
        if language not in self.VALID_LANGUAGES:
            self.respond_error(Storyboard.LANGUAGE_INVALID_ERROR)
            return

        # Select the scenario information file based on the
        # requested language
        if language == query.Parameters.JA:
            training_settings_file = DATABASE_DIR + SCENARIOS_FILE_JA
        else:
            training_settings_file = DATABASE_DIR + SCENARIOS_FILE_EN

        if DEBUG:
            print "* DEBUG: trngsrv: Read training settings from '%s'..." % (training_settings_file)

        # Note: Only reading data that is (potentially) modified externally =>
        #       no need for synchronization
        result = training_info.parse_YAML_file(training_settings_file)

        if not result:
            self.respond_error(Storyboard.TRAINING_SETTINGS_LOADING_ERROR)
            return

        if DEBUG:
            training_info.pretty_print()

        # If we reached this point, it means processing was successful
        # => act according to each action

        ####################################################################
        # Fetch content action
        # Note: Only reading data that is (potentially) modified externally =>
        #       no need for synchronization
        if action == query.Parameters.FETCH_CONTENT: 

            # Convert the training info to the external JSON
            # representation that will be provided to the client
            response_data = training_info.get_JSON_representation()

        ####################################################################
        # Original Create training action
        # Note: Requires synchronized access to active sessions list
        elif action == query.Parameters.CREATE_TRAINING:

            if not instance_count:
                self.respond_error(Storyboard.INSTANCE_COUNT_MISSING_ERROR)
                return

            try:
                instance_count_value = int(instance_count)
            except ValueError as error:
                self.respond_error(Storyboard.INSTANCE_COUNT_INVALID_ERROR)
                return

            if not ttype:
                self.respond_error(Storyboard.TRAINING_TYPE_MISSING_ERROR)
                return

            if not scenario:
                self.respond_error(Storyboard.SCENARIO_NAME_MISSING_ERROR)
                return

            if not level:
                self.respond_error(Storyboard.LEVEL_NAME_MISSING_ERROR)
                return

            # Synchronize access to active sessions list and related variables
            self.lock_active_sessions.acquire()
            try:
                cyber_range_id = self.generate_cyber_range_id(self.pending_sessions)
                if cyber_range_id:
                     # Convert to string for internal representation
                    cyber_range_id = str(cyber_range_id)
                    self.pending_sessions.append(cyber_range_id)
                    print "* INFO: trngsrv: Allocated session with ID #%s." % (cyber_range_id)
                else:
                    self.respond_error(Storyboard.SESSION_ALLOCATION_ERROR)
                    return
            finally:
                self.lock_active_sessions.release()

            ########################################
            # Handle content upload
            content_file_name = training_info.get_content_file_name(scenario, level)
            if content_file_name == None:
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_IDENTIFICATION_ERROR)
                return

            content_file_name = DATABASE_DIR + content_file_name

            if DEBUG:
                print "* DEBUG: trngsrv: Training content file: %s" % (content_file_name)

            # Open the content file
            try:
                content_file = open(content_file_name, "r")
                content_file_content = content_file.read()
                content_file.close()

            except IOError as error:
                print "* ERROR: trngsrv: File error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_LOADING_ERROR)
                return

            try:
                # Note: creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.UPLOAD_CONTENT,
                    query.Parameters.DESCRIPTION_FILE: content_file_content,
                    query.Parameters.RANGE_ID: cyber_range_id
                }

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send upload request to content server %s." % (CONTENT_SERVER_URL)
                if DEBUG:
                    print "* DEBUG: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(CONTENT_SERVER_URL, query_params)
                data = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Content server response body: %s" % (data)

                (status, activity_id) = query.Response.parse_server_response(data)

                if DEBUG:
                    print("* DEBUG: trngsrv: Response status: {}".format(status))
                    print("* DEBUG: trngsrv: Response activity_id: {}".format(activity_id))

                if status == Storyboard.SERVER_STATUS_SUCCESS:
                    # Store activity id in session description
                    pass
                else:
                    print "* ERROR: trngsrv: Content upload error."
                    self.removePendingSession(cyber_range_id)
                    self.respond_error(Storyboard.CONTENT_UPLOAD_ERROR)
                    return

                # Save the response data
                contsrv_response = data

            except IOError as error:
                print "* ERROR: trngsrv: URL error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_SERVER_ERROR)
                return

            ########################################
            # Handle instantiation
            range_file_name = training_info.get_range_file_name(scenario, level)
            if range_file_name == None:
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.TEMPLATE_IDENTIFICATION_ERROR)
                # TODO: Should delete the content uploaded above before returning
                return

            range_file_name = DATABASE_DIR + range_file_name
            progression_scenario_name = training_info.get_progression_scenario_name(scenario, level)

            if DEBUG:
                print "* DEBUG: trngsrv: Cyber range file: %s" % (range_file_name)
                print "* DEBUG: trngsrv: Progression scenario: %s" % (progression_scenario_name)

            # Open the cyber range file (template)
            try:
                range_file = open(range_file_name, "r")
                range_file_content = range_file.read()
                range_file.close()

            except IOError as error:
                print "* ERROR: trngsrv: File error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.TEMPLATE_LOADING_ERROR)
                return

            # Do instantiation
            try:
                # Replace variables in the range file
                range_file_content = user_obj.replace_variables(range_file_content, cyber_range_id, instance_count_value)

                # NOTE: creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.INSTANTIATE_RANGE,
                    query.Parameters.DESCRIPTION_FILE: range_file_content,
                    query.Parameters.RANGE_ID: cyber_range_id
                }

                # If we have a progression scenario defined, we add its name to the query
                if progression_scenario_name:
                    query_tuples[query.Parameters.PROGRESSION_SCENARIO] = progression_scenario_name

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send instantiate request to instantiation server %s." % (INSTANTIATION_SERVER_URL)
                if DEBUG:
                    print "* DEBUG: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(INSTANTIATION_SERVER_URL, query_params)
                data = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Instantiation server response body: %s" % (data)

                # Remove pending session
                self.removePendingSession(cyber_range_id)

                (status, message) = query.Response.parse_server_response(data)

                if DEBUG:
                    print "* DEBUG: trngsrv: Response status:", status
                    print "* DEBUG: trngsrv: Response message:", message

                if status == Storyboard.SERVER_STATUS_SUCCESS:
                    session_name = "Training Session #%s" % (cyber_range_id)
                    crt_time = time.asctime()
                    print "* INFO: trngsrv: Instantiation successful => save training session: %s (time: %s)." % (session_name, crt_time)

                    # Synchronize access to active sessions list
                    self.lock_active_sessions.acquire()
                    try:
                        # Read session info
                        session_info = sessinfo.SessionInfo()
                        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)

                        # Add new session and save to file
                        # Scenarios and levels should be given as arrays,
                        # so we convert values to arrays when passing arguments
                        session_info.add_session(session_name, cyber_range_id, user_id,
                                                 crt_time, ttype, [scenario], [level],
                                                 language, instance_count, activity_id)
                        session_info.write_YAML_file(ACTIVE_SESSIONS_FILE)
                    finally:
                        self.lock_active_sessions.release()
                else:
                    print "* ERROR: trngsrv: Range instantiation error."
                    self.respond_error(Storyboard.INSTANTIATION_ERROR)
                    return

                # Save the response data
                instsrv_response = data

                if DEBUG:
                    print "* DEBUG: trngsrv: contsrv response: %s" %(contsrv_response)
                    print "* DEBUG: trngsrv: instsrv response: %s" %(instsrv_response)

                # Prepare the response as a message
                # TODO: Should create a function to handle this
                if message:
                    response_data = '[{{"{0}": "{1}"}}]'.format(Storyboard.SERVER_MESSAGE_KEY, message)
                else:
                    response_data = None

            except IOError as error:
                print "* ERROR: trngsrv: URL error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.INSTANTIATION_SERVER_ERROR)
                return

        ####################################################################
        # Create training action
        # Note: Requires synchronized access to active sessions list
        elif action == query.Parameters.CREATE_TRAINING_Variation:

            if not instance_count:
                self.respond_error(Storyboard.INSTANCE_COUNT_MISSING_ERROR)
                return

            try:
                instance_count_value = int(instance_count)
            except ValueError as error:
                self.respond_error(Storyboard.INSTANCE_COUNT_INVALID_ERROR)
                return

            if not ttype:
                self.respond_error(Storyboard.TRAINING_TYPE_MISSING_ERROR)
                return

            if not scenario:
                self.respond_error(Storyboard.SCENARIO_NAME_MISSING_ERROR)
                return

            if not level:
                self.respond_error(Storyboard.LEVEL_NAME_MISSING_ERROR)
                return

            # Synchronize access to active sessions list and related variables
            self.lock_active_sessions.acquire()
            try:
                cyber_range_id = self.generate_cyber_range_id(self.pending_sessions)
                if cyber_range_id:
                    # Convert to string for internal representation
                    cyber_range_id = str(cyber_range_id)
                    self.pending_sessions.append(cyber_range_id)
                    print "* INFO: trngsrv: Allocated session with ID #%s." % (cyber_range_id)
                else:
                    self.respond_error(Storyboard.SESSION_ALLOCATION_ERROR)
                    return
            finally:
                self.lock_active_sessions.release()

            ########################################
            # Handle instantiation
            spec_file_name = training_info.get_range_file_name(scenario, level)
            if spec_file_name == None:
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.TEMPLATE_IDENTIFICATION_ERROR)
                return

            spec_file_name = DATABASE_DIR + spec_file_name

            if DEBUG:
                print "* DEBUG: trngsrv: Scenario specification file: %s" % (spec_file_name)

            # Open the specification file (template)
            try:
                spec_file = open(spec_file_name, "r")
                spec_file_content = spec_file.read()
                spec_file.close()

            except IOError as error:
                print "* ERROR: trngsrv: File error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.TEMPLATE_LOADING_ERROR)
                return

            # Do instantiation
            try:
                # Replace variables in the specification file
                spec_file_content = user_obj.replace_variables(spec_file_content, cyber_range_id, instance_count_value)

                # Note: creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.INSTANTIATE_RANGE,
                    query.Parameters.DESCRIPTION_FILE: spec_file_content,
                    query.Parameters.RANGE_ID: cyber_range_id
                }

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send instantiate request to instantiation server %s." % (INSTANTIATION_SERVER_URL)
                if DEBUG:
                    print "* DEBUG: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(INSTANTIATION_SERVER_URL, query_params)
                data=None
                data = data_stream.read()
                query_result = None
                query_result = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Instantiation server response body: %s" % (data)
                    print "* DEBUG: trngsrv: Instantiation server response query_result: %s" % (query_result)

                # Remove pending session
                self.removePendingSession(cyber_range_id)

                (status, message) = query.Response.parse_server_response(data)

                if DEBUG:
                    print "* DEBUG: trngsrv: Response status:", status
                    print "* DEBUG: trngsrv: Response message:", message

                if status == Storyboard.SERVER_STATUS_SUCCESS:
                    pass
                else:
                    print "* ERROR: trngsrv: Range instantiation error."
                    self.respond_error(Storyboard.INSTANTIATION_ERROR)
                    return

                # Save the response data
                instsrv_response = data

            except IOError as error:
                print "* ERROR: trngsrv: URL error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.INSTANTIATION_SERVER_ERROR)
                return
            ########################################
            # Handle GET_CR_CREATION_LOG
            try:
                # Note: creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.GET_CR_CREATION_LOG,
                    query.Parameters.RANGE_ID: cyber_range_id
                }

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send instantiate request to instantiation server %s." % (INSTANTIATION_SERVER_URL)
                if DEBUG:
                    print "* DEBUG: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(INSTANTIATION_SERVER_URL, query_params)
                query_result = None
                query_result = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Instantiation server response body: %s" % (query_result)

                #############################################################################
                # Start parse GET_CR_CREATION_LOG & store "exec-result:"
                # meta_answer_dic :
                # {1: [
                #       {'desktop,1,eth_ip': '1.1.1.2'},
                #       {'desktop,1,whoami': 'root'}
                #     ],
                # 2: [
                #       {'desktop,1,eth_ip': '1.2.1.2'},
                #       {'desktop,1,whoami': 'root'}
                #    ]
                # }
                #############################################################################
                creation_log_content = query_result
                if (creation_log_content[0]=="[" )& \
                        (creation_log_content[1]=="{" )& \
                        (creation_log_content[(len(creation_log_content)-2)]=="}" )& \
                        (creation_log_content[(len(creation_log_content)-1)]=="]"):
                    creation_log_content=creation_log_content[2:]
                    creation_log_content=creation_log_content[:-2]
                (status,creation_log_message)=creation_log_content.split(',')
                (tag,body)=creation_log_message.split(':')
                decode_mesage=urllib.unquote(body)
                decode_mesage=decode_mesage.split("\n")
                result_list=[]
                for lines in decode_mesage :
                    if 'exec-result:' in lines:
                        result_list.append(lines.replace("exec-result: ", ""))
                all_result = []
                for instnum,result in enumerate(result_list):
                    tag,ans = result.split()
                    ans=urllib.unquote(ans)
                    ans=ans.replace("\n", "")
                    ins,guest,num,var=tag.split(",")
                    ins_num=ins.replace("ins", "")
                    user_def = guest+','+num+','+var
                    all_result.append({int(ins_num):{user_def:ans}})
                meta_answer_dic={}
                for inst in all_result:
                    for i in inst:
                        try:
                            meta_answer_dic[i].append(inst[i])
                        except:
                            meta_answer_dic[i]=[inst[i]]
                #############################################################################
                # End parse GET_CR_CREATION_LOG & store "exec-result:"
                #############################################################################

            except IOError as error:
                print "* ERROR: trngsrv: File error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_LOADING_ERROR)
                return

            ########################################
            # Handle content upload
            content_file_name = training_info.get_content_file_name(scenario, level)
            if content_file_name == None:
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_IDENTIFICATION_ERROR)
                return

            content_file_name = DATABASE_DIR + content_file_name

            if DEBUG:
                print "* DEBUG: trngsrv: Training content file: %s" % (content_file_name)

            # Open the content file
            try:
                content_file = open(content_file_name, "r")
                content_file_content = content_file.read()
                content_file.close()

            except IOError as error:
                print "* ERROR: trngsrv: File error: %s." % (error)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_LOADING_ERROR)
                return

            #############################################################################
            # Loop for meta_answer
            #############################################################################
            # test code for New syntax as meta_answer by rive3
            try:
                for inst in range(instance_count_value):
                    meta_answers={}
                    for meta_answer_par_inst in meta_answer_dic[inst+1]:
                        meta_answers.update(meta_answer_par_inst)
                    content_template=Meta_answer_template(content_file_content)
                    if DEBUG:
                        print meta_answers
                    patched_content=content_template.safe_substitute(meta_answers)
                    content_list = yaml.load(patched_content)
                    try:
                        #change 2 dic type
                        for i in content_list:
                            if type(i) != dict:
                                logging.error("Incorrect format")
                            for j in i:
                                #top level tag (training)
                                for k in i[j]:
                                    # training section
                                    for quest in k["questions"]:
                                        # search keys
                                        for keys in list(quest):
                                            if(keys=="meta_answer"):
                                                try:
                                                    del quest["answer"]
                                                except:
                                                    pass
                                                finally:
                                                    quest["answer"]=quest["meta_answer"]
                                                del quest["meta_answer"]

                    except (IOError, yaml.YAMLError) as e:
                        logging.error("General error: " + str(e))
                        self.removePendingSession(cyber_range_id)
                        self.respond_error(Storyboard.INSTANTIATION_SERVER_ERROR)
                        return
                    content_file_description=yaml.dump(content_list, default_flow_style=False)
                    try:
                        # Note: creating a dictionary as below does not
                        # preserve the order of the parameters, but this has
                        # no negative influence in our implementation
                        query_tuples = {
                            query.Parameters.USER: user_id,
                            query.Parameters.ACTION: query.Parameters.UPLOAD_CONTENT,
                            query.Parameters.DESCRIPTION_FILE: content_file_description,
                            query.Parameters.RANGE_ID: cyber_range_id
                        }

                        query_params = urllib.urlencode(query_tuples)
                        print "* INFO: trngsrv: Send upload request to content server %s." % (CONTENT_SERVER_URL)
                        if DEBUG:
                            print "* DEBUG: trngsrv: POST parameters: %s" % (query_params)
                        data_stream = urllib.urlopen(CONTENT_SERVER_URL, query_params)
                        data = None
                        data = data_stream.read()
                        if DEBUG:
                            print "* DEBUG: trngsrv: Content server response body: %s" % (data)

                        (status, activity_id) = query.Response.parse_server_response(data)

                        if DEBUG:
                            print("* DEBUG: trngsrv: Response status: {}".format(status))
                            print("* DEBUG: trngsrv: Response activity_id: {}".format(activity_id))

                        if status == Storyboard.SERVER_STATUS_SUCCESS:
                            # Store activity id in session description
                            session_name = "Training Session #%s" % (cyber_range_id)
                            crt_time = time.asctime()
                            print "* INFO: trngsrv: Instantiation successful => save training session: %s (time: %s)." % (session_name, crt_time)

                            # Synchronize access to active sessions list
                            self.lock_active_sessions.acquire()
                            try:
                                # Read session info
                                session_info = sessinfo.SessionInfo()
                                session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)

                                # Add new session and save to file
                                # Scenarios and levels should be given as arrays,
                                # so we convert values to arrays when passing arguments
                                session_info.add_session(session_name, cyber_range_id, user_id,
                                                         crt_time, ttype, [scenario], [level],
                                                         language, instance_count, activity_id)
                                session_info.write_YAML_file(ACTIVE_SESSIONS_FILE)
                            finally:
                                self.lock_active_sessions.release()
                                #pass
                        else:
                            print "* ERROR: trngsrv: Content upload error."
                            self.removePendingSession(cyber_range_id)
                            self.respond_error(Storyboard.CONTENT_UPLOAD_ERROR)
                            return

                        # Save the response data
                        contsrv_response = data

                        if DEBUG:
                            print "* DEBUG: trngsrv: contsrv response: %s" %(contsrv_response)
                            print "* DEBUG: trngsrv: instsrv response: %s" %(instsrv_response)

                        # Prepare the response as a message
                        # TODO: Should create a function to handle this
                        if message:
                            response_data = '[{{"{0}": "{1}"}}]'.format(Storyboard.SERVER_MESSAGE_KEY, message)
                        else:
                            response_data = None

                    except IOError as error:
                        print "* ERROR: trngsrv: URL error: %s." % (error)
                        self.removePendingSession(cyber_range_id)
                        self.respond_error(Storyboard.CONTENT_SERVER_ERROR)
                        return
            except Exception as e:
                print "* ERROR: trngsrv: loop error: %s." % (e)
                self.removePendingSession(cyber_range_id)
                self.respond_error(Storyboard.CONTENT_SERVER_ERROR)
                return

        ####################################################################
        # Retrieve saved training configurations action
        # Note: Requires synchronized access to saved configurations list
        elif action == query.Parameters.GET_CONFIGURATIONS: 

            self.lock_saved_configurations.acquire()
            try:
                # Read session info
                session_info = sessinfo.SessionInfo()
                session_info.parse_YAML_file(SAVED_CONFIGURATIONS_FILE)

                # TODO: Catch error in operation above 
            finally:
                self.lock_saved_configurations.release()

            # Convert the training session info to the external JSON
            # representation that will be provided to the client
            response_data = session_info.get_JSON_representation(user_id)

        ####################################################################
        # Retrieve active training sessions action
        # Note: Requires synchronized access to active sessions list        
        elif action == query.Parameters.GET_SESSIONS: 

            self.lock_active_sessions.acquire()
            try:
                # Read session info
                session_info = sessinfo.SessionInfo()
                session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)

                # TODO: Catch error in operation above 
            finally:
                self.lock_active_sessions.release()

            # Convert the training session info to the external JSON
            # representation that will be provided to the client
            response_data = session_info.get_JSON_representation(user_id)

        ####################################################################
        # End training variation action
        # Note: Requires synchronized access to active sessions list
        elif action == query.Parameters.END_TRAINING_Variation:

            if not range_id:
                print "* ERROR: trngsrv: %s." % (Storyboard.SESSION_ID_MISSING_ERROR)
                self.respond_error(Storyboard.SESSION_ID_MISSING_ERROR)
                return
            activity_id = None
            self.lock_active_sessions.acquire()
            try:
                 activity_id = self.check_range_id_exists(range_id, user_id)
                 activity_id_list = self.check_range_id_and_activity_id_exists(range_id, user_id)
                 if not activity_id:
                     print "* ERROR: trngsrv: Session with ID "+ range_id + " doesn't exist for user " + user_id
                     error_msg = Storyboard.SESSION_ID_INVALID_ERROR + ": " + range_id
                     self.respond_error(error_msg)
                     return
            finally:
                self.lock_active_sessions.release()
                ########################################
            # Handle content removal
            for aclist in activity_id_list:
                try:
                    # Note: Creating a dictionary as below does not
                    # preserve the order of the parameters, but this has
                    # no negative influence in our implementation
                    query_tuples = {
                        query.Parameters.USER: user_id,
                        query.Parameters.ACTION: query.Parameters.REMOVE_CONTENT,
                        query.Parameters.RANGE_ID: range_id,
                        query.Parameters.ACTIVITY_ID: aclist
                    }

                    query_params = urllib.urlencode(query_tuples)
                    print "* INFO: trngsrv: Send removal request to content server %s." % (CONTENT_SERVER_URL)
                    print "* INFO: trngsrv: POST parameters: %s" % (query_params)
                    data_stream = urllib.urlopen(CONTENT_SERVER_URL, query_params)
                    data = data_stream.read()
                    if DEBUG:
                        print "* DEBUG: trngsrv: Content server response body: %s" % (data)

                    # We don't parse the response since the content server does not provide
                    # a uniformly formatted one; instead we only check for SUCCESS key
                    if Storyboard.SERVER_STATUS_SUCCESS in data:
                        # Nothing to do on success as there is no additional info provided
                        pass
                    else:
                        print "* ERROR: trngsrv: Content removal error."
                        self.respond_error(Storyboard.CONTENT_REMOVAL_ERROR)
                        return

                    # Save the response data
                    contsrv_response = data

                except IOError as error:
                    print "* ERROR: trngsrv: URL error: %s." % (error)
                    self.respond_error(Storyboard.CONTENT_SERVER_ERROR)
                    return

            ########################################
            # Handle range destruction
            try:
                # Note: creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.DESTROY_RANGE,
                    query.Parameters.RANGE_ID: range_id
                }

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send destroy request to instantiation server %s." % (INSTANTIATION_SERVER_URL)
                print "* INFO: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(INSTANTIATION_SERVER_URL, query_params)
                data = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Instantiation server response body: %s" % (data)

                (status, message) = query.Response.parse_server_response(data)

                if status == Storyboard.SERVER_STATUS_SUCCESS:

                    self.lock_active_sessions.acquire()
                    try:
                        # Read session info
                        session_info = sessinfo.SessionInfo()
                        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)
                        for ac in activity_id_list:
                            # Remove session and save to file
                            if not session_info.remove_session_variation(range_id, user_id,ac):
                                print "* ERROR: Cannot remove training session %s." % (range_id)
                                self.respond_error(Storyboard.SESSION_INFO_CONSISTENCY_ERROR)
                                return
                            else:
                                session_info.write_YAML_file(ACTIVE_SESSIONS_FILE)
                    finally:
                        self.lock_active_sessions.release()

                else:
                    print "* ERROR: trngsrv: Range destruction error: %s." % (message)
                    self.respond_error(Storyboard.DESTRUCTION_ERROR)
                    return

                instsrv_response = data

                if DEBUG:
                    print "* DEBUG: trngsrv: contsrv response: %s" %(contsrv_response)
                    print "* DEBUG: trngsrv: instsrv response: %s" %(instsrv_response)

                # Prepare the response: no data needs to be returned,
                # hence we set the content to None
                response_data = None

            except IOError as error:
                print "* ERROR: trngsrv: URL error: %s." % (error)
                self.respond_error(Storyboard.INSTANTIATION_SERVER_ERROR)
                return
        ####################################################################
        # End training action
        # Note: Requires synchronized access to active sessions list        
        elif action == query.Parameters.END_TRAINING:

            if not range_id:
                print "* ERROR: trngsrv: %s." % (Storyboard.SESSION_ID_MISSING_ERROR)
                self.respond_error(Storyboard.SESSION_ID_MISSING_ERROR)
                return

            activity_id = None
            self.lock_active_sessions.acquire()
            try:
                activity_id = self.check_range_id_exists(range_id, user_id)
                if not activity_id:
                    print "* ERROR: trngsrv: Session with ID "+ range_id + " doesn't exist for user " + user_id
                    error_msg = Storyboard.SESSION_ID_INVALID_ERROR + ": " + range_id
                    self.respond_error(error_msg)
                    return
            finally:
                self.lock_active_sessions.release()


            ########################################
            # Handle content removal
            try:
                # Note: Creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.REMOVE_CONTENT,
                    query.Parameters.RANGE_ID: range_id,
                    query.Parameters.ACTIVITY_ID: activity_id
                }

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send removal request to content server %s." % (CONTENT_SERVER_URL) 
                print "* INFO: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(CONTENT_SERVER_URL, query_params)
                data = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Content server response body: %s" % (data)

                # We don't parse the response since the content server does not provide
                # a uniformly formatted one; instead we only check for SUCCESS key
                if Storyboard.SERVER_STATUS_SUCCESS in data:
                    # Nothing to do on success as there is no additional info provided
                    pass
                else:
                    print "* ERROR: trngsrv: Content removal error."
                    self.respond_error(Storyboard.CONTENT_REMOVAL_ERROR)
                    return

                # Save the response data
                contsrv_response = data

            except IOError as error:
                print "* ERROR: trngsrv: URL error: %s." % (error)
                self.respond_error(Storyboard.CONTENT_SERVER_ERROR)
                return

            ########################################
            # Handle range destruction
            try:
                # Note: creating a dictionary as below does not
                # preserve the order of the parameters, but this has
                # no negative influence in our implementation
                query_tuples = {
                    query.Parameters.USER: user_id,
                    query.Parameters.ACTION: query.Parameters.DESTROY_RANGE,
                    query.Parameters.RANGE_ID: range_id
                }

                query_params = urllib.urlencode(query_tuples)
                print "* INFO: trngsrv: Send destroy request to instantiation server %s." % (INSTANTIATION_SERVER_URL) 
                print "* INFO: trngsrv: POST parameters: %s" % (query_params)
                data_stream = urllib.urlopen(INSTANTIATION_SERVER_URL, query_params)
                data = data_stream.read()
                if DEBUG:
                    print "* DEBUG: trngsrv: Instantiation server response body: %s" % (data)

                (status, message) = query.Response.parse_server_response(data)

                if status == Storyboard.SERVER_STATUS_SUCCESS:

                    self.lock_active_sessions.acquire()
                    try:
                        # Read session info
                        session_info = sessinfo.SessionInfo()
                        session_info.parse_YAML_file(ACTIVE_SESSIONS_FILE)

                        # Remove session and save to file
                        if not session_info.remove_session(range_id, user_id):
                            print "* ERROR: Cannot remove training session %s." % (range_id)
                            self.respond_error(Storyboard.SESSION_INFO_CONSISTENCY_ERROR)
                            return
                        else:
                            session_info.write_YAML_file(ACTIVE_SESSIONS_FILE)
                    finally:
                        self.lock_active_sessions.release()

                else:
                    print "* ERROR: trngsrv: Range destruction error: %s." % (message)
                    self.respond_error(Storyboard.DESTRUCTION_ERROR)
                    return

                instsrv_response = data

                if DEBUG:
                    print "* DEBUG: trngsrv: contsrv response: %s" %(contsrv_response)
                    print "* DEBUG: trngsrv: instsrv response: %s" %(instsrv_response)

                # Prepare the response: no data needs to be returned,
                # hence we set the content to None
                response_data = None

            except IOError as error:
                print "* ERROR: trngsrv: URL error: %s." % (error)
                self.respond_error(Storyboard.INSTANTIATION_SERVER_ERROR)
                return

        ####################################################################
        # Catch unknown actions
        else:
            print "* WARNING: trngsrv: Unknown action: %s." % (action)

        # Emulate communication delay
        if EMULATE_DELAY:
            sleep_time = random.randint(2,5)
            print "* INFO: trngsrv: Simulate communication by sleeping %d s." % (sleep_time)
            time.sleep(sleep_time)

        # Respond to requester with SUCCESS
        self.respond_success(response_data)

    def removePendingSession(self, cyber_range_id):
        # Synchronize access to active sessions list related variable
        self.lock_active_sessions.acquire()
        try:
            self.pending_sessions.remove(cyber_range_id)
        finally:
            self.lock_active_sessions.release()

    # Respond to requester that operation was successful
    def respond_success(self, response_data):

        # Send response header to requester (triggers log_message())
        self.send_response(HTTP_STATUS_OK)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # Prepare success status
        response_status = '"{0}": "{1}"'.format(Storyboard.SERVER_STATUS_KEY, Storyboard.SERVER_STATUS_SUCCESS)

        # If response data exists, we prepend the success status to dictionary,
        # otherwise we make a dictionary containing only the status
        if response_data:
            # NOTE: We assume the response data is an array containing
            # a dictionary, hence of the form '[{"key": "value"...}]';
            # in order to merge it with the response status, we must
            # skip the first 2 characters
            response_body = '[{' + response_status + ", " + response_data[2:]
        else:
            response_body = '[{' + response_status + '}]'

        # Send response to requester
        self.wfile.write(response_body)

        # Output server response body
        print "* INFO: trngsrv: Server response body: %s" % (response_body)
        print Storyboard.SEPARATOR2

    # Respond to requester that operation encountered an error
    def respond_error(self, message):

        # Send response header to requester (triggers log_message())
        # Note: Error information is included in standard successful responses
        self.send_response(HTTP_STATUS_OK)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # Prepare error status
        response_status = '"{0}": "{1}"'.format(Storyboard.SERVER_STATUS_KEY, Storyboard.SERVER_STATUS_ERROR)

        # If a message exists, we append it to the error status,
        # otherwise we make a dictionary containing only the status
        if message:
            response_message = '"message": "' + message + '"'
            response_body = '[{' + response_status + ", " + response_message + '}]'
        else:
            response_body = '[{' + response_status + '}]'

        # Send response to requester
        self.wfile.write(response_body)

        # Output server response body
        print "* INFO: trngsrv: Server response body: %s" % (response_body)
        print Storyboard.SEPARATOR2

    #########################################################################
    # POST request to another server (the instantiation server)
    #def post_request():
    #    # Initialize variables
    #    POST_parameters = None


# Print usage information
def usage():
    print "OVERVIEW: CyTrONE training server that manages the content and instantiation servers.\n"
    print "USAGE: trngsrv.py [options]\n"

    print "OPTIONS:"
    print "-h, --help         Display help\n"


# Use threads to handle multiple clients
# Note: By using ForkingMixIn instead of ThreadingMixIn,
# separate processes are used instead of threads
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


#############################################################################
# Main program
#############################################################################
def main(argv):

    print Storyboard.SEPARATOR3
    print "CyTrONE v%s: Integrated cybersecurity training framework" % (CYTRONE_VERSION)
    print Storyboard.SEPARATOR3

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(argv, "h", ["help"])
    except getopt.GetoptError as err:
        print "* ERROR: trngsrv: Command-line argument error: %s" % (str(err))
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()

    try:

        # Configure the web server
        if LOCAL_SERVER:
            server_address = LOCAL_ADDRESS
        else:
            server_address=""
        server_port = SERVER_PORT

        multi_threading = ""
        if ENABLE_THREADS:
            server = ThreadedHTTPServer((server_address, server_port),
                                        RequestHandler)
            multi_threading = " (multi-threading mode)"
        else:
            server = HTTPServer((server_address, server_port), RequestHandler)

        # Use SSL socket if HTTPS is enabled
        if Storyboard.ENABLE_HTTPS:
            print("* INFO: trngsrv: HTTPS is enabled => set up SSL socket")
            if os.path.isfile(Storyboard.SSL_keyfile):
                key = Storyboard.SSL_keyfile
                print("* INFO: trngsrv: use keyfile => "+key)
            if os.path.isfile(Storyboard.SSL_certfile):
                crt = Storyboard.SSL_certfile
                print("* INFO: trngsrv: use certfile => "+crt)
            if Storyboard.SSL_ca_certs is not None:
                if os.path.isfile(Storyboard.SSL_ca_certs):
                    ca_certs=Storyboard.SSL_ca_certs
            else:
                ca_certs = None
            try:
                server.socket = ssl.wrap_socket (server.socket, keyfile=key, certfile=crt, ca_certs=ca_certs, server_side=True)
            except:
                print("* INFO: trngsrv: can't use keyfile , certfile , ca_certs => try to use default keyfile , certfile")
                try:
                    server.socket = ssl.wrap_socket (server.socket, keyfile="cytrone.key", certfile="cytrone.crt", ca_certs=None, server_side=True)
                except:
                    print("* INFO: trngsrv: can't set up SSL socket => set up SSL disable")
                    Storyboard.ENABLE_HTTPS = False
            finally:
                print("* INFO: trngsrv: set up for HTTP server done")


        # Start web server
        print "* INFO: trngsrv: CyTrONE training server listens on %s:%d%s." % (
            server_address, server_port, multi_threading)
        if SERVE_FOREVER:
            server.serve_forever()
        else:
            server.handle_request()

    # Deal with keyboard interrupts
    except KeyboardInterrupt:
        print '* INFO: trngsrv: Interrupted via ^C => shut down server.'
        server.socket.close()

    print "* INFO: trngsrv: CyTrONE training server ended execution."

#############################################################################
# Meta_answer_template
class Meta_answer_template(Template):
    idpattern=r'[_a-zA-Z,][_a-zA-Z0-9,]*'
#############################################################################
# Run server
if __name__ == "__main__":
    main(sys.argv[1:])
