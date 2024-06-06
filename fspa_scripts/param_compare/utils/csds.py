"""
Code that handles queries with close-the-u-py and returns CSDS data.
"""

from close_the_u import state_data_store
import os
import json
import sys
import pandas as pd
import logging

###############################################################################
# QUERY STATE DATA STORE
###############################################################################

def get_csds_values(collection_name, env = 'dev'):
    """Get and return state data store query based on provided CLI arguments."""
    logging.info("Making request to State Data Store for states...")
    try:
        response = state_data_store.sds_states.get_states(
            collection_name=collection_name,
            env=env
        )
    except:
        logging.error(f"Failed query to CSDS 'get_states' for collection '{collection_name}'.")
        sys.exit()

    logging.info("Received response from State Data Store.")
        
    if response is None:
        logging.error(f"CSDS response for '{collection_name}' is 'None'.")
        sys.exit()

    return response

###############################################################################
# STATE DATA STORE QUERY TO PANDAS
###############################################################################

def create_df_from_csds(response):
    """Return pandas DataFrame from state data store query JSON data."""
    
    # if no parameters, return empty dataframe for merge
    if not response['data']['states']:
        logging.warning(f"No parameters in CSDS query.")
        return pd.DataFrame(columns=['name', 'value'])

    return pd.json_normalize(response['data']['states'])
