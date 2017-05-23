#!/usr/bin/python

#############################################################################
# Classes related to the CyTrONE content upload server operation
#############################################################################

# External imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#import urlparse
import time
import random
#import subprocess
import os
import sys
import getopt
from SocketServer import ThreadingMixIn
#import threading

# Internal imports
import userinfo
import query

#############################################################################
# Constants
#############################################################################

# Web server constants
LOCAL_ADDRESS = "127.0.0.1"
SERVER_PORT   = 8084
SUCCESS_CODE  = 200
REQUEST_ERROR = 404
SERVER_ERROR  = 500
LOCAL_SERVER  = False
SERVE_FOREVER = True # Use serve count if not using local server?!
RESPONSE_SUCCESS = '[{"status": "SUCCESS"}]'
RESPONSE_ERROR = '[{"status": "ERROR"}]'
ENABLE_THREADS = True

# Names of files containing training-related information
USERS_FILE  = "users.yml"

# Other constants
SEPARATOR = "-----------------------------------------------------------------"
DATABASE_DIR = "../database/"
CONTENT_DESCRIPTION_TEMPLATE = "tmp_content_description-{}.yml"
DEFAULT_CNT2LMS_PATH = "/home/cyuser/moodle/cnt2lms/"
DEFAULT_SETTINGS_PATH = "/home/cyuser/moodle/settings/"
CNT2LMS_PATH = ""
SETTINGS_PATH = ""
SIMULATION_DURATION = -1 # use -1 for random interval, positive value for fixed interval

# Debugging constants
DO_DEBUG = False
USE_MOODLE = True

#############################################################################
# Manage the content server functionality
#############################################################################
class RequestHandler(BaseHTTPRequestHandler):

    # List of valid actions recognized by this server
    VALID_ACTIONS = [query.Parameters.UPLOAD_CONTENT,
                     query.Parameters.RESET_CONTENT]

    #########################################################################
    # Print log messages with custom format
    # Default format is shown below:
    #     127.0.0.1 - - [22/Jun/2016 14:47:56] "POST / HTTP/1.0" 200 -
    def log_message(self, format, *args):
        (client_host, client_port) = self.client_address
        print("* INFO: contsrv: Server response to client %s - - [%s] %s" %
              (client_host, self.log_date_time_string(), format%args))

    #########################################################################
    # Handle a POST message
    def do_POST(self):

        # Get the parameters of the POST request
        params = query.Parameters(self)

        if DO_DEBUG:
            print SEPARATOR
            print "* INFO: contsrv: Request to content server: POST parameters: %s" % (params)

        # Get parameter values for given keys
        user_id = params.get(query.Parameters.USER)
        action = params.get(query.Parameters.ACTION)
        description_file = params.get(query.Parameters.DESCRIPTION_FILE)
        range_id = params.get(query.Parameters.RANGE_ID)

        if DO_DEBUG:
            print SEPARATOR
            print "PARAMETERS:"
            print SEPARATOR
            print "USER: %s" % (user_id)
            print "ACTION: %s" % (action)
            print "DESCRIPTION FILE:\n%s" % (description_file) 
            print "RANGE_ID: %s" % (range_id)
            print SEPARATOR

            
        ## Handle user information
        
        # Get user information from YAML file
        # Note: Only reading data that is (potentially) modified externally =>
        #       no need for synchronization

        user_info = userinfo.UserInfo()
        if not user_info.parse_YAML_file(DATABASE_DIR + USERS_FILE):
            self.send_error(SERVER_ERROR, "User information issue")
            return
        if DO_DEBUG:
            user_info.pretty_print()

        # Check that user id is valid
        user_obj = user_info.get_user(user_id) 
        if not user_obj:
            self.send_error(REQUEST_ERROR, "Invalid user id")
            return

        
        ## Handle action information

        # Check that action is valid
        if action not in self.VALID_ACTIONS:
            self.send_error(REQUEST_ERROR, "Invalid action")
            return

        # If we reached this point, it means processing was successful
        # => act according to each action
        if action == query.Parameters.UPLOAD_CONTENT: 

            # Check that description is not empty
            if not description_file:
                self.send_error(REQUEST_ERROR, "Invalid description file")
                return

            # Save the description received as a file
            try:
                content_file_name = CONTENT_DESCRIPTION_TEMPLATE.format(range_id)
                content_file = open(content_file_name, "w")
                content_file.write(description_file)
                content_file.close()
                print "* INFO: contsrv: Saved POSTed content description to file '%s'." % (content_file_name)
            except IOError:
                print "* ERROR: contsrv: Could not write to file %s." % (content_file_name)

            print "* INFO: contsrv: Start LMS content upload."

            # Use Moodle to really do the content upload
            if USE_MOODLE:
                try:
                    command = "python -u " + CNT2LMS_PATH + "cnt2lms.py " + SETTINGS_PATH + "moodle_config-upload" + range_id
                    return_value = os.system(command)
                    exit_status = os.WEXITSTATUS(return_value)
                    if exit_status == 0:
                        response_content = RESPONSE_SUCCESS
                    else:
                        self.send_error(SERVER_ERROR, "LMS upload issue")
                        return
                except IOError:
                    self.send_error(SERVER_ERROR, "LMS upload I/O error")
                    return
            
            # Don't use Moodle, just simulate the content upload
            else:
                # Simulate time needed to instantiate the cyber range
                if SIMULATION_DURATION == -1:
                    sleep_time = random.randint(2,5)
                else:
                    sleep_time = SIMULATION_DURATION
                print "* INFO: contsrv: Simulate upload by sleeping %d s." % (sleep_time)
                time.sleep(sleep_time)

                # Simulate the success or failure of the upload
                random_number = random.random()
                if random_number > 0.0:
                    response_content = RESPONSE_SUCCESS
                else:
                    response_content = RESPONSE_ERROR

        elif action == query.Parameters.RESET_CONTENT: 

            print "* INFO: contsrv: Start LMS content reset."
            
            # Use Moodle to really do the content reset
            if USE_MOODLE:
                try:
                    command = "python -u " + CNT2LMS_PATH + "copyToMoodle.py " + SETTINGS_PATH + "moodle_config-reset" + range_id
                    return_value = os.system(command)
                    exit_status = os.WEXITSTATUS(return_value)
                    if exit_status == 0:
                        response_content = RESPONSE_SUCCESS
                    else:
                        self.send_error(SERVER_ERROR, "LMS reset issue")
                        return
                except IOError:
                    self.send_error(SERVER_ERROR, "LMS reset I/O error")
                    return
            
            # Don't use Moodle, just simulate the content reset
            else:
                # Simulate time needed to instantiate the cyber range
                if SIMULATION_DURATION == -1:
                    sleep_time = random.randint(2,5)
                else:
                    sleep_time = SIMULATION_DURATION
                print "* INFO: contsrv: Simulate reset by sleeping %d s." % (sleep_time)
                time.sleep(sleep_time)

                # Simulate the success or failure of the upload
                random_number = random.random()
                if random_number > 0.0:
                    response_content = RESPONSE_SUCCESS
                else:
                    response_content = RESPONSE_ERROR

        # Catch potential unimplemented actions (if any)
        else:
            print "* WARNING: contsrv: Unknown action: %s." % (action)

        # Send response header to requester (triggers log_message())
        self.send_response(SUCCESS_CODE)
        self.send_header("Content-type", "text/html")
        self.end_headers() 
           
        # Send scenario database content information to requester
        self.wfile.write(response_content)

        # Output server reply
        print "* INFO: contsrv: Server response content: %s" % (response_content)

        
# Print usage information
def usage():
    print "OVERVIEW: CyTrONE content server that manages the cnt2lms training content to LMS converter.\n"
    print "USAGE: contsrv.py [options]\n"
    print "OPTIONS:"
    print "-h, --help             Display help"
    print "-n, --no-lms           Disable LMS use => only simulate actions"
    print "-p, --path <PATH>      The location where cnt2lms software is installed"
    print "-s, --settings <PATH>  The location where cnt2lms settings are placed\n"

# Use threads to handle multiple clients
# Note: By using ForkingMixIn instead of ThreadingMixIn,
# separate processes are used instead of threads
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


#############################################################################
# Main program
#############################################################################
def main(argv):

    global USE_MOODLE
    global CNT2LMS_PATH
    global SETTINGS_PATH
    
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(argv, "hnp:s:", ["help", "no-lms", "path=", "settings="])
    except getopt.GetoptError as err:
        print "* ERROR: contsrv: Command-line argument error: %s" % (str(err))
        usage()
        sys.exit(-1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-n", "--no-lms"):
            USE_MOODLE = False;
        elif opt in ("-p", "--path"):
            CNT2LMS_PATH = arg
        elif opt in ("-s", "--settings"):
            SETTINGS_PATH = arg

    # Assign default value if necessary
    if not CNT2LMS_PATH:
        CNT2LMS_PATH = DEFAULT_CNT2LMS_PATH
    # Append '/' to path if it does not exist
    if not CNT2LMS_PATH.endswith("/"):
        CNT2LMS_PATH += "/"

    # Assign default value if necessary
    if not SETTINGS_PATH:
        SETTINGS_PATH = DEFAULT_SETTINGS_PATH
    # Append '/' to path if it does not exist
    if not SETTINGS_PATH.endswith("/"):
        SETTINGS_PATH += "/"

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
            
        # Start the web server
        print "* INFO: contsrv: CyTrONE content server started on %s:%d%s." % (
            server_address, server_port, multi_threading)
        if not USE_MOODLE:
            print "* INFO: contsrv: LMS use is disabled => only simulate actions."
        else:
            print "* INFO: contsrv: Using cnt2lms software installed in %s." % (CNT2LMS_PATH)
            print "* INFO: contsrv: Using cnt2lms settings located in %s." % (SETTINGS_PATH)
            
        if SERVE_FOREVER:
            server.serve_forever()
        else:
            server.handle_request()

    # Catch socket errors
    except IOError:
        print "* ERROR: contsrv: CyTrONE content server: HTTPServer error (server may be running already)."
    
    # Deal with keyboard interrupts
    except KeyboardInterrupt:
        print "* INFO: contsrv: Interrupted via ^C => shut down server."
        server.socket.close()

    print "* INFO: contsrv: CyTrONE content server ended execution."


#############################################################################
# Run server
if __name__ == "__main__":
    main(sys.argv[1:])
