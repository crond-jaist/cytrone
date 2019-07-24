
#############################################################################
# Classes to handle scenario-related information
#############################################################################

# External imports
import yaml
import json
import types

# Various constants
SEPARATOR = "-----------------------------------------------------------------"
SEPARATO2 = "================================================================="

# Debugging constants
DO_DEBUG = False


#############################################################################
# Manage the keys used for representing scenario information
#############################################################################
class Keys:
    
    # Values of keys for scenario information representation
    TYPES = "types"
    NAME = "name"
    CATEGORY = "category"
    SCENARIOS = "scenarios"
    LEVELS = "levels"
    CONTENT = "content"
    SPECIFICATION = "specification" # Obsolete label => to be removed
    RANGE = "range"
    PROGRESSION = "progression"


#############################################################################
# Manage training type information
#############################################################################
class TrainingType:

    # Initialize object based on type information
    def __init__(self, type_info):

        self.name = type_info.get(Keys.NAME, None)
        assert self.name!=None

        self.category = type_info.get(Keys.CATEGORY, None)
        assert self.category!=None

    # Create a string representation of the training type
    def __str__(self):

        string = "  - " + Keys.NAME + ": " + self.name + "\n    " \
                 + Keys.CATEGORY + ": " + self.category
        
        return string

    def get_JSON_representation(self):

        type_repr = {}
        type_repr[Keys.NAME] = self.name
        type_repr[Keys.CATEGORY] = self.category

        return type_repr

    
#############################################################################
# Manage scenario information
#############################################################################
class Scenario:

    # Initialize object using scenario information
    def __init__(self, scenario_info):

        self.name = scenario_info.get(Keys.NAME, None)
        assert self.name!=None

        levels_info = scenario_info.get(Keys.LEVELS, None)
        assert levels_info!=None

        self.levels = []
        for level_info in levels_info:
            level = Level(level_info)
            self.levels.append(level)

    # Create a string representation of the scenario
    def __str__(self):

        string = "  - " + Keys.NAME + ": " + self.name + "\n    " \
                 + Keys.LEVELS + ": " + str(len(self.levels)) + " level(s)"

        for level in self.levels:
            string += "\n" + level.__str__()

        return string

    def get_JSON_representation(self):

        scenario_repr = {}
        scenario_repr[Keys.NAME] = self.name

        levels_repr_array = []
        for level in self.levels:
            levels_repr_array.append(level.get_JSON_representation())
        scenario_repr[Keys.LEVELS] = levels_repr_array

        return scenario_repr


#############################################################################
# Manage level information
#############################################################################
class Level:

    # Initialize object based on level information
    def __init__(self, level_info):
        
        self.name = level_info.get(Keys.NAME, None)
        assert self.name!=None

        self.content_file = level_info.get(Keys.CONTENT, None)
        self.range_file = level_info.get(Keys.RANGE, None)
        # Also try alternative (obsolete) label
        if not self.range_file:
            self.range_file = level_info.get(Keys.SPECIFICATION, None)
        #assert self.range_file!=None
        self.progression_scenario = level_info.get(Keys.PROGRESSION, None)

    # Create a string representation of the level
    def __str__(self):

        string = "      - " + Keys.NAME + ": " + self.name + "\n        " \
                 + Keys.CONTENT + ": " + str(self.content_file) + "\n        " \
                 + Keys.RANGE + ": " + str(self.range_file) + "\n        " \
                 + Keys.PROGRESSION + ": " + str(self.progression_scenario)
        return string

    def get_JSON_representation(self):

        level_repr = {}
        level_repr[Keys.NAME] = self.name

        return level_repr

    
#############################################################################
# Manage overall information about training
#############################################################################
class TrainingInfo:

    # List of scenarios (as Scenario objects)
    scenarios = []

    # Parse a YAML information in a file and store values into the
    # object fields
    def parse_YAML_file(self, yaml_file_name):

        # Open the YAML file
        try:
            yaml_file = open(yaml_file_name, "r")
        except IOError:
            print "ERROR: Cannot open file %s." % (yaml_file_name)
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
                print "ERROR: YAML error in file %s at position: (%s:%s)." % (
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
            print "ERROR: %s." % (error)
            return False


    # Actually parse a information object, and store values into the
    # object fields
    def parse_info(self, info):

        # Initialize the types list
        self.types = []

        # Initialize the scenario list
        self.scenarios = []
        
        # Get data for all training types from info
        for data in info:
            types_info = data.get(Keys.TYPES, None)
            if types_info != None:
                break    
        assert types_info!=None

        if DO_DEBUG:
            print SEPARATOR
            print "PARSE INFO: %d type(s)" % (
                len(types_info))
            print types_info
            print SEPARATOR

        # Get data for each training type
        for type_info in types_info:

            type = TrainingType(type_info)
            self.types.append(type)

            if DO_DEBUG:
                print "TYPE:\n%s" % (type)

        if DO_DEBUG:
            print SEPARATOR

        
        # Get data for all scenarios from info
        for data in info:
            scenarios_info = data.get(Keys.SCENARIOS, None)
            if scenarios_info != None:
                break    
        assert scenarios_info!=None

        if DO_DEBUG:
            print SEPARATOR
            print "PARSE INFO: %d scenario(s)" % (
                len(scenarios_info))
            print scenarios_info
            print SEPARATOR

        # Get data for each scenario
        for scenario_info in scenarios_info:

            scenario = Scenario(scenario_info)
            self.scenarios.append(scenario)

            if DO_DEBUG:
                print "SCENARIO:\n%s" % (scenario)

        if DO_DEBUG:
            print SEPARATOR

        return True
    

    # Pretty-print info about the scenarios
    def pretty_print(self):
        print SEPARATOR
        print "TRAINING INFO: %d type(s)  %d scenario(s)" % (
            len(self.types), len(self.scenarios))
        print SEPARATOR
        index = 1;
        for type in self.types:
            print "TYPE #%d:" % (index)
            print type.__str__()
            index += 1
        index = 1;
        for scenario in self.scenarios:
            print "SCENARIO #%d:" % (index)
            print scenario.__str__()
            index += 1
        print SEPARATOR


    # Create an external JSON representation that includes only
    # information that can be made available to clients
    def get_JSON_representation(self):
        representation = []

        # Build training type representation
        types_repr = {}
        types_repr_array = []
        for type in self.types:
            types_repr_array.append(type.get_JSON_representation())
        types_repr[Keys.TYPES] = types_repr_array

        # Build scenarios representation
        scenarios_repr = {}
        scenarios_repr_array = []
        for scenario in self.scenarios:
            scenarios_repr_array.append(scenario.get_JSON_representation())
        scenarios_repr[Keys.SCENARIOS] = scenarios_repr_array

        # Combine representations
        representation.append(types_repr)
        representation.append(scenarios_repr)

        return json.dumps(representation)


    # Get the name of the file that contains the training content for the
    # scenario and level provided as arguments
    def get_content_file_name(self, scenario_name, level_name):

        scenario_name_utf = unicode(scenario_name, 'utf-8') # convert to UTF-8
        level_name_utf = unicode(level_name, 'utf-8') # convert to UTF-8
        
        content_file = None
        #print "DEBUG: Search for scenario=%s level=%s... (type=%s)" % (scenario_name.__str__(), level_name, type(scenario_name))

        for scenario in self.scenarios:
            
            if type(scenario.name) == types.UnicodeType:
                # Printing Unicode doesn't work on development servers,
                # so I commented out the debug message
                #print "DEBUG: scenario name=%s (type=%s)" % (scenario.name, type(scenario.name))
                scenario_name_cmp = scenario_name_utf
            else:
                scenario_name_cmp = scenario_name
            if scenario.name == scenario_name_cmp:
                for level in scenario.levels:
                    if type(level.name) == types.UnicodeType:
                        # Printing Unicode doesn't work on development servers,
                        # so I commented out the debug message
                        #print "DEBUG: level name=%s (type=%s)" % (level.name, type(level.name))
                        level_name_cmp = level_name_utf
                    else:
                        level_name_cmp = level_name
                    if level.name == level_name_cmp:
                        content_file = level.content_file

        return content_file

    # Get the name of the file that contains the range specification for the
    # scenario and level provided as arguments
    def get_range_file_name(self, scenario_name, level_name):

        scenario_name_utf = unicode(scenario_name, 'utf-8') # convert to UTF-8
        level_name_utf = unicode(level_name, 'utf-8') # convert to UTF-8
        
        range_file = None
        #print "DEBUG: Search for scenario=%s level=%s... (type=%s)" % (scenario_name.__str__(), level_name, type(scenario_name))

        for scenario in self.scenarios:
            
            if type(scenario.name) == types.UnicodeType:
                # Printing Unicode doesn't work on development servers,
                # so I commented out the debug message
                #print "DEBUG: scenario name=%s (type=%s)" % (scenario.name, type(scenario.name))
                scenario_name_cmp = scenario_name_utf
            else:
                scenario_name_cmp = scenario_name
            if scenario.name == scenario_name_cmp:
                for level in scenario.levels:
                    if type(level.name) == types.UnicodeType:
                        # Printing Unicode doesn't work on development servers,
                        # so I commented out the debug message
                        #print "DEBUG: level name=%s (type=%s)" % (level.name, type(level.name))
                        level_name_cmp = level_name_utf
                    else:
                        level_name_cmp = level_name
                    if level.name == level_name_cmp:
                        range_file = level.range_file

        return range_file

    # Get the name of the file that contains the progression details
    # for the scenario and level provided as arguments
    def get_progression_scenario_name(self, scenario_name, level_name):

        scenario_name_utf = unicode(scenario_name, 'utf-8') # convert to UTF-8
        level_name_utf = unicode(level_name, 'utf-8') # convert to UTF-8

        progression_scenario = None

        for scenario in self.scenarios:

            if type(scenario.name) == types.UnicodeType:
                # Printing Unicode doesn't work on development servers,
                # so I commented out the debug message
                #print "DEBUG: scenario name=%s (type=%s)" % (scenario.name, type(scenario.name))
                scenario_name_cmp = scenario_name_utf
            else:
                scenario_name_cmp = scenario_name
            if scenario.name == scenario_name_cmp:
                for level in scenario.levels:
                    if type(level.name) == types.UnicodeType:
                        # Printing Unicode doesn't work on development servers,
                        # so I commented out the debug message
                        #print "DEBUG: level name=%s (type=%s)" % (level.name, type(level.name))
                        level_name_cmp = level_name_utf
                    else:
                        level_name_cmp = level_name
                    if level.name == level_name_cmp:
                        progression_scenario = level.progression_scenario

        return progression_scenario

#############################################################################
# Testing code for the classes in this file
#
# This code will be executed _only_ when this module is called as the
# main program
#############################################################################
if __name__ == '__main__':
    try:

        enabled = [False, True, False]
        DATABASE_DIR = "../database/"
        
        #####################################################################
        # TEST #1
        if enabled[0]:
            TEST_FILE = DATABASE_DIR + "training-en.yml"
            print SEPARATO2
            print "TEST #1: Get training information from YAML file: %s." % (
                TEST_FILE)
            print SEPARATO2
            training_info = TrainingInfo()
            training_info.parse_YAML_file(TEST_FILE)
            training_info.pretty_print()
            print "External JSON representation: %s" % (training_info.get_JSON_representation())

        #####################################################################
        # TEST #2
        if enabled[1]:
            TEST_FILE = DATABASE_DIR + "training-ja.yml"
            print SEPARATO2
            print "TEST #2: Get training information from YAML file: %s." % (
                TEST_FILE)
            print SEPARATO2
            training_info = TrainingInfo()
            training_info.parse_YAML_file(TEST_FILE)
            training_info.pretty_print()
            print "External JSON representation: %s" % (training_info.get_JSON_representation())

        #####################################################################
        # TEST #3
        if enabled[2]:
            TEST_STRING = '[{"scenarios": [{"levels": [{"range": "NIST-level1.yml", "name": "Level 1 (Easy)"}, {"range": "NIST-level2.yml", "name": "Level 2 (Medium)"}, {"range": "NIST-level3.yml", "name": "Level 3 (Hard)"}], "name": "NIST Information Security Testing and Assessment"}, {"levels": [{"range": "IR-level1.yml", "name": "Level 1 (Detection)"}, {"range": "IR-level2.yml", "name": "Level 2 (Forensics)"}, {"range": "IR-level3.yml", "name": "Level 3 (Response)"}], "name": "Incident Response"}]}]'
            print SEPARATO2
            print "TEST #3: Get training information from JSON string: %s." % (
                TEST_STRING)
            print SEPARATO2
            training_info = TrainingInfo()
            training_info.parse_JSON_data(TEST_STRING)
            training_info.pretty_print()
    
    except IOError as error:
        print "ERROR: %s." % (error)
