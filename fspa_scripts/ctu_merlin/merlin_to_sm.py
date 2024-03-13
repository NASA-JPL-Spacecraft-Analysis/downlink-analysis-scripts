"""Pull state information from Merlin and upload to State Manager
"""

import json
import argparse
from pathlib import Path
from typing import List, Union, Sequence

from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.utils.sessions import start_session_from_configuration
from aerie_cli.persistent import PersistentConfigurationManager
from aerie_cli.aerie_host import AerieHostConfiguration
from aerie_cli.aerie_client import AerieClient

from fspa_scripts.ctu_merlin.data.state_manager import SMState, SMStateEnumeration, SMGroup
from fspa_scripts.ctu_merlin.data.merlin import ValueSchema
from fspa_scripts.ctu_merlin.utils.converters import value_schema_to_sm

STRUCT_DELIMITER = "--"


def main(raw_args: Union[Sequence[str], None] = None):
    args = parse_args(raw_args)

    # Use either the active Aerie CLI session or start a session for the user-specified config
    if args.aerie_host:
        host_configurations = PersistentConfigurationManager.get_configurations()
        try:
            hc: AerieHostConfiguration = next(filter(lambda hc: hc.name ==
                                                     args.aerie_host, host_configurations))
        except StopIteration:
            raise ValueError(f"Unknown aerie host. Configure aerie hosts with `aerie-cli configurations`.",
                             "Available hosts are:\n" + '\n\t'.join(hc.name for hc in host_configurations))

        ah = start_session_from_configuration(hc)
        aerie_client = AerieClient(ah)

    else:
        aerie_client = get_active_session_client()

    resource_types = aerie_client.get_resource_types(args.model_id)

    # Initialize outputs
    states: List[SMState] = []
    enumerations: List[SMStateEnumeration] = []
    groups: List[SMGroup] = []

    for resource_type in resource_types:
        new_states, new_enumerations, new_groups = value_schema_to_sm(
            resource_type.name, ValueSchema.parse_unknown_schema(resource_type.schema)
        )

        states.extend(new_states)
        enumerations.extend(new_enumerations)
        groups.extend(new_groups)

    if args.output:
        output_basepath = Path(args.output)
    else:
        output_basepath = Path.cwd().joinpath('merlin_to_sm_output')

    output_basepath.mkdir(exist_ok=True)

    with open(output_basepath.joinpath("resource_schema.json"), 'w') as fid:
        json.dump([r.to_dict() for r in resource_types], fid, indent=2)

    with open(output_basepath.joinpath("merlin_states.json"), 'w') as fid:
        json.dump([s.to_dict() for s in states], fid, indent=2)

    with open(output_basepath.joinpath("merlin_enumerations.json"), 'w') as fid:
        json.dump([e.to_dict() for e in enumerations], fid, indent=2)

    with open(output_basepath.joinpath("merlin_groups.json"), 'w') as fid:
        json.dump([g.to_dict() for g in groups], fid, indent=2)


def parse_args(args: Union[Sequence[str], None] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    # Required args
    parser.add_argument("-m", "--model-id", required=True,
                        help="ID of mission model in Aerie instance")

    # Optional args
    parser.add_argument("--aerie-host", required=False,
                        help="Optionally specify a different host from local Aerie CLI configuration by name")
    parser.add_argument("-o", "--output", required=False,
                        help="Path to output folder")

    return parser.parse_args(args)


if __name__ == '__main__':
    main()
