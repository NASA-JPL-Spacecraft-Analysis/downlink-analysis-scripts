"""Push Merlin Resources to State Manager and CSDS

This script pulls time series resource values from an Aerie/Merlin simulation dataset and pushes them to a CTU State 
Data Store (CSDS) instance. The Aerie host must be configured using Aerie-CLI. CSDS authentication is not supported.

Only numeric resources are currently supported. Non-numeric resources will be ignored.
"""

import argparse
import itertools

from aerie_cli.persistent import PersistentConfigurationManager
from aerie_cli.persistent import PersistentSessionManager
from aerie_cli.aerie_host import AerieHostConfiguration
from aerie_cli.utils.sessions import start_session_from_configuration

# from close_the_u.close_the_u.ctu_states import create_states as create_csds_states
from close_the_u.state_data_store import create_states as create_csds_states

from fspa_scripts.ctu_merlin.utils.aerie_interface import CTUAerieClient, ResourceProfile
from fspa_scripts.ctu_merlin.utils.converters import value_schema_to_sm, resource_to_csds, tag_csds_data


def main(raw_args=None):

    host_configurations = PersistentConfigurationManager.get_configurations()

    parser = argparse.ArgumentParser(description=__doc__)
    # TODO include if we want to add SM interation
    # parser.add_argument(
    #     "--sm-collection",
    #     required=True,
    #     help="ID of the State Manager collection"
    # )
    parser.add_argument(
        "--csds-protocol",
        required=False,
        help="Transfer protocol for CSDS host. Either http or https",
        default="http"
    )
    parser.add_argument(
        "--csds-host",
        required=False,
        help="CSDS Host; either 'local' or 'dev'",
        default="local"
    )
    parser.add_argument(
        "--csds-collection",
        required=True,
        help="ID of the CSDS collection"
    )
    parser.add_argument(
        "--aerie-host",
        required=False,
        help="Specify a different host from local Aerie CLI configuration by name. Available hosts: " +
        ", ".join([hc.name for hc in host_configurations]) +
        ". Defaults to active session"
    )
    parser.add_argument(
        "--sim-dataset-id",
        required=True,
        help="Source simulation dataset ID",
        type=int
    )
    parser.add_argument(
        "--resources",
        required=False,
        help="Specify particular resources to push. Defaults to all",
        nargs="+"
    )

    args = parser.parse_args(raw_args)

    # Use either the active Aerie CLI session or start a session for the user-specified config
    if args.aerie_host:

        try:
            hc: AerieHostConfiguration = next(filter(lambda hc: hc.name ==
                                                     args.aerie_host, host_configurations))
        except StopIteration:
            raise ValueError(
                f"Unknown aerie host. Configure aerie hosts with `aerie-cli configurations`.")

        ah = start_session_from_configuration(hc)
        aerie_client = CTUAerieClient(ah)
    else:
        aerie_client = CTUAerieClient(
            PersistentSessionManager.get_active_session())

    # Pull some initial metadata
    simulation_start_time = aerie_client.get_simulation_start_time(
        args.sim_dataset_id)
    plan_id = aerie_client.get_plan_id_by_sim_id(args.sim_dataset_id)

    # Get all resource names if none are specified
    if args.resources:
        resource_names = args.resources
    else:
        resource_names = aerie_client.get_resource_names(args.sim_dataset_id)

    for resource_name in resource_names:
        try:
            # Get the final resource profile for this resource from Aerie
            print(
                f"Downloading profile segments for resource: {resource_name}")
            resource_profile = aerie_client.get_resource_profile(
                resource_name, args.sim_dataset_id)
            print(f"Download complete for resource: {resource_name}")
        except RuntimeError:
            print(
                f"Failed to get profile segments for resource: {resource_name}")
            continue

        # Convert resource profile to format of CSDS data record
        print(f"Processing profile segments for resource: {resource_name}")
        csds_states = list(itertools.chain.from_iterable([resource_to_csds(
            resource_profile.name,
            resource_profile.type.schema,
            p.dynamics,
            simulation_start_time + p.start_offset
        ) for p in resource_profile.profile_segments]))

        # Tag the CSDS data record with other data fields
        csds_states = tag_csds_data(
            csds_states,
            collectionName=args.csds_collection,
            planId=str(plan_id),
            runId=str(args.sim_dataset_id)
        )
        print(f"Processed profile segments for resource: {resource_name}")

        print(f"Uploading states to CSDS for resource: {resource_name}")
        create_csds_states(
            [c.to_dict() for c in csds_states],
            env=args.csds_host
        )
        print(f"Uploaded states to CSDS for resource: {resource_name}")


if __name__ == "__main__":
    main()
