"""
Code that handles loading seqgen_fincon.json and returns data.
"""

import json
import sys
import pandas as pd
import logging

###############################################################################
# GET SEQGEN FINCONS
###############################################################################

def get_seqgen_fincon_values(path):
    """Return seqgen_fincon data from file path."""
    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logging.error("File '{path}' cannot be found.")
        sys.exit()
    
###############################################################################
# SEQGEN FINCONS TO PANDAS
###############################################################################

def create_df_from_seqgen_fincon(data):
    """Return pandas DataFrame from param.json data."""

    if not isinstance(data, list):
        logging.error("seqgen_fincon JSON file is not a list.")
        sys.exit()

    # if no parameters, return empty dataframe for merge
    if not data:
        logging.warning(f"No parameters in seqgen_fincon file.")
        return pd.DataFrame(columns=['name', 'value'])
    
    return pd.json_normalize(data)
