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

def get_csds_values(collection_name, name, scet, env = 'dev'):
    """Get and return state data store query based on provided CLI arguments."""

    # create filename for response
    filename = f"./data/csds_responses/{collection_name}_{name}_{scet}_{env}.json"

    if os.path.exists(filename):
        print("Using saved response for CSDS for parameter values...")
        try:
            with open(filename) as csds_states_values:
                return json.load(csds_states_values)
        except FileNotFoundError:
            sys.exit(f"ERROR: file '{filename}' cannot be found. This shouldn\'t happen.")

    else:
        print("Making request to State Data Store for commands...")
        # venue = _get_env_venue(env)
        try:
            response = state_data_store.sds_states.get_states_by_applicable_time(
                collection_name=collection_name,
                name=name, # looks like we have to call CSDS for every single parameter... probably not efficient. Need to figure out if this is necessary.
                scet=scet,
                env=env
            )
            # print("RESPONSE", response)
        except:
            sys.exit(f"ERROR: Could not get query for parameter name '{name}' collection '{collection_name}' at SCET {scet}.")

        print("Received response from State Data Store.")

        with open(filename, "w") as json_file:
            json.dump(
                response, json_file, indent=4, sort_keys=False, separators=(",", ": ")
            )
            
        if response is None:
            sys.exit(f"ERROR: CSDS response for '{scet}' is 'None'.")
        
        if len(response['data']['stateByApplicableTime']) == 0:
            print(f"WARNING: CSDS query response for '{scet}' has no parameters.")

        return response

###############################################################################
# STATE DATA STORE QUERY TO PANDAS
###############################################################################

def create_df_from_csds(response):
    """Return pandas DataFrame from state data store query JSON data."""
    
    # if no parameters, return empty dataframe for merge
    if not response['data']['stateByApplicableTime']:
        return pd.DataFrame(columns=['name', 'value'])

    return pd.json_normalize(response['data']['stateByApplicableTime'])
