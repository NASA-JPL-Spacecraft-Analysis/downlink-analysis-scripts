#!/usr/bin/env python
import argparse
import json
import os
import parasol
from parasol.exceptions import ParasolAuthException, ParasolBaseException

TYPE = "fsw_parameter"
VALUE_TYPE = "MEASURED"
GROUP = "no_group"
COPY = "COPY_0"

"""
TODO:
- Compare one parameter json file to another: examples
- Initial tests param-checker#29 ()
- Compare one parasol query result to another
- Compare parasol query result to parameter json
"""

def _get_env_venue(env):
    if env == "dev":
        return {
            "parasol_host": "parasol.eurc-dev.jpl.nasa.gov",
            "cookie_name": "ecDevRhel8Sso",
        }

def get_parameter_values(args):
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
        except ParasolAuthException as exc:
            print("Oh no! You forgot to login!")
            raise exc
        except ParasolBaseException as exc:
            print("Something else happened!")
            raise exc

        print("Received response from Parasol.")

        with open(filename, "w") as json_file:
            json.dump(
                response, json_file, indent=4, sort_keys=False, separators=(",", ": ")
            )

        return response


def compare_values(args, response):
    for module_name, module in response.items():
        print("Composing states for module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            print(parameter_name)
            # for volatility, data in parameter.items():
            #     if volatility.upper() in [
            #         member.value
            #         for member in state_data_store.enum_classes["volatility"]
            #     ]:

            #         try:
            #             if isinstance(data, list):
            #                 data = data[0]

            #             state = _composeState(
            #                 args, parameter_name, volatility.upper(), data
            #             )
            #             if state is not None:
            #                 states.append(state)

            #         except ValueError as err:
            #             print(err)
            #             pass

        # print("Composed {} states for module: {}".format(len(states), module_name))
        print('Done!')



def setup():
    try:
        os.mkdir("parasol_responses")
    except:
        pass


def main():
    # SETUP PARASOL RESPONSE DIRECTORY
    setup()

    # SETUP PARSER
    parser = argparse.ArgumentParser(
        description="CLI for comparing parameter JSON and parasol queries."
    )

    parser.add_argument(
        "--host",
        required=True,
        help="session host on parasol (ex: eurcits001)"
    )

    parser.add_argument(
        "--session",
        required=True,
        help="session id on parasol (ex: 578)"
    )

    parser.add_argument(
        "--scet",
        required=True,
        help="a SCET formatted time (ex: 2023-136T22:08:51.038)",
    )
    
    parser.add_argument(
        "--vcid",
        type=int,
        default=0,
        help="vcid 0 or 1 (ex: 0)"
    )

    parser.add_argument(
        "--env",
        default="dev",
        help="venue for retrieving parameter values and publishing (ex: dev)",
    )

    args = parser.parse_args()

    # QUERY PARASOL
    parasol_response = get_parameter_values(args)
    results = compare_values(args, parasol_response)

    # RUN PARASOL COMPARE SCRIPT
    print(parasol_response)


if __name__ == "__main__":
    main()