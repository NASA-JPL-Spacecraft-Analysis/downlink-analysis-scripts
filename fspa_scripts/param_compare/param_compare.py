#!/usr/bin/env python

"""
FSW parameter comparison script. Compare Parasol queries and/or param.json and 
generate a human-readable output in XLSX or JSON.
"""

# GENERAL IMPORTS
import argparse
import json
import os
import sys
import pathlib
import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.parasol import get_parameter_values
from utils.compare import create_df_from_parasol, create_df_from_param_json, compare_parameters

###############################################################################
# PARSER HELPERS
###############################################################################
def add_subparser(subparsers, name, description):
    """
    Add common arguments for all subparsers to the top-level argument
    parser. Include flags for output path, output verbosity, and which
    parameters to include in output. Sets the formatter class to 
    argparse.RawDescriptionHelpFormatter.
    """
    
    parser = subparsers.add_parser(
        name,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    
    parser.add_argument(
        "-o", "--output", 
        type=pathlib.Path, 
        metavar='PATH', 
        help="Path to desired output location."
    )

    parser.add_argument(
        "--verbose", 
        action='store_true', 
        help="Include all data from compared files in output."
    )
    
    parser.add_argument(
        "--diff-only", 
        dest="diff_only",
        action='store_true', 
        help="Only output parameters that do not match."
    )
    
    parser.add_argument(
        "--intersect-only", 
        dest="intersect_only",
        action='store_true', 
        help="Only output parameters that exist in both inputs."
    )

    parser.add_argument(
        "--to-json", 
        dest="to_json",
        action='store_true', 
        help="Output comparison as JSON."
    )

    return parser

###############################################################################
# XLSX HELPERS
###############################################################################   
def add_metadata_worksheet(workbook, metadata):
    """Add dictionary as table to a worksheet called 'metadata'."""
    # Add metadata worksheet to a workbook
    metadata_worksheet = workbook.add_worksheet("metadata")
    bold_format = workbook.add_format({'bold': True})
    metadata_worksheet.set_column(0, 0, 25, bold_format)
    metadata_worksheet.set_column(1, 1, 25)
    i = 0
    for name, meta in metadata.items():
        metadata_worksheet.write_row(i, 0, [name, meta])
        i += 1
    return workbook

def create_xlsx(df, filename, metadata = dict()):
    """Create XLSX file from pandas dataframe."""
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    
    # Sort rows with matches first; then alphabetical by parameter name
    df.sort_values(by=['match', 'name'], ascending=[False, True], inplace=True)
    
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name="compare")
    
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    compare_worksheet = writer.sheets["compare"]
    
    # make cell formats to use in conditional formatting, metadata
    green_format = workbook.add_format({'bg_color':   '#C6EFCE','font_color': '#006100'})
    # yellow_format = workbook.add_format({'bg_color':   '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color':   '#FFC7CE','font_color': '#9C0006'})
    
    # set better column widths for compare
    name_col = 1 + df.columns.get_loc("name")
    value_1_col = 1 + df.columns.get_loc("value_1")
    value_2_col = 1 + df.columns.get_loc("value_2")
    match_col = 1 + df.columns.get_loc("match")
    
    compare_worksheet.set_column(name_col, name_col, 45) # 'name'
    compare_worksheet.set_column(value_1_col, value_1_col, 20) # 'value_1'
    compare_worksheet.set_column(value_2_col, value_2_col, 20) # 'value_2'
    compare_worksheet.set_column(match_col, match_col, 20) # 'match'

    # Get the dimensions of the dataframe.
    (max_row, max_col) = df.shape

    # Apply a conditional format to the required cell range.
    compare_worksheet.conditional_format(1, max_col, max_row, max_col, {
        "type": "cell",
        "criteria": "==",
        "value": "TRUE",
        "format": green_format
    })

    compare_worksheet.conditional_format(1, max_col, max_row, max_col, {
        "type": "cell",
        "criteria": "==",
        "value": "FALSE",
        "format": red_format
    })

    add_metadata_worksheet(workbook, metadata)

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()

def create_json(df, filename, metadata = dict()):
    """Create JSON file from pandas dataframe."""
    data = json.loads(df.to_json(orient='records'))
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4, sort_keys=False, separators=(",", ": "))

###############################################################################
# COMPARE FUNCTIONS
###############################################################################

def compare_parasol(args, response1, response2):
    """Compare parasol query to parasol query and generate output."""
    df1 = create_df_from_parasol(response1)
    df2 = create_df_from_parasol(response2)
    df = compare_parameters(df1, df2, args.verbose, args.intersect_only, args.diff_only)
    
    # print statistics from comparison
    total, match_count, non_match_count = return_stats(df)
    OUTPUT_TIME = datetime.now()
    OUTPUT_FILENAME = f'{OUTPUT_TIME.strftime("%Y_%m_%dT%H_%M_%S")}_parasol_parasol'
    OUTPUT_FILEPATH = get_output_path(args.output).joinpath(OUTPUT_FILENAME)
    metadata = {
        "Host:": args.host,
        "Session:": f"{args.session}",
        "SCET 1:": args.scet1,
        "SCET 2:": args.scet2,
        "VCID:": f"{args.vcid}",
        "env:": args.env,
        "Workbook created:": OUTPUT_TIME.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "Parameter Count:": total,
        "Matches:": match_count,
        "Non-Matches:": non_match_count,
    }
    
    if args.to_json:
        create_json(df, f"{OUTPUT_FILEPATH}.json", metadata = dict())
    else:
        create_xlsx(df, f"{OUTPUT_FILEPATH}.xlsx", metadata)
    
def compare_parasol_json(args, parasol_response, json_data):
    """Compare parasol query to param.json and generate output."""
    df1 = create_df_from_parasol(parasol_response)
    df2 = create_df_from_param_json(json_data)
    df = compare_parameters(df1, df2, args.verbose, args.intersect_only, args.diff_only)

    # print statistics from comparison
    total, match_count, non_match_count = return_stats(df)
    OUTPUT_TIME = datetime.now()
    OUTPUT_FILENAME = f'{OUTPUT_TIME.strftime("%Y_%m_%dT%H_%M_%S")}_parasol_json'
    OUTPUT_FILEPATH = get_output_path(args.output).joinpath(OUTPUT_FILENAME)
    metadata = {
        "Host:": args.host,
        "Session:": f"{args.session}",
        "SCET:": args.scet,
        "JSON PATH:": str(args.json),
        "VCID:": f"{args.vcid}",
        "env:": args.env,
        "Workbook created:": OUTPUT_TIME.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "Parameter Count:": total,
        "Matches:": match_count,
        "Non-Matches:": non_match_count,
    }

    if args.to_json:
        create_json(df, f"{OUTPUT_FILEPATH}.json", metadata = dict())
    else:
        create_xlsx(df, f"{OUTPUT_FILEPATH}.xlsx", metadata)

def compare_json(args, json1, json2):
    """Compare param.json to param.json and generate output."""
    df1 = create_df_from_param_json(json1)
    df2 = create_df_from_param_json(json2)
    df = compare_parameters(df1, df2, args.verbose, args.intersect_only, args.diff_only)

    # print statistics from comparison
    total, match_count, non_match_count = return_stats(df)
    OUTPUT_TIME = datetime.now()
    OUTPUT_FILENAME = f'{OUTPUT_TIME.strftime("%Y_%m_%dT%H_%M_%S")}_json_json'
    OUTPUT_FILEPATH = get_output_path(args.output).joinpath(OUTPUT_FILENAME)
    metadata = {
        "JSON 1 PATH:": str(args.json1),
        "JSON 2 PATH:": str(args.json2),
        "Workbook created:": OUTPUT_TIME.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "Parameter Count:": total,
        "Matches:": match_count,
        "Non-Matches:": non_match_count,
    }

    if args.to_json:
        create_json(df, f"{OUTPUT_FILEPATH}.json", metadata = dict())
    else:
        create_xlsx(df, f"{OUTPUT_FILEPATH}.xlsx", metadata)

###############################################################################
# RUN MAIN, ARG PARSER
###############################################################################
def create_script_directories():
    """Create directories for script."""
    try:
        os.mkdir("data/parasol_responses")
        os.mkdir("output")
    except:
        pass

def get_output_path(path):
    """Get or build output path provided by user."""
    output_basepath = Path(path) if path else Path.cwd().joinpath('output')
    output_basepath.mkdir(exist_ok=True)
    return output_basepath

def return_stats(df):
    """Get and print basic compare stats."""
    total = df.shape[0]
    matches = df.loc[df['match'] == True].shape[0]
    non_matches = total - matches
    
    # print summary
    print("PARAMETER COUNT:", total)
    print('MATCHES:', matches)
    print('NON-MATCHES:', non_matches)

    # return results for metadata
    return total, matches, non_matches

def main():
    create_script_directories()

    # CREATE PARSER
    parser = argparse.ArgumentParser(description="CLI for comparing parameter JSON and parasol queries.")
    subparsers = parser.add_subparsers(title='command', dest='command')

    # PARASOL-PARASOL PARSER
    parasol_only_parser = add_subparser(
        subparsers,
        "parasol",
        description="Compare two parasol queries between scet1 and scet2."
    )
    parasol_only_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_only_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_only_parser.add_argument("--scet1", required=True, help="A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--scet2", required=True, help="A SCET formatted time for parasol query 2 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_only_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    
    # PARASOL-JSON PARSER
    parasol_json_parser = add_subparser(
        subparsers,
        "parasol_json",
        description="Compare two parasol queries by scet1 and scet2."
    )
    parasol_json_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_json_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_json_parser.add_argument("--scet", required=True, help="A SCET formatted time (ex: 2023-136T22:08:51.038)")
    parasol_json_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_json_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    parasol_json_parser.add_argument("--json", required=True, type=pathlib.Path, metavar='PATH', help="param.json to use for comparison")

    # JSON-JSON PARSER
    json_only_parser = add_subparser(
        subparsers, 
        "json", 
        description="Compare two param.json files."
    )
    json_only_parser.add_argument("--json1", required=True, type=pathlib.Path, metavar='PATH', help="Path to first param.json to generate comparison")
    json_only_parser.add_argument("--json2", required=True, type=pathlib.Path, metavar='PATH', help="Path to second param.json to generate comparison")

    # parse arguments
    args = parser.parse_args()

    # COMPARE TWO PARASOL QUERIES
    if args.command == 'parasol':
        response1 = get_parameter_values(args.host, args.session, args.scet1, args.vcid, args.env)
        response2 = get_parameter_values(args.host, args.session, args.scet2, args.vcid, args.env)

        if response1 is None:
            sys.exit(f'ERROR: parasol query for \'{args.scet1}\' returned \'None\'.')
        if response2 is None:
            sys.exit(f'ERROR: parasol query for \'{args.scet2}\' returned \'None\'.')
        
        # OR we can implement parameter_values_diff, which returns 
        compare_parasol(args, response1, response2)
    
    # COMPARE A PARASOL QUERY WITH PARAM JSON
    elif args.command == 'parasol_json':
        parasol_response = get_parameter_values(args.host, args.session, args.scet, args.vcid, args.env)

        if parasol_response is None:
            sys.exit(f'ERROR: parasol query for \'{args.scet1}\' returned \'None\'.')

        try:
            with open(args.json, "r") as json_file:
                json_data = json.load(json_file)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json1}\' cannot be found.')

        compare_parasol_json(args, parasol_response, json_data)
    
    # COMPARE TWO PARAM JSON
    elif args.command == 'json':
        try:
            with open(args.json1, "r") as json_file1:
                json_data1 = json.load(json_file1)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json1}\' cannot be found.')
    
        try:
            with open(args.json2, "r") as json_file2:
                json_data2 = json.load(json_file2)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json2}\' cannot be found.')

        compare_json(args, json_data1, json_data2)


if __name__ == "__main__":
    main()