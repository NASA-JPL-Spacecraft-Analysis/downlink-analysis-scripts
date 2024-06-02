#!/usr/bin/env python
import argparse
import json
import numbers
import os
import sys

from typing import Any, Dict, List, Optional, Tuple

import parasol
from close_the_u import state_data_store

TYPE = "fsw_parameter"
VALUE_TYPE = "MEASURED"
GROUP = "no_group"
COPY = "COPY_0"


def _get_env_venue(env: str, auth_type: str) -> Tuple:
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

    print(f"Configuring Parasol for {env} with auth type {auth_type}: {host}")
    parasol.configure(parasol_host=host, cookie_name=cookie, auth_type=auth_type, phase="cruise")


def _insert_states(env: str, states: List[Dict]) -> None:
    response = state_data_store.create_states(states, env=env)

    if response["data"]["createStates"]["success"] == True:
        print("Successfully inserted {} states into Clipper State Data Store".format(len(states)))


def _compose_state(
    args: Dict[str, Any], parameter_name: str, volatility: str, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    state = None

    value = data["value"]
    evidence = data["evidence"][0]

    state = {
        "sessionId": args.session,
        "collectionName": args.collection,
        "name": parameter_name,
        "scet": evidence["scet"],
        "volatility": volatility,
        "cpu": str(args.vcid),
        "value": value if isinstance(value, numbers.Number) else -99999,
    }

    if state is not None:
        defaults = {"type": TYPE, "valueType": VALUE_TYPE}
        state.update(defaults)

    return state


def _get_parameter_values(args: Dict[str, Any]) -> Dict[str, Any]:
    filename = "./parasol_responses/{}_{}_{}_{}.json".format(args.host, args.session, args.start_scet, args.vcid)

    if os.path.exists(filename):
        print("Using saved response for Parasol for parameter values")
        with open(filename) as parasol_parameter_values:
            return json.load(parasol_parameter_values)

    else:
        try:
            print("Making request to Parasol for parameter values")
            # response = parasol.get_parameter_values(
            #     phase="cruise",
            #     time_str=args.start_scet,
            #     time_type="scet",
            #     session_host=args.host,
            #     session_id=args.session,
            #     vcid=args.vcid,
            # )
            response = parasol.get_parameter_values_history(
                phase="cruise",
                session_host = args.host, 
                session_id = args.session, 
                end_time = args.end_scet, 
                end_time_type="scet",
                start_time = args.start_scet, 
                start_time_type="scet",
                vcid=args.vcid,
            )
            print("Received response from Parasol")

            with open(filename, "w") as json_file:
                json.dump(response, json_file, indent=4, sort_keys=False, separators=(",", ": "))

            return response
        except parasol.exceptions.ParasolAuthException as exc:
            auth_helper = "credss" if args.auth_type == 'csso' else "cam-login"
            print(f"Please run {auth_helper} in your terminal.")
            sys.exit()

        except parasol.exceptions.ParasolBaseException as exc:
            auth_helper = "credss" if args.auth_type == 'csso' else "cam-login"
            print(f"Parasol exception. Run {auth_helper} in your terminal and try again. Otherwise ask for support.")
            sys.exit()


def _compose_states_and_insert(args: Dict[str, Any], response: Dict[str, Any]) -> None:
    for module_name, module in response.items():
        states = []
        print("Composing states for module {}".format(module_name))

        for group_name, group in module.items():
            if not bool(group):
                continue

            for parameter_name, parameter in group[COPY].items():
                for volatility, data in parameter.items():
                    csds_volatility = volatility.replace("-", "_").upper()
                    if csds_volatility in [member.value for member in state_data_store.enum_classes["volatility"]]:

                        try:
                            if isinstance(data, list):
                                data = data[0]

                            state = _compose_state(args, parameter_name, csds_volatility, data)

                            if state is not None:
                                states.append(state)

                        except ValueError as err:
                            print(err)
                            pass

        print("Composed {} states for module: {}".format(len(states), module_name))
        _insert_states(args.env, states)


def setup():
    try:
        os.mkdir("parasol_responses")
    except:
        pass


def main():
    setup()

    parser = argparse.ArgumentParser(description="Publish FSW Parameters from Parasol to Clipper State Data Store")
    parser.add_argument("--host", required=True, help="session host on parasol (ex: eurcits001)")
    parser.add_argument("--session", required=True, help="session id on parasol (ex: 578)")
    parser.add_argument(
        "--start-scet",
        required=True,
        help="a scet formatted time (ex: 2023-136T22:08:51.038)",
    )
    parser.add_argument(
        "--end-scet",
        required=True,
        help="a scet formatted time (ex: 2023-136T22:08:51.038)",
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="name of the data store collection to publish parasol data (ex: eurcits001-578)",
    )
    parser.add_argument("--vcid", type=int, default=0, help="vcid 0 or 1 (default: 0)")
    parser.add_argument(
        "--env",
        default="dev",
        help="venue for retrieving parameter values and publishing (default: dev)",
    )
    parser.add_argument(
        "--auth-type",
        default="csso",
        help="csso (Parasol with Chillax) or cam (Parasol with MCWS) (default: csso)",
    )
    args = parser.parse_args()

    _configure_parasol(args.env, args.auth_type)
    parasol_response = _get_parameter_values(args)
    print (parasol_response)
    if parasol_response:
        _compose_states_and_insert(args, parasol_response)
    else:
        print(f"No data found for: Host: {args.host} | Session: {args.session} | SCET: {args.start_scet}")


if __name__ == "__main__":
    main()
