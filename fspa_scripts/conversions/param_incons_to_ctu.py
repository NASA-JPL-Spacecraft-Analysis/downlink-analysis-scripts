#!/usr/bin/env python
import argparse
import json
import numbers
import os
import sys
import logging
import requests
from pathlib import Path

from close_the_u import state_data_store
from typing import Dict, List

TYPE = "fsw_parameter"
VALUE_TYPE = "PREDICTED"

# setup logging
FORMAT = "[%(levelname)s] [%(asctime)s]: %(message)s"
requests.packages.urllib3.disable_warnings()
logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

###############################################################################
# PARSER TEXT
###############################################################################
PARSER_DESCRIPTION = """CLI for publishing parameter incons or param_json to Clipper State Data Store."""

PARSER_INPUT_HELP = """required arguments:
type        Type of input (seqgen_fincon or param_json) to publish.
input       Input file path for type.
collection  Collection Name for state data store to publish parameters (ex: 'STATE_MANAGER_DEMO')
env         Venue for retrieving parameter values (ex: dev)
"""

###############################################################################
# HELPERS
###############################################################################
def load_json_file(path):
    """Return data from JSON file path."""
    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logging.error("File '{path}' cannot be found.")
        sys.exit()

###############################################################################
# STATE DATA STORE
###############################################################################
def _insert_states(venue: str, states: List[Dict]) -> None:
    response = state_data_store.create_states(states, env=venue)
    if response["data"]["createStates"]["success"] == True:
        logging.info(
            "Successfully inserted {} states into Clipper State Data Store".format(
                len(states)
            )
        )

def build_param_json_states(collection_name, scet, data) -> None:
    """Build list of state data store objects from param_json parameters list."""
    # if incorrect JSON foramt, log and error
    if not 'parameter_file' in data or not 'parameter_list' in data['parameter_file']:
        logging.error("Cannot process param_json JSON file. Expecting 'parameter_list' inside 'parameter_file' object.")
        sys.exit()

    # if no parameters, return empty dataframe for merge
    if not data['parameter_file']['parameter_list']:
        logging.warning(f"No parameters in param_json file.")

    # start building states
    states = []
    for parameter in data['parameter_file']['parameter_list']:
        logging.info("Composing states for parameters from 'param_json'...")

        state = None
        metadata = dict()
        metadata.update({"friendly_type": parameter["friendly_type"]})
        metadata.update({"type": parameter["type"]})
        metadata.update({"enum_name": parameter["enum_name"]})
        metadata.update({"string": parameter["string"]})
        metadata.update({"string_length": parameter["string_length"]})
        metadata.update({"symbolic": parameter["symbolic"]})

        # computed fields
        value = parameter["value"] if parameter["value"] else parameter["string"]

        try:
            state = {
                "scet": scet,
                "collectionName": collection_name,
                "hexId": parameter["id"],
                "name": parameter["name"],
                "version": parameter["version"],
                "type": TYPE,
                "value": value if isinstance(value, numbers.Number) else -99999, # using same logic as publish_fsw_params.py
                "value_type": VALUE_TYPE, # this should always be 'predicted' but it exists in param_json (parameter["value_type"].upper())
                "metadata": metadata
            }
        except ValueError as err:
            logging.error(err)
            pass

        if state is not None:
            states.append(state)

    return states


def build_seqgen_fincon_states(collection_name, scet, data) -> None:
    """Build list of state data store objects from seqgen_fincon JSON."""
    # if incorrect JSON foramt, log and error
    if not isinstance(data, list):
        logging.error("seqgen_fincon JSON file is not a list.")
        sys.exit()

    # if no parameters, return empty dataframe for merge
    if not data:
        logging.warning(f"No parameters in seqgen_fincon file.")

    # start building states
    states = []
    for parameter in data:
        logging.info("Composing states for parameters from 'seqgen_fincon'...")

        state = None
        metadata = dict()
        metadata.update({"fincon_name": parameter["fincon_name"]})
        metadata.update({"type": parameter["type"]})

        try:
            state = {
                "scet": scet,
                "collectionName": collection_name,
                "hexId": parameter["id"],
                "name": parameter["name"],
                "version": parameter["version"],
                "type": TYPE,
                "value": parameter["value"] if isinstance(parameter["value"], numbers.Number) else -99999, # using same logic as publish_fsw_params.py
                "value_type": VALUE_TYPE, # this should always be 'predicted'
                "metadata": metadata
            }
        except ValueError as err:
            logging.error(err)
            pass

        if state is not None:
            states.append(state)

        return states
###############################################################################
# RUN MAIN
###############################################################################
def main():
    parser = argparse.ArgumentParser(
        description=PARSER_DESCRIPTION, 
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-t", "--type", required=True, choices=['seqgen_fincon'], help="Type of input (seqgen_fincon) to publish.") # removed 'param_json' type for now
    parser.add_argument("-i", "--input", required=True, help="Input file path for type.")
    parser.add_argument("--scet", required=True, type=str, help="A SCET formatted time this input file was generated with that will be published to CSDS.")
    parser.add_argument("-c", "--collection", required=True, help="Name of the data store collection to publish parasol data (ex: eurcits001-578).")
    parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    args = parser.parse_args()

    # validate file path is .json
    if Path(os.path.basename(args.input)).suffix != '.json':
        sys.exit(f"Input type '{args.type}' expects JSON file. You provided: {args.input}")
    
    data = load_json_file(args.input)

    states = []
    if args.type == 'param_json':
        states = build_param_json_states(args.collection, args.scet, data)
    elif args.type == 'seqgen_fincon':
        states = build_seqgen_fincon_states(args.collection, args.scet, data)
    else:
        logging.error("Unrecognized 'type'. Please see 'param_incons_to_ctu -h' for help.")
        sys.exit()

    logging.info("Composed {} states for input: {}".format(len(states), args.input))
    _insert_states(args.env, states)

if __name__ == "__main__":
    main()
