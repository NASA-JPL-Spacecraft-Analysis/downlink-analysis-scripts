"""
Code that handles loading seqgen_fincon and returns data.
"""

import json
import sys
import pandas as pd

###############################################################################
# GET SEQGEN FINCONS
###############################################################################

def get_seqgen_fincon_values(file_path):
    """Return seqgen_fincon data from file path."""
    try:
        with open(file_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        sys.exit(f'ERROR: file \'{file_path}\' cannot be found.')
    
###############################################################################
# SEQGEN FINCONS TO PANDAS
###############################################################################

def create_df_from_seqgen_fincon(data):
    """Return pandas DataFrame from param.json data."""

    # if no parameters, return empty dataframe for merge
    if not data:
        return pd.DataFrame(columns=['name', 'value'])
    
    return pd.json_normalize(data)
