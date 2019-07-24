
#############################################################################
# Classes to handle user-related information
#############################################################################

# External imports
import yaml
#import string


# Various constants
SEPARATOR = "-----------------------------------------------------------------"
SEPARATO2 = "================================================================="

# Debugging constants
DO_DEBUG = False


#############################################################################
# Manage the keys used for representing user information
#############################################################################
class Keys:
    
    # Values of keys for representing general user information
    USERS = "users"
    NAME = "name"
    ID = "id"
    PASSWORD = "password"

    # Values of keys for representing host information
    HOST_MGMT_ADDR = "host_mgmt_addr"
    #HOST_EXP_ADDR = "host_exp_addr"
    HOST_VIRBR_ADDR = "host_virbr_addr"
    HOST_ACCOUNT = "host_account"
    #HOST_PASSWD = "host_passwd"
    #GUEST_IP_ADDR = "guest_ip_addr"
    #CLONE_MGMT_NETWORK_PREFIX = "clone_mgmt_network_prefix"

    # NOTE: Above are keys used for _defining_ variable values,
    #       and then used as such in the output files
    #       Below are keys that are assigned values internally,
    #       and appear only in the output files

    #CLONE_MGMT_NETWORK = "clone_mgmt_network"
    CLONE_INSTANCE_NUMBER = "clone_instance_number"  ##### ????????
    #CLONE_MGMT_ADDR_LIST = "clone_mgmt_addr_list"
    # This is anther special case of internal variable:
    # it appears in the template, but it is assigned a value internally
    CLONE_RANGE_ID = "clone_range_id"
    

#############################################################################
# Manage user information
#############################################################################
class User:

    # Constants
    CLONE_MGMT_NETWORK_SUFFIX = ".1.1/16"
    CLONE_MGMT_ADDR_FIRST_SUFFIX = 2

    # Variables defined in "users.yml" and used as such in the output files
    DEFINED_VARIABLES = [
        Keys.HOST_MGMT_ADDR, #Keys.HOST_EXP_ADDR,
        Keys.HOST_VIRBR_ADDR, Keys.HOST_ACCOUNT,
        #Keys.HOST_PASSWD,
        #Keys.GUEST_IP_ADDR,
        #Keys.CLONE_MGMT_NETWORK_PREFIX
    ]

    # Only variables that are assigned values internally
    INTERNAL_VARIABLES = [
        #Keys.CLONE_MGMT_NETWORK,
        Keys.CLONE_INSTANCE_NUMBER,
        #Keys.CLONE_MGMT_ADDR_LIST,
        Keys.CLONE_RANGE_ID
    ]
    
    # All variables that are assigned values, including those that are
    # internally assigned
    ALL_VARIABLES = []
    ALL_VARIABLES.extend(DEFINED_VARIABLES)
    ALL_VARIABLES.extend(INTERNAL_VARIABLES)

    
    # Initialize object based on user information
    def __init__(self, user_info):

        self.name = user_info.get(Keys.NAME, None)
        assert self.name != None

        self.id = user_info.get(Keys.ID, None)
        assert self.id != None

        self.password = user_info.get(Keys.PASSWORD, None)

        for variable in self.DEFINED_VARIABLES:
            if DO_DEBUG:
                print "* DEBUG: userinfo: %s -> %s" % (variable, user_info.get(variable, None))
            # Make sure to convert to string in order to avoid having
            # a value such as 10.1 be treated as a float
            setattr(self, variable, user_info.get(variable, None).__str__())
            assert getattr(self, variable) != None

            # Deal with special variables
            #if variable == Keys.CLONE_MGMT_NETWORK_PREFIX:
            #    clone_mgmt_addr = getattr(self, variable) + self.CLONE_MGMT_NETWORK_SUFFIX
            #    setattr(self, Keys.CLONE_MGMT_NETWORK, clone_mgmt_addr)
        
        if DO_DEBUG:
            print "* DEBUG: userinfo: USER:  NAME=%s  ID=%s" % (self.name, self.id)


    # Create a string representation of the user
    def __str__(self):
        
        return "  - " + Keys.NAME + ": " + self.name + "\n    " \
                 + Keys.ID + ": " + self.id
    

    # Replace variables in a range specification based on user information
    def replace_variables(self, range_file_content, cyber_range_id, instance_count):

        return_string = range_file_content

        #ADDR_SUFFIX = "SFX"

        # Assign cyber range id to internal variable
        setattr(self, Keys.CLONE_RANGE_ID, cyber_range_id)
        
        # Derive internal variables that depend on instance_count
        setattr(self, Keys.CLONE_INSTANCE_NUMBER, str(instance_count))
        #addr_list = ""
        #for i in range (1, instance_count+1):
        #    # Special handling of suffix
        #    addr_list += (getattr(self, Keys.CLONE_MGMT_NETWORK_PREFIX)
        #                        + "." + str(i) + "." + ADDR_SUFFIX
        #                        + "; ")
        #setattr(self, Keys.CLONE_MGMT_ADDR_LIST, addr_list)

        # Do replace all variables with their values
        for variable in self.ALL_VARIABLES:
            variable_name = "{{ " + variable + " }}"
            variable_value = getattr(self, variable)

            if DO_DEBUG:
                print "* DEBUG: userinfo: name=%s value=%s" % (variable_name, variable_value)

            return_string = return_string.replace(variable_name, variable_value)

            # Replace the variable names with values
            #if variable != Keys.CLONE_MGMT_ADDR_LIST:
            #    return_string = return_string.replace(variable_name, variable_value)
            # CLONE_MGMT_ADDR_LIST needs special handling    
            #else:
            #    suffix = self.CLONE_MGMT_ADDR_FIRST_SUFFIX
            #    # While the variable name still appears in the list, we replace
            #    # _only_ one instance of it with an incremental suffix number
            #    while Keys.CLONE_MGMT_ADDR_LIST in return_string:
            #        variable_value2 = variable_value.replace(ADDR_SUFFIX, str(suffix))
            #        return_string = return_string.replace(variable_name, variable_value2, 1)
            #        suffix += 1
        
        return return_string


#############################################################################
# Manage user information
#############################################################################
class UserInfo:

    # List of users (User objects)
    users = []

    
    # Parse a YAML information in a file and store values into the
    # object fields
    def parse_YAML_file(self, yaml_file_name):

        # Open the YAML file
        try:
            yaml_file = open(yaml_file_name, "r")
        except IOError:
            print "* ERROR: userinfo: Cannot open file %s." % (yaml_file_name)
            return False
            
        try:
            # Load the YAML information
            info = yaml.load(yaml_file)

            # Close the file
            yaml_file.close()

            # Actually parse the information
            result = self.parse_info(info)

            if DO_DEBUG:
                print result

            return True

        except yaml.YAMLError as exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                print "* ERROR: userinfo: YAML error in file %s at position: (%s:%s)." % (
                    yaml_file_name, mark.line+1, mark.column+1)
            return False


    # Actually parse a information object, and store values into the
    # object fields
    def parse_info(self, info):

        self.users = []
        
        # Get data for all users from info
        for data in info:
            users_info = data.get(Keys.USERS, None)
            if users_info != None:
                break
        assert users_info != None

        if DO_DEBUG:
            print SEPARATOR
            print "* DEBUG: userinfo: PARSE INFO: %d users(s)" % (
                len(users_info))
            print users_info
            print SEPARATOR

        # Get data for each user
        for user_info in users_info:

            user = User(user_info)
            self.users.append(user)

            if DO_DEBUG:
                print "* DEBUG: userinfo: USER: %s" % (user)
                
        if DO_DEBUG:
            print SEPARATOR

        return True
    
 
    # Get a user identified by id if it exists
    def get_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user
            
        return None


    # Pretty-print info about the object
    def pretty_print(self):
        index = 1;
        print SEPARATOR
        print "USER INFO: %d user(s)" % (
            len(self.users))
        print SEPARATOR
        for user in self.users:
            print "USER #%d:" % (index)
            print user
            index += 1
        print SEPARATOR


#############################################################################
# Testing code for the classes in this file
#
# This code will be executed _only_ when this module is called as the
# main program
#############################################################################
if __name__ == '__main__':
    try:

        enabled = [True]
        DATABASE_DIR = "../database/"

        #####################################################################
        # TEST #1
        if enabled[0]:
            TEST_FILE = DATABASE_DIR + "users.yml"
            print SEPARATO2
            print "TEST #1: Get user information from YAML file: %s." % (
                TEST_FILE)
            print SEPARATO2
            user_info = UserInfo()
            user_info.parse_YAML_file(TEST_FILE)
            user_info.pretty_print()
    
    except IOError as error:
        print "* ERROR: userinfo: %s." % (error)
