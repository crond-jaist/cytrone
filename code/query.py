
#############################################################################
# Classes related to the query parameters used by CyTrONE servers
#############################################################################

# External imports
import urlparse
import json

# Internal imports
from storyboard import Storyboard


#############################################################################
# Constants
#############################################################################

# Various constants
SEPARATOR = "-----------------------------------------------------------------"

# Debugging constants
DO_DEBUG = False


#############################################################################
# Manage the query parameters the training server recognizes
#############################################################################
class Parameters:
    
    ## Constants defining keys and values
    # User information
    USER = "user"
    PASSWORD = "password"

    # Action specification
    ACTION = "action"
    
    FETCH_CONTENT = "fetch_content"         # Training server
    CREATE_TRAINING = "create_training"
    GET_CONFIGURATIONS = "get_configurations"
    GET_SESSIONS = "get_sessions"
    END_TRAINING = "end_training"

    INSTANTIATE_RANGE = "instantiate_range" # Instantiation server
    DESTROY_RANGE = "destroy_range"

    UPLOAD_CONTENT = "upload_content"       # Content server
    RESET_CONTENT = "reset_content"
    
    # Language settings
    LANG = "lang"
    EN = "en"
    JA = "ja"

    # Range settings
    TYPE = "type"
    SCENARIO = "scenario"
    LEVEL = "level"
    COUNT = "count"
    DESCRIPTION_FILE = "description_file"
    RANGE_ID = "range_id"

    #########################################################################
    # Initialize object with parameters from POST message
    def __init__(self, request_handler = None):

        if request_handler:
            # Get the length of the POST message content, and read data
            # from message accordingly
            length = int(request_handler.headers.getheader('content-length'))
            parameter_data = request_handler.rfile.read(length)

            # Parse the query string into a dictionary (raise exception if
            # there are parsing errors)
            self.parameters = urlparse.parse_qs(parameter_data,
                                                strict_parsing=True)

    #########################################################################
    # Parse query parameters
    def parse_parameters(self, query_string):
        # Parse the query string into a dictionary (raise exception if
        # there are parsing errors)
        self.parameters = urlparse.parse_qs(query_string, strict_parsing=True)
        
    #########################################################################
    # Return a string representation of the object
    def __str__(self):
        return str(self.parameters)

    #########################################################################
    # Get the value of the parameter corresponding to a given key
    def get(self, key):

        # Set default values if the key is not specified;
        # must use lists in order to mimic the output of parse_qs()
        default_values = {
            self.USER: None,
            self.PASSWORD: None,
            self.ACTION: None,
            self.LANG: [self.EN],
            self.TYPE: None,
            self.SCENARIO: None,
            self.LEVEL: None,
            self.COUNT: None,
            self.DESCRIPTION_FILE: None,
            self.RANGE_ID: None
        }

        # Get values associated to the key
        values = self.parameters.get(key, default_values[key])
        
        # If values is not None and not a zero length list, return the
        # first element of the list
        if values:
            return values[0]
        return None

#############################################################################
# Handle the training server response
#############################################################################
class Response:

    # Parse response of instantiation server
    @staticmethod
    def parse_server_response(json_data):

        try:
            # Load JSON data                            
            data = json.loads(json_data)

            status = None
            message = None
            for item in data:
                status = item.get(Storyboard.SERVER_STATUS_KEY, None)
                if status != None:
                    message = item.get(Storyboard.SERVER_MESSAGE_KEY, None)
                    break

            return (status, message)
        
        except ValueError as error:
            print "* ERROR: query: %s." % (error)
            return (None, None)


