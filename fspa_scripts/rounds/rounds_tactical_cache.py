#!/usr/bin/env python
import argparse

from typing import Dict

import rounds
import rounds.exceptions


rounds_config = {
    "dev": {"host": "rounds.eurc-dev.jpl.nasa.gov", "cookie": "ecDevRhel8Sso"},
    "testbed": {"host": "rounds.ectb.awsgw1.jpl.nasa.gov", "cookie": "ecProdRhel8Sso"},
    "gdsit": {"host": "rounds.gdsit.eurc.jpl.nasa.gov", "cookie": "ecTestCloudSso"},
    "test": {"host": "rounds.test.eurc.jpl.nasa.gov", "cookie": "ecProdRhel8Sso"},
    "ops": {"host": "rounds.ops.eurc.jpl.nasa.gov", "cookie": "ecOpsCloudSso"},
}


class RoundsEnvException(Exception):
    pass


def _configure_rounds(venue: str) -> None:
    if venue in rounds_config:
        rounds_host = rounds_config[venue]['host']
        cookie_name = rounds_config[venue]['cookie']
        auth_type = 'cam'
    else:
        raise RoundsEnvException(f"Unknown Rounds venue {venue}. Please use --help to view valid venues.")

    print(f"Configuring Rounds for {venue}. Host: {rounds_host} Cookie: {cookie_name}")
    rounds.configure(rounds_host=rounds_host, cookie_name=cookie_name, auth_type=auth_type, phase="cruise")


def _run_rounds_evaluate(session_host: str = None, session_id: str = None, start_scet: str = None, end_scet: str = None) -> Dict:

    print(f"Running Rounds Evaluate Values for: Host: {session_host} | Session: {session_id} | START SCET: {start_scet} | END SCET: {end_scet}")
    print(f"This process does not runs async and will return immediately.")
    try:
        run_id = rounds.evaluate(
            session_host=session_host,
            session_id=session_id,
            time_type='scet',
            start_time=start_scet,
            end_time=end_scet,
            evaluation_type='tact',
            data_provider='chillax-mcws'
        )

        return run_id

    except rounds.exceptions.RoundsAuthException as exc:
        print("Please retry after using cam-login.")
        raise exc
    except rounds.exceptions.RoundsBaseException as exc:
        print("Something unexpected happened!")
        raise exc


def main():
    parser = argparse.ArgumentParser(description="Create tactical results in Rounds")
    parser.add_argument("--host", required=False, help="session host on Rounds (ex: eurcits001)")
    parser.add_argument("--session", required=False, help="session id on Rounds (ex: 578)")
    parser.add_argument("--start-scet", required=True, help="The start SCET of the EOP (ex: 2025-001T00:00:00.0)")
    parser.add_argument("--end-scet", required=True, help="The end SCET of the EOP (ex: 2025-002T00:00:00.0)")
    parser.add_argument("--venue", required=False, default="dev", help="venue for evaluating rounds rules (default: dev)")

    args = parser.parse_args()

    host = args.host
    session = args.session
    start_scet = args.start_scet
    end_scet = args.end_scet
    venue = args.venue

    _configure_rounds(venue)
    run_id = _run_rounds_evaluate(session_host=host, session_id=session, start_scet=start_scet, end_scet=end_scet)

    if run_id:
        print(f"Tactical cache started for: Host: {host} | Session: {session} | START SCET: {start_scet} | END SCET: {end_scet} | Run Id: {run_id}")
    else:
        print(f"No data found for: Host: {host} | Session: {session} | SCET: {start_scet}")


if __name__ == "__main__":
    main()
