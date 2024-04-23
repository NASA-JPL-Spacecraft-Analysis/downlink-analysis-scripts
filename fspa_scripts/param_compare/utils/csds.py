"""
Code that handles queries with close-the-u-py and returns CSDS data.
"""

from close_the_u import state_data_store
import os
import json
import sys
import pandas as pd

###############################################################################
# QUERY STATE DATA STORE
###############################################################################

def get_csds_values(collection_name, env = 'dev'):
    """Get and return state data store query based on provided CLI arguments."""
    filename = f"./data/csds_responses/{collection_name}_{env}.json"

    if os.path.exists(filename):
        print("Using saved response for CSDS for parameter values.")
        try:
            with open(filename) as csds_states_values:
                return json.load(csds_states_values)
        except FileNotFoundError:
            sys.exit(f"ERROR: file '{filename}' cannot be found. This shouldn't happen.")

    else:
        print("Making request to State Data Store for states...")
        try:
            response = state_data_store.sds_states.get_states(
                collection_name=collection_name,
                env=env
            )
        except:
            sys.exit(f"ERROR: Could not get states query for collection '{collection_name}'.")

        print("Received response from State Data Store.")

        with open(filename, "w") as json_file:
            json.dump(
                response, json_file, indent=4, sort_keys=False, separators=(",", ": ")
            )
            
        if response is None:
            sys.exit(f"ERROR: CSDS response for '{collection_name}' is 'None'.")
        
        if len(response['data']['states']) == 0:
            print(f"WARNING: CSDS query response for '{collection_name}' has no parameters.")

        return response

###############################################################################
# STATE DATA STORE QUERY TO PANDAS
###############################################################################

def create_df_from_csds(response):
    """Return pandas DataFrame from state data store query JSON data."""
    
    # if no parameters, return empty dataframe for merge
    if not response['data']['states']:
        return pd.DataFrame(columns=['name', 'value'])

    return pd.json_normalize(response['data']['states'])
