
#############################################################################
# Classes related to the CyTrONE storyboard
#############################################################################

class Storyboard:

    # Global configuration flags
    ENABLE_HTTPS = True
    ENABLE_PASSWORD = True
    SSL_keyfile = "cytrone.key"
    SSL_certfile = "cytrone.crt"
    SSL_ca_certs = None

    # Separator constants
    SEPARATOR1 = "-------------------------------------------------------------------------"
    SEPARATOR2 = "========================================================================="
    SEPARATOR3 = "#########################################################################"

    # Server status keys
    SERVER_STATUS_KEY = "status"
    SERVER_STATUS_SUCCESS = "SUCCESS"
    SERVER_STATUS_ERROR = "ERROR"
    SERVER_ACTIVITY_ID_KEY = "activity_id"
    SERVER_MESSAGE_KEY = "message"

    # Server status messages
    USER_SETTINGS_LOADING_ERROR = "Server could not load the user information database"
    USER_ID_MISSING_ERROR = "User id is missing"
    USER_ID_INVALID_ERROR = "User id is invalid"
    USER_PASSWORD_MISSING_ERROR = "User password is missing"
    USER_PASSWORD_NOT_IN_DATABASE_ERROR = "User password not in database"
    USER_ID_PASSWORD_INVALID_ERROR = "User id and/or password are invalid"

    ACTION_MISSING_ERROR = "Action is missing"
    ACTION_INVALID_ERROR = "Action is invalid"

    LANGUAGE_MISSING_ERROR = "Language is missing"
    LANGUAGE_INVALID_ERROR = "Language is invalid"

    TRAINING_SETTINGS_LOADING_ERROR = "Server could not load the training settings database"

    INSTANCE_COUNT_MISSING_ERROR = "Instance count is missing"
    INSTANCE_COUNT_INVALID_ERROR = "Instance count is invalid"

    TRAINING_TYPE_MISSING_ERROR = "Training type is invalid or missing"

    SCENARIO_NAME_MISSING_ERROR = "Scenario name is missing"

    LEVEL_NAME_MISSING_ERROR = "Level name is missing"

    SESSION_ALLOCATION_ERROR = "Server could not allocate a new session (maximum number reached)"

    CONTENT_IDENTIFICATION_ERROR = "Server could not determine the training content for the specified scenario and level"
    CONTENT_LOADING_ERROR = "Server could not load the training content"
    CONTENT_UPLOAD_ERROR = "LMS content manager could not upload the training content"
    CONTENT_REMOVAL_ERROR = "LMS content manager could not remove the training activity"
    CONTENT_SERVER_ERROR = "Server could not communicate with the LMS content manager"

    TEMPLATE_IDENTIFICATION_ERROR = "Server could not determine the cyber range template for the specified scenario and level" 
    TEMPLATE_LOADING_ERROR = "Server could not load the cyber range template" 

    INSTANTIATION_SERVER_ERROR = "Server could not communicate with the cyber range manager"
    INSTANTIATION_ERROR = "Cyber range manager could not instantiate the cyber range"
    INSTANTIATION_STATUS_FILE_NOT_FOUND = "Instantiation status file could not be found"
    INSTANTIATION_CYRIS_IO_ERROR = "CyRIS execution I/O error"
    INSTANTIATION_SIMULATED_ERROR = "Simulated range instantiation error"

    DESTRUCTION_ERROR = "Cyber range manager could not destroy the cyber range"
    DESTRUCTION_SIMULATED_ERROR = "Simulated range destruction error"
    DESTRUCTION_SCRIPT_NOT_FOUND = "Destruction script could not be found"

    SESSION_ID_MISSING_ERROR = "Session id is missing"
    SESSION_ID_INVALID_ERROR = "Session id is invalid"
    SESSION_INFO_CONSISTENCY_ERROR = "Server encountered a session information consistency issue"
