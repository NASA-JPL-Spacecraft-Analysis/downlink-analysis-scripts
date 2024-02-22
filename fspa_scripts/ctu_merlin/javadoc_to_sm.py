"""Pull state information from Merlin and upload to State Manager
"""

import json
import argparse
from pathlib import Path
from typing import Union, Sequence

from fspa_scripts.ctu_merlin.utils.parse_javadoc_xml import parse_javadoc_xml
from fspa_scripts.ctu_merlin.utils.converters import javadoc_state_to_sm

STRUCT_DELIMITER = "--"


def main(raw_args: Union[Sequence[str], None] = None):
    args = parse_args(raw_args)

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path.cwd().joinpath('javadoc_states_for_sm.json')

    output_file.parent.mkdir(exist_ok=True, parents=True)

    with open(args.javadoc_states, 'r') as fid:
        javadoc_states = parse_javadoc_xml(fid)

    for js in javadoc_states:
        js.docs = js.docs.replace(",", "")

    with open(output_file, "w") as fid:
        json.dump([javadoc_state_to_sm(s) for s in javadoc_states], fid, indent=2)


def parse_args(args: Union[Sequence[str], None] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    # Required args
    parser.add_argument("-i", "--javadoc-states", required=True,
                        help="Path to Javadoc XML state annotations")

    # Optional args
    parser.add_argument("-o", "--output", required=False,
                        help="Path to output file")

    return parser.parse_args(args)


if __name__ == '__main__':
    main()
