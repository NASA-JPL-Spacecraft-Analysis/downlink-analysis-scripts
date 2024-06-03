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
        logging.error(f"File '{path}' cannot be found.")
        sys.exit()
    
###############################################################################
# SEQGEN FINCONS TO PANDAS
###############################################################################

def create_df_from_seqgen_fincon(data):
    """Return pandas DataFrame from param.json data."""
    rows_list = []

    if not isinstance(data, list):
        logging.error("seqgen_fincon JSON file is not a list.")
        sys.exit()

    # if no parameters, return empty dataframe for merge
    if not data:
        logging.warning(f"No parameters in seqgen_fincon file.")
        return pd.DataFrame(columns=['name', 'value'])
    
    for parameter in data:
        rows_list.append({
            "name": parameter['name'],
            "id": parameter['id'],
            "version": parameter['version'],
            "fincon_name": parameter['fincon_name'],
            "value": str(parameter['value']),
        })
    
    return pd.DataFrame(rows_list)
