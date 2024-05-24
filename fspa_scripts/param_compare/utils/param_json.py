"""
Code that handles loading param.json and returns data.
"""

import json
import sys
import pandas as pd
import os
import logging

###############################################################################
# GET PARAM.JSON
###############################################################################

def get_param_json_values(path):
    """Return param.json data from file path."""
    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logging.error(f"File '{path}' cannot be found.")
        sys.exit()
    
###############################################################################
# PARAM.JSON TO PANDAS
###############################################################################

def create_df_from_param_json(data):
    """Return pandas DataFrame from param.json data."""
    # if incorrect JSON foramt, log and error
    if not 'parameter_file' in data or not 'parameter_list' in data['parameter_file']:
        logging.error("Cannot process param_json JSON file. Expecting 'parameter_list' inside 'parameter_file' object.")
        sys.exit()

    # if no parameters, return empty dataframe for merge
    if not data['parameter_file']['parameter_list']:
        logging.warning(f"No parameters in param_json file.")
        return pd.DataFrame(columns=['name', 'value'])

    return pd.json_normalize(data['parameter_file']['parameter_list'])
