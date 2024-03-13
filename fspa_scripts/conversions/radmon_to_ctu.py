#!/usr/bin/env python3

"""radmon_to_ctu.py

Standalone tool for converting a RadMon .csv output to CTU .csv input.

RadMon .csv files look like this:

    ert,scet,sclk,vcid,STATE_1_NAME,STATE_2_NAME,...,STATE_N_NAME
    2020-001T12:00:00,2020-001T12:00:00,70000,3,12,16,99

We want a format that looks like this:

    name,scet,value,ert,sclk,vcid
    STATE_1_NAME,2020-001T12:00:00,12,2020-001T12:00:00,70000
    STATE_2_NAME,2020-001T12:00:00,16,2020-001T12:00:00,70000
    ...
    STATE_N_NAME,2020-001T12:00:00,99,2020-001T12:00:00,70000
    
"""

import csv
from fspa_scripts.common.arguments import process_simple_io_arguments

OUTPUT_HEADERS = ["name", "scet", "value", "ert", "sclk", "vcid"]


def main():
    args = process_simple_io_arguments()
    reader = csv.reader(args.infile)
    csv_lines = list(reader)
    # extract the names of all states represented in the dataset
    states = csv_lines[0][4:]
    with open(f"{args.outdir}/output.csv", "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(OUTPUT_HEADERS)
        for row in csv_lines[1:]:
            # the first four columns in each row are values that apply to every other state
            # represented by the remaining columns
            ert, scet, sclk, vcid, state_values = (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4:],
            )
            # zip the remaining columns in the rows (state values) with their state names so
            # that we can write out rows in the desired format
            for state, value in zip(states, state_values):
                writer.writerow([state, scet, value, ert, sclk, vcid])


if __name__ == "__main__":
    main()
