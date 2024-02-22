#!/usr/bin/env python3

"""chill_to_ctu.py

Standalone tool for converting a chill .csv output to CTU .csv input.

Chill .csv format is subject to change. We expect and extract "name",
"scet", and "value" in a generic way by evaluating what columns exist
in the data at runtime.


We want a format that looks like this:

    name,scet,value,type
    STATE_1_NAME,2020-001T12:00:00,12,predicted
    STATE_2_NAME,2020-001T12:00:00,16,predicted
    ...
    STATE_N_NAME,2020-001T12:00:00,99,predicted
    
"""

import csv
from fspa_scripts.common.arguments import process_simple_io_arguments

OUTPUT_HEADERS = ["name", "scet", "value", "type"]
STATE_TYPE = "predicted"


def main():
    args = process_simple_io_arguments()
    reader = csv.reader(args.infile)
    csv_lines = list(reader)
    with open(f"{args.outdir}/output.csv", "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(OUTPUT_HEADERS)
        for row in csv_lines[1:]:
            datum = dict(zip(csv_lines[0], row))
            writer.writerow([datum["name"], datum["scet"], datum["value"], STATE_TYPE])


if __name__ == "__main__":
    main()
