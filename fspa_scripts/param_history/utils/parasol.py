"""
Code that handles queries with parasol-py and returns data.
"""

import parasol
import parasol.exceptions
import os
import json
import sys
import pandas as pd
import logging

# CONSTANTS
from .constants import PARASOL_HOST, PARASOL_PHASE, PARASOL_COPY, COOKIE_NAME

###############################################################################
# HELPERS
###############################################################################

def _get_env_venue(env):
    """Get venue to query parasol by environment."""
    if env == "dev":
        return {
            "parasol_host": PARASOL_HOST,
            "cookie_name": COOKIE_NAME,
        }


###############################################################################
# QUERY PARASOL
###############################################################################

def get_parasol_values(host, session, scet, vcid, volatility, env, csso: bool = False):
    """Get and return parasol query based on provided CLI arguments."""
    filename = f"data/parasol_responses/{host}_{session}_{scet}_{vcid}.json"

    if os.path.exists(filename):
        logging.info("Using saved response for Parasol for parameter values.")
        try:
            with open(filename) as parasol_parameter_values:
                return json.load(parasol_parameter_values)
        except FileNotFoundError as exc:
            logging.error("File '{filename}' cannot be found.")
            sys.exit()

    else:
        logging.info("Making request to Parasol for parameter values...")
        venue = _get_env_venue(env)
        if venue:
            parasol.configure(
                parasol_host=venue["parasol_host"],
                auth_type="cam" if not csso else "csso",
                phase=PARASOL_PHASE,
                cookie_name=venue["cookie_name"] if not csso else "ssosession",
            )
        try:
            response = parasol.get_parameter_values(
                time_str=scet,
                time_type="scet",
                session_host=host,
                session_id=session,
                vcid=vcid,
            )
        except parasol.exceptions.ParasolAuthException as exc:
            logging.error(
                "Please run %r in your terminal.", "cam-login" if not csso else "credss"
            )
            sys.exit()

        except parasol.exceptions.ParasolBaseException as exc:
            logging.error(
                "Parasol exception. Run %r in your terminal and try again. Otherwise ask for support.",
                "cam-login" if not csso else "credss",
            )
            sys.exit()

        logging.info("Received response from Parasol.")

        with open(filename, "w") as json_file:
            json.dump(
                response, json_file, indent=4, sort_keys=False, separators=(",", ": ")
            )
            
        if response is None:
            logging.error(f"ERROR: parasol response for '{scet}' is 'None'.")
            sys.exit()

        return response

###############################################################################
# PARASOL QUERY TO PANDAS
###############################################################################

def create_df_from_parasol(response, vol):
    """Return pandas DataFrame from parasol query JSON data."""
    rows_list = []
    logging.info(f"Groups in parasol query: {len(response.items())}")
    for module_name, module in response.items():
        if not bool(module):
            logging.debug(f"No groups in parasol module '{module_name}'")
            continue

        for group_name, group in module.items():
            if not bool(group):
                logging.debug(f"No copies in parasol module {module_name}, group {group_name}")
                continue

            for parameter_name, parameter in group[PARASOL_COPY].items():
                volatility = 'volatile' if vol == 'vol' else 'non-volatile'
                
                # check if volatility specified by user exists in query
                if not volatility in parameter:
                    new_vol = 'non-volatile' if volatility == 'volatile' else 'non-volatile'
                    if not new_vol in parameter:
                        logging.error(f"No value exists for {parameter_name} in parasol query.")
                        sys.exit()
                    
                    # inform user we're testing different volatility
                    logging.warning(f"Parameter '{parameter_name}' has no {volatility} value. Using {new_vol} value instead.")
                    volatility = new_vol

                rows_list.append({
                    "name": parameter_name, 
                    "value": parameter[volatility]['value'],
                    "module": module_name,
                    "group": group_name,
                    "copy": PARASOL_COPY,
                    "evidence":parameter[volatility]['evidence'],
                    "evidence_status": parameter[volatility]['evidence_status']
                })

    # if no parameters, return empty dataframe for merge
    if not rows_list:
        logging.error(f"No parameters in parasol query.")
        sys.exit()
    
    return pd.DataFrame(rows_list)
