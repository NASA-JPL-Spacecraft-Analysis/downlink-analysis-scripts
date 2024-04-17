"""
Code that handles loading param.json and returns data.
"""

import json
import sys
import pandas as pd

###############################################################################
# GET PARAM.JSON
###############################################################################

def get_param_json_values(file_path):
    """Return param.json data from file path."""
    try:
        with open(file_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        sys.exit(f"ERROR: file '{file_path}' cannot be found.")
    
###############################################################################
# PARAM.JSON TO PANDAS
###############################################################################

def create_df_from_param_json(data):
    """Return pandas DataFrame from param.json data."""

    # if no parameters, return empty dataframe for merge
    if not data['parameter_file']['parameter_list']:
        return pd.DataFrame(columns=['name', 'value'])

    return pd.json_normalize(data['parameter_file']['parameter_list'])
