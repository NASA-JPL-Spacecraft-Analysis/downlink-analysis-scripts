#!/usr/bin/env python
import argparse
import json
import os
import parasol
import sys
import pathlib

GROUP = "no_group"
COPY = "COPY_0"

###############################################################################
# HELPERS
###############################################################################
def _get_env_venue(env):
    if env == "dev":
        return {
            "parasol_host": "parasol.eurc-dev.jpl.nasa.gov",
            "cookie_name": "ecDevRhel8Sso",
        }

def get_parameter_values(args):
    """
    Get and return parasol query based on provided CLI arguments.
    """

    # create filename for response
    filename = "./parasol_responses/{}_{}_{}_{}.json".format(
        args.host, args.session, args.scet, args.vcid
    )

    if os.path.exists(filename):
        print("Using saved response for Parasol for parameter values...")
        with open(filename) as parasol_parameter_values:
            return json.load(parasol_parameter_values)

    else:
        print("Making request to Parasol for parameter values...")
        venue = _get_env_venue(args.env)
        try:
            response = parasol.get_parameter_values(
                phase="cruise",
                auth_type="cam",
                parasol_host=venue["parasol_host"],
                cookie_name=venue["cookie_name"],
                time_str=args.scet,
                time_type="scet",
                session_host=args.host,
                session_id=args.session,
                vcid=args.vcid,
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


###############################################################################
# COMPARE FUNCTIONS
###############################################################################
def compare_parasol(args, response1, response2):
    for module_name, module in response1.items():
        print("Comparing parameters for query 1, module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            print(parameter_name)
        print('Done!')

    for module_name, module in response2.items():
        print("Comparing parameters for query 2, module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            print(parameter_name)
        print('Done!')

def compare_parasol_json(args, parasol_response, json_data):
    for module_name, module in parasol_response.items():
        print("Comparing parameters for query 1, module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            print(parameter_name)
        print('Done!')
    # TODO: process/compare json_data

def compare_json(args, json1, json2):
    pass

###############################################################################
# RUN MAIN, ARG PARSER
###############################################################################
def setup():
    """Create missing directories for script."""
    try:
        os.mkdir("parasol_responses")
        os.mkdir("output")
    except:
        pass

def main():
    setup()

    # CREATE PARSER
    parser = argparse.ArgumentParser(description="CLI for comparing parameter JSON and parasol queries.")
    subparsers = parser.add_subparsers(title='command', dest='command')

    # PARASOL-PARASOL PARSER
    parasol_only_parser = subparsers.add_parser(
        "parasol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two parasol queries by time1 and time2.")
    
    parasol_only_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_only_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_only_parser.add_argument("--scet1", required=True, help="A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--scet2", required=True, help="A SCET formatted time for parasol query 2 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_only_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    
    # PARASOL-JSON PARSER
    parasol_json_parser = subparsers.add_parser(
        "parasol_json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two parasol queries by scet1 and scet2.")
    
    parasol_json_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_json_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_json_parser.add_argument("--scet", required=True, help="A SCET formatted time (ex: 2023-136T22:08:51.038)")
    parasol_json_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_json_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    parasol_json_parser.add_argument("--json", required=True, type=pathlib.Path, metavar='PATH', help="param.json to use for comparison")

    # JSON-JSON PARSER
    json_only_parser = subparsers.add_parser(
        "json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two param.json files.")
    
    json_only_parser.add_argument("--json1", required=True, type=pathlib.Path, metavar='PATH', help="Path to first param.json to generate comparison")
    json_only_parser.add_argument("--json2", required=True, type=pathlib.Path, metavar='PATH', help="Path to second param.json to generate comparison")

    args = parser.parse_args()

    # COMPARE TWO PARASOL QUERIES
    if args.command == 'parasol':
        response1 = get_parameter_values(args.host, args.session, args.scet1, args.vcid)
        response2 = get_parameter_values(args.host, args.session, args.scet2, args.vcid)

        if response1 is None:
            sys.exit(f'ERROR: parasol query for \'{args.scet1}\' returned \'None\'.')

        if response2 is None:
            sys.exit(f'ERROR: parasol query for \'{args.scet2}\' returned \'None\'.')
        
        # OR we can implement parameter_values_diff, which returns 
        compare_parasol(args, response1, response2)
    
    # COMPARE A PARASOL QUERY WITH PARAM JSON
    elif args.command == 'parasol_json':
        parasol = get_parameter_values(args.host, args.session, args.scet, args.vcid)

        try:
            with open(args.json, "r") as json_file:
                json_data = json.load(json_file)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json1}\' cannot be found.')

        compare_parasol_json(args, parasol, json_data)
    
    # COMPARE TWO PARAM JSON
    elif args.command == 'json':
        try:
            with open(args.json1, "r") as json_file1:
                json_data1 = json.load(json_file1)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json1}\' cannot be found.')
    
        try:
            with open(args.json1, "r") as json_file2:
                json_data2 = json.load(json_file2)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json1}\' cannot be found.')

        compare_json(args, json_data1, json_data2)


if __name__ == "__main__":
    main()
    

"""
TODO:
- Compare one parameter json file to another: examples
- Initial tests param-checker#29 ()
- Compare one parasol query result to another
- Compare parasol query result to parameter json
"""