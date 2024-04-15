"""
Code that handles queries with parasol-py and returns data.
"""

import parasol
import os
import json

# CONSTANTS
from .constants import PARASOL_HOST, PARASOL_PHASE, COOKIE_NAME

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

def get_parameter_values(host, session, scet, vcid, env):
    """Get and return parasol query based on provided CLI arguments."""

    # create filename for response
    filename = "./data/parasol_responses/{}_{}_{}_{}.json".format(
        host, session, scet, vcid
    )

    if os.path.exists(filename):
        print("Using saved response for Parasol for parameter values...")
        with open(filename) as parasol_parameter_values:
            return json.load(parasol_parameter_values)

    else:
        print("Making request to Parasol for parameter values...")
        venue = _get_env_venue(env)
        try:
            response = parasol.get_parameter_values(
                phase=PARASOL_PHASE,
                auth_type="cam",
                parasol_host=venue["parasol_host"],
                cookie_name=venue["cookie_name"],
                time_str=scet,
                time_type="scet",
                session_host=host,
                session_id=session,
                vcid=vcid,
            )
        except parasol.exceptions.ParasolAuthException as exc:
            print("Oh no! You forgot to login!")
            raise exc
        except parasol.exceptions.ParasolBaseException as exc:
            print("Something else happened!")
            raise exc

        print("Received response from Parasol.")

        with open(filename, "w") as json_file:
            json.dump(
                response, json_file, indent=4, sort_keys=False, separators=(",", ": ")
            )

        return response

