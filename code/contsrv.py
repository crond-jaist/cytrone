#!/usr/bin/python

#############################################################################
# Classes related to the CyTrONE content upload server operation
#############################################################################

# External imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import time
import random
import subprocess
import os
import sys
import getopt
from SocketServer import ThreadingMixIn

# Internal imports
import userinfo
import query
from storyboard import Storyboard

#############################################################################
# Constants
#############################################################################

# Web server constants
LOCAL_ADDRESS = "127.0.0.1"
SERVER_PORT   = 8084
SUCCESS_CODE  = 200
REQUEST_ERROR = 404
SERVER_ERROR  = 500
LOCAL_SERVER  = True
SERVE_FOREVER = True # Use serve count if not using local server?!
RESPONSE_SUCCESS = '[{"' + Storyboard.SERVER_STATUS_KEY + '": "' + Storyboard.SERVER_STATUS_SUCCESS + '"}]'
RESPONSE_SUCCESS_ID_PREFIX = '[{"' + Storyboard.SERVER_STATUS_KEY + '": "' + Storyboard.SERVER_STATUS_SUCCESS \
                             + '", "' + Storyboard.SERVER_ACTIVITY_ID_KEY + '": "'
RESPONSE_SUCCESS_ID_SUFFIX = '"}]'
RESPONSE_ERROR = '[{"' + Storyboard.SERVER_STATUS_KEY + '": "' + Storyboard.SERVER_STATUS_ERROR + '"}]'
ENABLE_THREADS = True

# Names of files containing training-related information
USERS_FILE  = "users.yml"

# Other constants
SEPARATOR = "-----------------------------------------------------------------"
DATABASE_DIR = "../database/"
CONTENT_DESCRIPTION_TEMPLATE = "tmp_content_description-{}.yml"
DEFAULT_CYLMS_PATH = "/home/cyuser/cylms/"
DEFAULT_CYLMS_CONFIG = "/home/cyuser/cytrone/moodle/cylms_config"
CYLMS_PATH = ""
CYLMS_CONFIG = ""

SIMULATION_DURATION = -1 # Use -1 for random delay, positive value for fixed delay
SIMULATION_RAND_MIN = 1 # Minimum limit for the random delay range
SIMULATION_RAND_MAX = 3 # Maximum limit for the random delay range

# Debugging constants
DO_DEBUG = False
USE_MOODLE = True

#############################################################################
# Manage the content server functionality
#############################################################################
class RequestHandler(BaseHTTPRequestHandler):

    # List of valid actions recognized by this server
    VALID_ACTIONS = [query.Parameters.UPLOAD_CONTENT,
                     query.Parameters.REMOVE_CONTENT]

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
        activity_id = params.get(query.Parameters.ACTIVITY_ID)

        if DO_DEBUG:
            print SEPARATOR
            print "PARAMETERS:"
            print SEPARATOR
            print "USER: %s" % (user_id)
            print "ACTION: %s" % (action)
            print "DESCRIPTION FILE:\n%s" % (description_file) 
            print "RANGE_ID: %s" % (range_id)
            print "ACTIVITY_ID: %s" % (activity_id)
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
            except IOError as error:
                print("* ERROR: contsrv: Could not write to file {}: {}".format(content_file_name, error))

            print "* INFO: contsrv: Start LMS content upload."

            # Use Moodle to really do the content upload
            if USE_MOODLE:
                try:
                    # ./cylms.py --convert-content training_example.yml --config-file config_example --add-to-lms 1
                    try:
                        add_output = subprocess.check_output(
                            ["python", "-u", CYLMS_PATH + "cylms.py", "--convert-content", content_file_name,
                             "--config-file", CYLMS_CONFIG, "--add-to-lms", range_id], stderr=subprocess.STDOUT)
                        # Find the activity id
                        activity_id = None
                        for output_line in add_output.splitlines():
                            print(output_line)
                            # Extract the course id
                            activity_id_tag = "activity_id="
                            if activity_id_tag in output_line:
                                # Split line of form ...to LMS successfully => activity_id=101
                                activity_id = output_line.split(activity_id_tag)[1]
                                if DO_DEBUG: print("* DEBUG: contsrv: Extracted activity id from command output: {}".format(activity_id))
                                response_content = RESPONSE_SUCCESS_ID_PREFIX + activity_id + RESPONSE_SUCCESS_ID_SUFFIX

                        # Check whether the activity id was extracted
                        if not activity_id:
                            self.send_error(SERVER_ERROR, "LMS upload issue")
                            return
                    except subprocess.CalledProcessError as error:
                        print("* ERROR: contsrv: Error message: {}".format(error.output)) 
                        self.send_error(SERVER_ERROR, "CyLMS execution issue")
                        return
                    
                except IOError:
                    self.send_error(SERVER_ERROR, "LMS upload I/O error")
                    return

            # Don't use Moodle, just simulate the content upload
            else:
                # Simulate time needed to instantiate the cyber range
                if SIMULATION_DURATION == -1:
                    sleep_time = random.randint(SIMULATION_RAND_MIN, SIMULATION_RAND_MAX)
                else:
                    sleep_time = SIMULATION_DURATION
                print Storyboard.SEPARATOR3
                print "* INFO: contsrv: Simulate upload by sleeping %d s." % (sleep_time)
                print Storyboard.SEPARATOR3
                time.sleep(sleep_time)

                # Simulate the success or failure of the upload
                random_number = random.random()
                if random_number > 0.0:
                    # In case of success, we need to set the activity id to some 'harmless' value
                    activity_id = "N/A"
                    response_content = RESPONSE_SUCCESS_ID_PREFIX + activity_id + RESPONSE_SUCCESS_ID_SUFFIX
                else:
                    response_content = RESPONSE_ERROR

        elif action == query.Parameters.REMOVE_CONTENT: 

            print "* INFO: contsrv: Start LMS content removal."

            # Check that range_id is not empty
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return

            # Check that activity_id is not empty
            if not activity_id:
                self.send_error(REQUEST_ERROR, "Invalid LMS activity id")
                return

            # Use Moodle to really do the content removal
            if USE_MOODLE:
                try:
                    # ./cylms.py --config-file config_example --remove-from-lms 1,ID
                    config_arg = " --config-file {}".format(CYLMS_CONFIG)
                    remove_arg = " --remove-from-lms {},{}".format(range_id, activity_id)
                    command = "python -u " + CYLMS_PATH + "cylms.py" + config_arg + remove_arg
                    if DO_DEBUG: print("* DEBUG: contsrv: command: " + command)
                    return_value = os.system(command)
                    exit_status = os.WEXITSTATUS(return_value)
                    if exit_status == 0:
                        response_content = RESPONSE_SUCCESS
                    else:
                        self.send_error(SERVER_ERROR, "LMS content removal issue")
                        return
                except IOError:
                    self.send_error(SERVER_ERROR, "LMS content removal I/O error")
                    return

            # Don't use Moodle, just simulate the content removal
            else:
                # Simulate time needed to instantiate the cyber range
                if SIMULATION_DURATION == -1:
                    sleep_time = random.randint(SIMULATION_RAND_MIN, SIMULATION_RAND_MAX)
                else:
                    sleep_time = SIMULATION_DURATION
                print Storyboard.SEPARATOR3
                print "* INFO: contsrv: Simulate removal by sleeping %d s." % (sleep_time)
                print Storyboard.SEPARATOR3
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
    print "OVERVIEW: CyTrONE content server that manages LMS training support via CyLMS.\n"
    print "USAGE: contsrv.py [options]\n"
    print "OPTIONS:"
    print "-h, --help           Display help"
    print "-n, --no-lms         Disable LMS use => only simulate actions"
    print "-p, --path <PATH>    Set the location where CyLMS is installed"
    print "-c, --config <FILE>  Set configuration file for LMS operations\n"

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
    global CYLMS_PATH
    global CYLMS_CONFIG

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(argv, "hnp:c:", ["help", "no-lms", "path=", "config="])
    except getopt.GetoptError as err:
        print "* ERROR: contsrv: Command-line argument error: %s" % (str(err))
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-n", "--no-lms"):
            USE_MOODLE = False;
        elif opt in ("-p", "--path"):
            CYLMS_PATH = arg
        elif opt in ("-c", "--config"):
            CYLMS_CONFIG = arg

    # Assign default value if necessary
    if not CYLMS_PATH:
        CYLMS_PATH = DEFAULT_CYLMS_PATH
    # Append '/' to path if it does not exist
    if not CYLMS_PATH.endswith("/"):
        CYLMS_PATH += "/"

    # Assign default value if necessary
    if not CYLMS_CONFIG:
        CYLMS_CONFIG = DEFAULT_CYLMS_CONFIG

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
        print "* INFO: contsrv: CyTrONE content server listens on %s:%d%s." % (
            server_address, server_port, multi_threading)
        if not USE_MOODLE:
            print "* INFO: contsrv: LMS use is disabled => only simulate actions."
        else:
            print "* INFO: contsrv: Using CyLMS software installed in %s." % (CYLMS_PATH)
            print "* INFO: contsrv: Using CyLMS configuration file %s." % (CYLMS_CONFIG)

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
