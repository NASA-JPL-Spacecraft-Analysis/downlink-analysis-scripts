"""
Code that handles loading param.json and returns data.
"""

import json
import sys

###############################################################################
# GET PARAM.JSON
###############################################################################

def get_param_json_values(file_path):
    """Return param.json data from file path."""
    try:
        with open(file_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        sys.exit(f'ERROR: file \'{file_path}\' cannot be found.')
    
