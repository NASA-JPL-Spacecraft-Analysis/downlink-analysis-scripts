#!/usr/bin/env python
import argparse
import json
import sys

from typing import Dict

import parasol
import parasol.exceptions


parasol_config = {
    "dev": {
        "host": "parasol.eurc-dev.jpl.nasa.gov"
    },
    "testbed": {
        "host": "parasol.ectb.awsgw1.jpl.nasa.gov"
    },
    "gdsit": {
        "host": "parasol.gdsit.eurc.jpl.nasa.gov"
    },
    "test": {
        "host": "parasol.test.eurc.jpl.nasa.gov"
    },
    "ops": {
        "host": "parasol.ops.eurc.jpl.nasa.gov"
    }
}

class ParasolEnvException(Exception):
    pass


def _configure_parasol(venue: str) -> None:
    if venue in parasol_config:
        parasol_host = parasol_config[venue]['host']
        cookie_name = 'ssosession'
        auth_type = 'csso'
    else:
        raise ParasolEnvException("Unknown Parasol venue {}".format(venue))

    print(f"Configuring Parasol for {venue}. Host: {parasol_host} Cookie: {cookie_name}")
    parasol.configure(
        parasol_host=parasol_host,
        cookie_name=cookie_name,
        auth_type=auth_type,
        phase="cruise"
    )


def _get_parameter_values(session_host: str=None, session_id: str=None, start_scet: str=None, end_scet: str=None) -> Dict:

    print(f"Getting Parasol Parameter Values for Start: {start_scet} End: {end_scet}")
    print(f"This process may taken several minutes.")
    try:
        for TIME in [start_scet, end_scet]:
            params = parasol.get_parameter_values(
                session_host=session_host,
                session_id=session_id,
                time_str=TIME,
                time_type='scet',
                vcid=0,
                defaults=False,
                phase='cruise',
                cmd_read_from='telemetry',
                update_tactical=True
            )

        return len(params)

    except parasol.exceptions.ParasolAuthException as exc:
        print("Oh no! You forgot to login!")
        raise exc
    except parasol.exceptions.ParasolBaseException as exc:
        print("Something else happened!")
        raise exc


def main():
    parser = argparse.ArgumentParser(description="Create tactical results in Parasol")
    parser.add_argument("--host", required=False, help="session host on parasol (ex: eurcits001)")
    parser.add_argument("--session", required=False, help="session id on parasol (ex: 578)")
    parser.add_argument("--start-scet", required=True, help="The start SCET of the EOP (ex: 2023-136T22:08:51.038)")
    parser.add_argument("--end-scet", required=True, help="The end SCET of the EOP (ex: 2023-136T22:08:51.038)")
    parser.add_argument("--venue", required=False, default="dev", help="venue for retrieving parameter values and publishing (default: dev)")

    args = parser.parse_args()

    host = args.host
    session = args.session
    start_scet = args.start_scet
    end_scet = args.end_scet
    venue = args.venue

    _configure_parasol(venue)
    parasol_response = _get_parameter_values(session_host=host, session_id=session, start_scet=start_scet, end_scet=end_scet)

    if parasol_response:
        print(f"Tactical cache created for: Host: {host} | Session: {session} | START SCET: {start_scet} | END SCET: {end_scet} ")
    else:
        print(f"No data found for: Host: {host} | Session: {session} | SCET: {start_scet}")


if __name__ == "__main__":
    main()
