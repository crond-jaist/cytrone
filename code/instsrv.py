#!/usr/bin/python

#############################################################################
# Classes related to the CyTrONE cyber range instantiation server operation
#############################################################################

# External imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import time
import random
import os
import sys
import getopt
from SocketServer import ThreadingMixIn
import urllib

# Internal imports
import userinfo
import query
from storyboard import Storyboard

#############################################################################
# Constants
#############################################################################

# Web server constants
LOCAL_ADDRESS = "127.0.0.1"
SERVER_PORT   = 8083
HTTP_OK_CODE  = 200
REQUEST_ERROR = 404
SERVER_ERROR  = 500
LOCAL_SERVER  = True
SERVE_FOREVER = True # Use serve count if not using local server?!
ENABLE_THREADS = True

# Names of files containing training-related information
USERS_FILE  = "users.yml"

# Internal constants
SEPARATOR = "-----------------------------------------------------------------"
DATABASE_DIR = "../database/"
RANGE_DESCRIPTION_TEMPLATE = "tmp_range_description-{0}.yml"

# CyRIS related constants
DEFAULT_CYRIS_PATH = "/home/cyuser/cyris/"
CYRIS_PATH = ""
CYRIS_RANGE_DIRECTORY = "cyber_range/" # TODO: This should also be provided as an argument
CYRIS_STATUS_FILENAME = "cr_creation_status"
CYRIS_NOTIFICATION_TEMPLATE = "range_notification-cr{0}.txt"
CYRIS_NOTIFICATION_SIMULATED = "range_notification-simulated.txt"
CYRIS_DETAILS_TEMPLATE = "range_details-cr{0}.yml"
CYRIS_ENTRY_POINT_TEMPLATE = "entry_points.txt"
CYRIS_CREATION_STATUS_TEMPLATE = "cr_creation_status"
CYRIS_INITIF_TEMPLATE = "initif.conf"
CYRIS_CREATION_LOG_TEMPLATE = "creation.log"
#CYRIS_DESTRUCTION_SCRIPT = "whole-controlled-destruction.sh"
CYRIS_DESTRUCTION_SCRIPT = "main/range_cleanup.py"
CYRIS_CONFIG_FILENAME = "CONFIG"

# CyPROM related constants
DEFAULT_CYPROM_PATH = "/home/cyuser/cyprom/"
CYPROM_PATH = ""

SIMULATION_DURATION = -1 # Use -1 for random delay, positive value for fixed delay
SIMULATION_RAND_MIN = 1 # Minimum limit for the random delay range
SIMULATION_RAND_MAX = 3 # Maximum limit for the random delay range

# Debugging constants
DEBUG = False
USE_CYRIS = True

# Temporary solution until a better way is implemented for generating scripts
# to connect to cyber range based on the output of CyRIS
# NOTE: Script generation functionality is not currently supported, so don't
#       enable it unless you know what you are doing
USE_CNT2LMS_SCRIPT_GENERATION = False
CYRIS_MASTER_HOST = "172.16.1.7"
CYRIS_MASTER_ACCOUNT = "cyuser"
CNT2LMS_PATH = "/home/cyuser/cylms/"


#############################################################################
# Manage the instantiation server functionality
#############################################################################
class RequestHandler(BaseHTTPRequestHandler):

    # List of valid actions recognized by this server
    VALID_ACTIONS = [query.Parameters.INSTANTIATE_RANGE,
                     query.Parameters.DESTROY_RANGE,
                     query.Parameters.GET_CR_NOTIFICATION,
                     query.Parameters.GET_CR_DETAILS,
                     query.Parameters.GET_CR_ENTRY_POINT,
                     query.Parameters.GET_CR_CREATION_STATUS,
                     query.Parameters.GET_CR_INITIF,
                     query.Parameters.GET_CR_CREATION_LOG]

    #########################################################################
    # Print log messages with custom format
    # Default format is shown below:
    #     127.0.0.1 - - [22/Jun/2016 14:47:56] "POST / HTTP/1.0" 200 -
    def log_message(self, format, *args):
        (client_host, client_port) = self.client_address
        print("* INFO: instsrv: Server response to client %s - - [%s] %s" %
              (client_host, self.log_date_time_string(), format%args))

    #########################################################################
    # Execute shell commands
    #def execute_command(self, command):
    #    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #    with open("log.txt", "a") as myfile:
    #        for line in p.stdout.readlines():
    #            myfile.write(line)

    #########################################################################
    # Handle a POST message
    def do_POST(self):

        # Get the parameters of the POST request
        params = query.Parameters(self)

        if DEBUG:
            print SEPARATOR
            print "* DEBUG: instsrv: Client POST request: POST parameters: %s" % (params)

        # Get parameter values for given keys
        user_id = params.get(query.Parameters.USER)
        action = params.get(query.Parameters.ACTION)
        description_file = params.get(query.Parameters.DESCRIPTION_FILE)
        progression_scenario = params.get(query.Parameters.PROGRESSION_SCENARIO)
        range_id = params.get(query.Parameters.RANGE_ID)

        if DEBUG:
            print SEPARATOR
            print "PARAMETERS:"
            print SEPARATOR
            print "USER: %s" % (user_id)
            print "ACTION: %s" % (action)
            print "DESCRIPTION FILE:\n%s" % (description_file) 
            print "PROGRESSION_SCENARIO: %s" % (progression_scenario)
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
        if DEBUG:
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

        #############################################################################
        # Instantiate the cyber range action
        if action == query.Parameters.INSTANTIATE_RANGE: 

            # Check that description is not empty
            if not description_file:
                self.send_error(REQUEST_ERROR, "Invalid description file")
                return

            # Check that range id was provided
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return

            # Save the description received as a file
            try:
                range_file_name = RANGE_DESCRIPTION_TEMPLATE.format(range_id)
                range_file = open(range_file_name, "w")
                range_file.write(description_file)
                range_file.close()
                print "* INFO: instsrv: Saved POSTed cyber range description to file '%s'." % (range_file_name)
            except IOError:
                print "* ERROR: instsrv: Could not write to file %s." % (range_file_name)

            print "* INFO: instsrv: Start cyber range instantiation."

            # Use CyRIS to really do cyber range instantiation
            if USE_CYRIS:
                try:
                    command = "python -u " + CYRIS_PATH + "main/cyris.py " + range_file_name + " " + CYRIS_PATH + CYRIS_CONFIG_FILENAME
                    return_value = os.system(command)
                    exit_status = os.WEXITSTATUS(return_value)
                    if exit_status != 0:
                        self.handle_cyris_error(range_id)
                        self.send_error(SERVER_ERROR, "CyRIS execution issue")
                        return

                    status_filename = CYRIS_PATH + CYRIS_RANGE_DIRECTORY + str(range_id) + "/" + CYRIS_STATUS_FILENAME
                    with open(status_filename, 'r') as status_file:
                        status_file_content = status_file.read()
                        if DEBUG:
                            print "* DEBUG: instsrv: Status file content=", status_file_content
                        if Storyboard.SERVER_STATUS_SUCCESS in status_file_content:

                            # Get notification text
                            notification_filename_short = CYRIS_NOTIFICATION_TEMPLATE.format(range_id) 
                            notification_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                                           CYRIS_RANGE_DIRECTORY,
                                                                           range_id,
                                                                           notification_filename_short)
                            if DEBUG:
                                print "* DEBUG: instsrv: Notification file name=", notification_filename

                            message = None
                            with open(notification_filename, 'r') as notification_file:
                                notification_file_content = notification_file.read()
                                message = urllib.quote(notification_file_content)

                            response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)

                            # We try to prepare the terminal for Moodle, but
                            # errors are only considered as warnings for the
                            # moment, since this functionality is not publicly
                            # released yet in cnt2lms
                            try:
                                if USE_CNT2LMS_SCRIPT_GENERATION:
                                    ssh_command = "ssh -tt -o 'ProxyCommand ssh cyuser@172.16.1.3 -W %h:%p' root@moodle"
                                    python_command = "python -u " + CNT2LMS_PATH + "get_cyris_result.py " + CYRIS_MASTER_HOST + " " + CYRIS_MASTER_ACCOUNT + " " + CYRIS_PATH + CYRIS_RANGE_DIRECTORY + " " + range_id + " 1"
                                    command = ssh_command + " \"" + python_command + "\""
                                    print "* DEBUG: instsrv: get_cyris_result command: " + command
                                    return_value = os.system(command)
                                    exit_status = os.WEXITSTATUS(return_value)
                                    if exit_status == 0:
                                        #response_content = RESPONSE_SUCCESS
                                        pass
                                    else:
                                        #self.send_error(SERVER_ERROR, "LMS terminal preparation issue")
                                        #return
                                        print "* DEBUG: instsrv: LMS terminal preparation issue"
                            except IOError:
                                #self.send_error(SERVER_ERROR, "LMS terminal preparation I/O error)
                                #return
                                print "* DEBUG: instsrv: LMS terminal preparation I/O error"

                            # CyPROM related functionality
                            if progression_scenario:

                                print "* INFO: instsrv: Run CyPROM using scenario '{}'".format(progression_scenario)

                                # Build CyRIS details file name
                                details_filename_short = CYRIS_DETAILS_TEMPLATE.format(range_id)
                                details_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                                          CYRIS_RANGE_DIRECTORY,
                                                                          range_id,
                                                                          details_filename_short)
                                # Build CyPROM command (note the background execution!)
                                cyprom_command = "python -u {0}main/cyprom.py --scenario {1} --cyris {2} &".format(CYPROM_PATH, progression_scenario, details_filename)

                                # Execute the command and handle the exit status
                                return_value = os.system(cyprom_command)
                                exit_status = os.WEXITSTATUS(return_value)
                                if exit_status != 0:
                                    self.handle_cyris_error(range_id)
                                    self.send_error(SERVER_ERROR, "CyPROM execution issue")
                                    return
                        else:
                            # Even though CyRIS is now destroying automatically the cyber range
                            # in case of error, as this may fail, we still try to clean up here
                            self.handle_cyris_error(range_id)
                            response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                                   Storyboard.INSTANTIATION_STATUS_FILE_NOT_FOUND)

                except IOError:
                    self.handle_cyris_error(range_id)
                    self.send_error(SERVER_ERROR, Storyboard.INSTANTIATION_CYRIS_IO_ERROR)
                    return

            # Don't use CyRIS, just simulate the instantiation
            else:
                # Simulate time needed to instantiate the cyber range
                if SIMULATION_DURATION == -1:
                    sleep_time = random.randint(SIMULATION_RAND_MIN, SIMULATION_RAND_MAX)
                else:
                    sleep_time = SIMULATION_DURATION
                print Storyboard.SEPARATOR3
                print "* INFO: instsrv: Simulate instantiation by sleeping %d s." % (sleep_time)
                print Storyboard.SEPARATOR3
                time.sleep(sleep_time)

                # Simulate the success or failure of the instantiation
                if random.random() > 0.0:
                    # Get sample notification text
                    notification_filename = "{0}/{1}".format(DATABASE_DIR,
                                                             CYRIS_NOTIFICATION_SIMULATED)
                    if DEBUG:
                        print "* DEBUG: instsrv: Simulated notification file name=", notification_filename

                    message = None
                    with open(notification_filename, 'r') as notification_file:
                        notification_file_content = notification_file.read()
                        message = urllib.quote(notification_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)

                    # CyPROM related functionality
                    if progression_scenario:
                        print "* INFO: instsrv: Simulated CyPROM execution using scenario '{}'.".format(progression_scenario)

                else:
                    response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                           Storyboard.INSTANTIATION_SIMULATED_ERROR)

        #############################################################################
        # Destroy the cyber range action
        elif action == query.Parameters.DESTROY_RANGE: 

            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return

            print "* INFO: instsrv: Start destruction of cyber range with id %s." % (range_id)

            # Use CyRIS to really do cyber range destruction
            if USE_CYRIS:
                destruction_filename = CYRIS_PATH + CYRIS_DESTRUCTION_SCRIPT
                destruction_command = "{0} {1} {2}".format(destruction_filename, range_id, CYRIS_PATH + CYRIS_CONFIG_FILENAME)
                print "* DEBUG: instrv: destruction_command: " + destruction_command
                return_value = os.system(destruction_command)
                exit_status = os.WEXITSTATUS(return_value)
                if exit_status == 0:
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS)
                else:
                    response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                           "CyRIS destruction issue")

            # Don't use CyRIS, just simulate the destruction
            else:
                # Simulate time needed to destroy the cyber range
                if SIMULATION_DURATION == -1:
                    sleep_time = random.randint(SIMULATION_RAND_MIN, SIMULATION_RAND_MAX)
                else:
                    sleep_time = SIMULATION_DURATION
                print Storyboard.SEPARATOR3
                print "* INFO: instsrv: Simulate destruction by sleeping %d s." % (sleep_time)
                print Storyboard.SEPARATOR3
                time.sleep(sleep_time)

                # Simulate the success or failure of the destruction
                if random.random() > 0.0:
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS)
                else:
                    response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                           Storyboard.DESTRUCTION_SIMULATED_ERROR)

        elif action == query.Parameters.GET_CR_NOTIFICATION:
            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return
            # Get notification text
            notification_filename_short = CYRIS_NOTIFICATION_TEMPLATE.format(range_id)
            notification_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                           CYRIS_RANGE_DIRECTORY,
                                                           range_id,
                                                           notification_filename_short)
            if DEBUG:
                print "* DEBUG: instsrv: Notification file name=", notification_filename
            message = None
            try:
                with open(notification_filename, 'r') as notification_file:
                    notification_file_content = notification_file.read()
                    message = urllib.quote(notification_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)
            except:
                response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                       "CyRIS range notification issue")

        elif action == query.Parameters.GET_CR_DETAILS:
            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return
            # Get range_details yml
            range_details_filename_short = CYRIS_DETAILS_TEMPLATE.format(range_id)
            range_details_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                            CYRIS_RANGE_DIRECTORY,
                                                            range_id,
                                                            range_details_filename_short)
            if DEBUG:
                print "* DEBUG: instsrv: Notification file name=", range_details_filename
            message = None
            try:
                with open(range_details_filename, 'r') as range_details_file:
                    range_details_file_content = range_details_file.read()
                    message = urllib.quote(range_details_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)
            except:
                response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                       "CyRIS range_details issue")

        elif action == query.Parameters.GET_CR_ENTRY_POINT:
            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return
            # Get entry_points txt
            entry_points_filename_short = CYRIS_ENTRY_POINT_TEMPLATE.format(range_id)
            entry_points_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                           CYRIS_RANGE_DIRECTORY,
                                                           range_id,
                                                           entry_points_filename_short)
            if DEBUG:
                print "* DEBUG: instsrv: Entry_point file name=", entry_points_filename
            message = None
            try:
                with open(entry_points_filename, 'r') as entry_points_file:
                    entry_points_file_content = entry_points_file.read()
                    message = urllib.quote(entry_points_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)
            except:
                response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                       "CyRIS entry_points issue")

        elif action == query.Parameters.GET_CR_CREATION_STATUS:
            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return
            # Get entry_points txt
            cr_creation_status_filename_short = CYRIS_CREATION_STATUS_TEMPLATE.format(range_id)
            cr_creation_status_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                                 CYRIS_RANGE_DIRECTORY,
                                                                 range_id,
                                                                 cr_creation_status_filename_short)
            if DEBUG:
                print "* DEBUG: instsrv: Cr_creation_status file name=", cr_creation_status_filename
            message = None
            try:
                with open(cr_creation_status_filename, 'r') as cr_creation_status_file:
                    cr_creation_status_file_content = cr_creation_status_file.read()
                    message = urllib.quote(cr_creation_status_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)
            except:
                response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                       "CyRIS cr_creation_status issue")

        elif action == query.Parameters.GET_CR_INITIF:
            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return
            # Get entry_points txt
            initif_filename_short = CYRIS_INITIF_TEMPLATE.format(range_id)
            initif_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                     CYRIS_RANGE_DIRECTORY,
                                                     range_id,
                                                     initif_filename_short)
            if DEBUG:
                print "* DEBUG: instsrv: Initif file name=", initif_filename
            message = None
            try:
                with open(initif_filename, 'r') as initif_file:
                    initif_file_content = initif_file.read()
                    message = urllib.quote(initif_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)
            except:
                response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                       "CyRIS initif issue")

        elif action == query.Parameters.GET_CR_CREATION_LOG:
            # Check that the range id is valid
            if not range_id:
                self.send_error(REQUEST_ERROR, "Invalid range id")
                return
            # Get entry_points txt
            creation_log_filename_short = CYRIS_CREATION_LOG_TEMPLATE.format(range_id)
            creation_log_filename = "{0}{1}{2}/{3}".format(CYRIS_PATH,
                                                           CYRIS_RANGE_DIRECTORY,
                                                           range_id,
                                                           creation_log_filename_short)
            if DEBUG:
                print "* DEBUG: instsrv: CREATION_LOG file name=", creation_log_filename
            message = None
            try:
                with open(creation_log_filename, 'r') as creation_log_file:
                    creation_log_file_content = creation_log_file.read()
                    message = urllib.quote(creation_log_file_content)
                    response_content = self.build_response(Storyboard.SERVER_STATUS_SUCCESS, message)
            except:
                response_content = self.build_response(Storyboard.SERVER_STATUS_ERROR,
                                                       "CyRIS creation_log issue")
        # Catch potential unimplemented actions (if any)
        else:
            print "* WARNING: instsrv: Unknown action: %s." % (action)

        # Send response header to requester (triggers log_message())
        self.send_response(HTTP_OK_CODE)
        self.send_header("Content-type", "text/html")
        self.end_headers() 

        # Send scenario database content information to requester
        self.wfile.write(response_content)

        # Output server reply
        if DEBUG:
            print "* DEBUG: instsrv: Server response content: %s" % (response_content)

    def build_response(self, status, message=None):

        # Prepare status
        response_status = '"{0}": "{1}"'.format(Storyboard.SERVER_STATUS_KEY, status)

        # If a message exists we append it to the status, otherwise we
        # make an array with a dictionary containing only the status
        if message:
            response_message = '"{0}": "{1}"'.format(Storyboard.SERVER_MESSAGE_KEY, message)
            response_body = '[{' + response_status + ", " + response_message + '}]'
        else:
            response_body = '[{' + response_status + '}]'

        return response_body

    def handle_cyris_error(self, range_id):
        print "* INFO: Error occurred in CyRIS => perform cyber range cleanup."
        destruction_filename = CYRIS_PATH + CYRIS_DESTRUCTION_SCRIPT
        destruction_command = "{0} {1} {2}".format(destruction_filename, range_id, CYRIS_PATH + CYRIS_CONFIG_FILENAME)
        print "* DEBUG: instrv: destruction_command: " + destruction_command
        return_value = os.system(destruction_command)
        exit_status = os.WEXITSTATUS(return_value)
        if exit_status != 0:
            print "* ERROR: instrv: Range cleanup failed."

# Print usage information
def usage():
    print "OVERVIEW: CyTrONE instantiation server that manages the CyRIS cyber range instantiation system.\n"
    print "USAGE: instsrv.py [options]\n"
    print "OPTIONS:"
    print "-h, --help           Display help"
    print "-n, --no-inst        Disable instantiation => only simulate actions"
    print "-p, --path <PATH>    Set the location where CyRIS is installed"
    print "-m, --cyprom <PATH>  Set the location where CyPROM is installed\n"


# Use threads to handle multiple clients
# Note: By using ForkingMixIn instead of ThreadingMixIn,
# separate processes are used instead of threads
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


#############################################################################
# Main program
#############################################################################
def main(argv):

    global USE_CYRIS
    global CYRIS_PATH
    global CYPROM_PATH

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(argv, "hnp:m:", ["help", "no-inst", "path=", "cyprom="])
    except getopt.GetoptError as err:
        print "* ERROR: instsrv: Command-line argument error: %s" % (str(err))
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-n", "--no-inst"):
            USE_CYRIS = False
        elif opt in ("-p", "--path"):
            CYRIS_PATH = arg
        elif opt in ("-m", "--cyprom"):
            CYPROM_PATH = arg

    # Assign default values to CYRIS_PATH and CYPROM_PATH if necessary
    if not CYRIS_PATH:
        CYRIS_PATH = DEFAULT_CYRIS_PATH
    if not CYPROM_PATH:
        CYPROM_PATH = DEFAULT_CYPROM_PATH
    # Append '/' to paths names if it is not present
    if not CYRIS_PATH.endswith("/"):
        CYRIS_PATH += "/"
    if not CYPROM_PATH.endswith("/"):
        CYPROM_PATH += "/"

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
        print "* INFO: instsrv: CyTrONE instantiation server listens on %s:%d%s." % (
            server_address, server_port, multi_threading)
        if not USE_CYRIS:
            print "* INFO: instsrv: CyRIS use is disabled => only simulate actions."
        else:
            print "* INFO: instsrv: Using CyRIS software installed in %s." % (CYRIS_PATH)
            print "* INFO: instsrv: Using CyPROM software installed in %s." % (CYPROM_PATH)

        if SERVE_FOREVER:
            server.serve_forever()
        else:
            server.handle_request()

    # Deal with keyboard interrupts
    except KeyboardInterrupt:
        print "* INFO: instsrv: Interrupted via ^C => shut down server."
        server.socket.close()

    print "* INFO: instsrv: CyTrONE instantiation server ended execution."


#############################################################################
# Run server
if __name__ == "__main__":
    main(sys.argv[1:])
