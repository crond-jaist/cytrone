
#############################################################################
# Classes to handle training session information
#############################################################################

# External imports
import yaml
import json
#import types

# Various constants
SEPARATOR = "-----------------------------------------------------------------"
SEPARATO2 = "================================================================="

# Debugging constants
DO_DEBUG = False


#############################################################################
# Manage the keys used for representing session information
#############################################################################
class Keys:
    
    # Values of keys for session information representation
    SESSIONS = "sessions"
    NAME = "name"
    ID = "id"
    USER = "user"
    TIME = "time"
    
    TYPE = "type"
    SCENARIOS = "scenarios"
    LEVELS = "levels"
    LANGUAGE = "language"
    COUNT = "count"
    ACTIVITY_ID = "activity_id"


#############################################################################
# Manage session information
#############################################################################
class Session:

    # Initialize object using scenario information
    def __init__(self, session_info=None):

        if session_info != None:

            # Management-related parameters
            self.name = session_info.get(Keys.NAME, None)
            assert self.name!=None

            # Since id() is a built-in function we need to use the name "sess_id"
            self.sess_id = session_info.get(Keys.ID, None)
            assert self.sess_id!=None

            self.user_id = session_info.get(Keys.USER, None)
            assert self.user_id!=None

            self.time = session_info.get(Keys.TIME, None)
            assert self.time!=None

            # Content-related parameters
            self.ttype = session_info.get(Keys.TYPE, None)
            assert self.ttype!=None
            
            self.scenarios = session_info.get(Keys.SCENARIOS, None)
            assert self.scenarios!=None

            self.levels = session_info.get(Keys.LEVELS, None)
            assert self.levels!=None

            self.language = session_info.get(Keys.LANGUAGE, None)
            assert self.language!=None

            self.count = session_info.get(Keys.COUNT, None)
            assert self.count!=None

            self.activity_id = session_info.get(Keys.ACTIVITY_ID, None)

    # Set fields for Session object
    def set_fields(self, name, sess_id, user_id, time, ttype,
                   scenarios, levels, language, count, activity_id):
        self.name = name
        self.sess_id = sess_id
        self.user_id = user_id
        self.time = time

        self.ttype = ttype
        self.scenarios = scenarios
        self.levels = levels
        self.language = language
        self.count = count
        self.activity_id = activity_id
        
    # Create a string representation of the session
    def __str__(self):

        string = "  - " + Keys.NAME + ": " + self.name + "\n    " \
                 + Keys.ID + ": " + str(self.sess_id) + "\n    " \
                 + Keys.USER + ": " + self.user_id + "\n    " \
                 + Keys.TIME + ": " + self.time  + "\n    " \
                 + Keys.TYPE + ": " + self.ttype + "\n    " \
                 + Keys.SCENARIOS + ": " + str(self.scenarios) + "\n    " \
                 + Keys.LEVELS + ": " + str(self.levels) + "\n    " \
                 + Keys.LANGUAGE + ": " + self.language + "\n    " \
                 + Keys.COUNT + ": " + self.count + "\n    " \
                 + Keys.ACTIVITY_ID + ": " + self.activity_id

        return string
    
    def get_JSON_representation(self, user_id):

        if self.user_id == user_id:
            return self.add_info_to_representation({})
            
        return {}

    def get_JSON_representation_all(self):

        return self.add_info_to_representation({})

    def add_info_to_representation(self, session_repr):

        # Management-related info
        session_repr[Keys.NAME] = self.name
        session_repr[Keys.ID] = self.sess_id
        session_repr[Keys.USER] = self.user_id
        session_repr[Keys.TIME] = self.time
        session_repr[Keys.ACTIVITY_ID] = self.activity_id

        # Content-related info
        session_repr[Keys.TYPE] = self.ttype
        session_repr[Keys.SCENARIOS] = self.scenarios
        session_repr[Keys.LEVELS] = self.levels
        session_repr[Keys.COUNT] = self.count
        session_repr[Keys.LANGUAGE] = self.language

        return session_repr
    
#############################################################################
# Manage overall information about training sessions
#############################################################################
class SessionInfo:

    # List of sessions (as Session objects)
    sessions = []

    # Parse YAML information in a file and store values into the
    # object fields
    def parse_YAML_file(self, yaml_file_name):

        # Initialize the sessions list
        self.sessions = []
        
        # Open the YAML file
        try:
            yaml_file = open(yaml_file_name, "r")
        except IOError:
            print "* WARNING: sessinfo: Cannot open file '%s' for read." % (yaml_file_name)
            return False
        
        try:
            # Load the YAML information
            info = yaml.load(yaml_file)

            # Close the file
            yaml_file.close()

            # Actually parse the information
            return self.parse_info(info)

        except yaml.YAMLError as exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                print "* ERROR: sessinfo: YAML error in file %s at position: (%s:%s)." % (
                    yaml_file_name, mark.line+1, mark.column+1)

            return False
        
    # Parse JSON data and store values into the object fields
    def parse_JSON_data(self, json_data):

        try:
            # Load JSON data from json_data
            data = json.loads(json_data)

            # Actually parse the information
            return self.parse_info(data)

        except ValueError as error:
            print "* ERROR: sessinfo: %s." % (error)
            return False


    # Actually parse a information object, and store values into the
    # object fields
    def parse_info(self, info):

        # Initialize the sessions list
        self.sessions = []
        
        # Get data for all training sessions from info
        for data in info:
            sessions_info = data.get(Keys.SESSIONS, None)
            if sessions_info != None:
                break    
        assert sessions_info!=None

        if DO_DEBUG:
            print SEPARATOR
            print "* DEBUG: sessinfo: PARSE INFO: %d session(s)" % (
                len(sessions_info))
            print sessions_info
            print SEPARATOR

        # If there are no sessions, we return here
        #if sessions_info == None:
        #    return False
        
        # Get data for each training session
        for session_info in sessions_info:

            session = Session(session_info)
            self.sessions.append(session)

            if DO_DEBUG:
                print "* DEBUG: sessinfo: SESSION:\n%s" % (session)

        if DO_DEBUG:
            print SEPARATOR

        return True

    
    # Add a session with the corresponding parameters
    def add_session(self, session_name, cyber_range_id, user_id, crt_time,
                    ttype, scenarios, levels, language, count, activity_id):

        session = Session(None)
        session.set_fields(session_name, cyber_range_id, user_id, crt_time,
                           ttype, scenarios, levels, language, count, activity_id)
        self.sessions.append(session)

        #if DO_DEBUG:   
        #self.pretty_print()


    # Remove a session with the corresponding parameters
    def remove_session(self, cyber_range_id, user_id):

        for session in self.sessions:
            if session.sess_id == cyber_range_id and session.user_id == user_id:
                self.sessions.remove(session)
                return True

        return False
    # Remove a session with the corresponding parameters
    def remove_session_variation(self, cyber_range_id, user_id,activity_id):
        for session in self.sessions:
            if session.sess_id == cyber_range_id and session.user_id == user_id and session.activity_id == activity_id:
                self.sessions.remove(session)
                return True

        return False

    # Build a list of active session ids
    def get_id_list_int(self):

        id_list = []
        for session in self.sessions:
            id_list.append(int(session.sess_id))

        return id_list

    # Determine whether a session with the given id exists
    def is_session_id(self, cyber_range_id):

        for session in self.sessions:
            if session.sess_id == cyber_range_id:
                return True

        return False

    # Determine whether a session with the given id exists for the
    # specified user
    def is_session_id_user(self, cyber_range_id, user_id):

        for session in self.sessions:
            if session.sess_id == cyber_range_id and session.user_id == user_id:
                return True

        return False

    # Get the activity id for a session with given id and a specified user
    def get_activity_id(self, cyber_range_id, user_id):

        for session in self.sessions:
            if session.sess_id == cyber_range_id and session.user_id == user_id:
                return session.activity_id

        return None

    # Get the activity id for a session with given id and a specified user
    def get_activity_id_list(self, cyber_range_id, user_id):
        activity_list=[]
        for session in self.sessions:
            if session.sess_id == cyber_range_id and session.user_id == user_id:
                activity_list.append(session.activity_id)
        if activity_list is None:
            return None
        else:
            return activity_list

    # Store session information in a YAML file
    def write_YAML_file(self, yaml_file_name):

        print "* INFO: sessinfo: Writing session info to file '%s'..." % (yaml_file_name)

        info = self.get_JSON_representation_all()

        # Open the YAML file
        try:
            yaml_file = open(yaml_file_name, "w")
        except IOError:
            print "* ERROR: sessinfo: Cannot open file '%s' for write." % (yaml_file_name)
            return False

        if DO_DEBUG:
            print SEPARATOR
            print "* DEBUG: sessinfo: Current session info:"
            print info
#            print yaml.dump(info)
#            print yaml.dump(info, default_flow_style = None)
#            print yaml.dump(info, default_flow_style = False)
#            print yaml.dump(info, default_flow_style = True)
            print SEPARATOR

        yaml_file.write(info)
        
        #yaml.dump(info, yaml_file)
        
        # Close the file
        yaml_file.close()
       
    # Pretty-print info about the scenarios
    def pretty_print(self):
        print SEPARATOR
        print "SESSION INFO: %d session(s)" % (len(self.sessions))
        print SEPARATOR
        index = 1;
        for session in self.sessions:
            #print "SESSION %d:" % (index)
            print "SESSION:"
            print session.__str__()
            index += 1
        print SEPARATOR


    # Create an external JSON representation that includes only
    # information that can be made available to clients
    def get_JSON_representation(self, user_id):
        representation = []

        # Build sessions representation
        sessions_repr = {}
        sessions_repr_array = []
        for session in self.sessions:
            session_repr = session.get_JSON_representation(user_id)

            # Only add representation to array if it is not empty
            if session_repr:
                sessions_repr_array.append(session_repr)
        sessions_repr[Keys.SESSIONS] = sessions_repr_array

        # Combine representations
        representation.append(sessions_repr)

        return json.dumps(representation)

    # Create an external JSON representation that includes
    # information for all users
    def get_JSON_representation_all(self):
        representation = []

        # Build sessions representation
        sessions_repr = {}
        sessions_repr_array = []
        for session in self.sessions:
            session_repr = session.get_JSON_representation_all()

            # Only add representation to array if it is not empty
            if session_repr:
                sessions_repr_array.append(session_repr)
        sessions_repr[Keys.SESSIONS] = sessions_repr_array

        # Combine representations
        representation.append(sessions_repr)

        return json.dumps(representation)


#############################################################################
# Testing code for the classes in this file
#
# This code will be executed _only_ when this module is called as the
# main program
#############################################################################
if __name__ == '__main__':
    try:

        enabled = [True, True]

        #####################################################################
        # TEST #1
        if enabled[0]:
            TEST_FILE = "active_sessions.yml"
            print "\n" + SEPARATO2
            print "TEST #1: Get session information from YAML file: %s" % (
                TEST_FILE)
            print SEPARATO2
            session_info = SessionInfo()
            session_info.parse_YAML_file(TEST_FILE)
            session_info.pretty_print()
            user_id = "john_doe"
            print "External JSON representation: %s" % (session_info.get_JSON_representation(user_id))

        #####################################################################
        # TEST #2
        if enabled[1]:
            TEST_STRING = '[{"sessions": [{"count": "2", "activity_id": "N/A", "name": "Training Session #1", "language": "en", "scenarios": ["Information Security Testing and Assessment"], "levels": ["Level 1 (Easy)"], "user": "john_doe", "time": "Thu Jul 11 10:43:31 2019", "type": "Scenario-Based Training", "id": "1"}]}]'
            print "\n" + SEPARATO2
            print "TEST #2: Get session information from JSON string: %s." % (
                TEST_STRING)
            print SEPARATO2
            session_info = SessionInfo()
            session_info.parse_JSON_data(TEST_STRING)
            session_info.pretty_print()
    
    except IOError as error:
        print "* ERROR: sessinfo: %s." % (error)
