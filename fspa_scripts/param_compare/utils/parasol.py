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
from typing import Any, Dict, Tuple

# CONSTANTS
from .constants import PARASOL_PHASE, PARASOL_COPY

###############################################################################
# HELPERS
###############################################################################

def _get_env_venue(env: str, auth_type: str) -> Tuple:
    """Get venue to query parasol by environment."""
    venue = None

    if env == "dev":
        venue = {"parasol_host": "parasol.eurc-dev.jpl.nasa.gov", "cookie_name": "ecDevRhel8Sso"}

    if env == "testbed":
        venue = {"parasol_host": "parasol.ectb.awsgw1.jpl.nasa.gov", "cookie_name": "ecProdRhel8Sso"}

    if env == "gdsit":
        venue = {"parasol_host": "parasol.gdsit.eurc.jpl.nasa.gov", "cookie_name": "ecTestCloudSso"}

    if auth_type == 'csso':
        return (venue["parasol_host"], "ssosession")
    else:
        return (venue["parasol_host"], venue["cookie_name"])


def _configure_parasol(env: Dict[str, Any], auth_type: str) -> None:
    host, cookie = _get_env_venue(env, auth_type)
    
    logging.debug(f"Configuring Parasol for {env} with auth type {auth_type}: {host}")
    
    parasol.configure(parasol_host=host, cookie_name=cookie, auth_type=auth_type, phase=PARASOL_PHASE)

###############################################################################
# QUERY PARASOL
###############################################################################

def get_parasol_values(host, session, scet, vcid, volatility, env, auth_type):
    """Get and return parasol query based on provided CLI arguments."""
    filename = f"data/parasol_responses/{host}_{session}_{scet}_{vcid}.json"

    if os.path.exists(filename):
        logging.info("Using saved response for Parasol for parameter values.")
        try:
            with open(filename) as parasol_parameter_values:
                return json.load(parasol_parameter_values)
        except FileNotFoundError as exc:
            logging.error(f"File '{filename}' cannot be found.")
            sys.exit()

    else:
        logging.info("Making request to Parasol for parameter values...")
        _configure_parasol(env, auth_type)
        try:
            response = parasol.get_parameter_values(
                time_str=scet,
                time_type="scet",
                session_host=host,
                session_id=session,
                vcid=vcid,
            )
        except parasol.exceptions.ParasolAuthException as exc:
            auth_helper = "credss" if auth_type == 'csso' else "cam-login"
            logging.error(f"Please run {auth_helper} in your terminal.")
            sys.exit()

        except parasol.exceptions.ParasolBaseException as exc:
            auth_helper = "credss" if auth_type == 'csso' else "cam-login"
            logging.error(f"Parasol exception. Run {auth_helper} in your terminal and try again. Otherwise ask for support.")
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
                    "value": str(parameter[volatility]['value']),
                    "module": module_name,
                    "group": group_name,
                    "copy": PARASOL_COPY,
                    "evidence":parameter[volatility]['evidence'],
                    "evidence_status": parameter[volatility]['evidence_status']
                })

    # if no parameters, return empty dataframe for merge
    if not rows_list:
        logging.warning(f"No parameters in parasol query.")
        return pd.DataFrame(columns=['name', 'value'])
    
    return pd.DataFrame(rows_list)
