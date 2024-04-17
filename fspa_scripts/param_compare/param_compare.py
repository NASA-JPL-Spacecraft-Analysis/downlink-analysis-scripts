#!/usr/bin/env python

"""
FSW parameter comparison script. Compare Parasol, param.json, SEQGEN fincons, 
and/or CSDS with one another and view a human-readable output in XLSX or JSON.
"""

import argparse
import json
import os
import pathlib
import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.parasol import get_parasol_values, create_df_from_parasol
from utils.param_json import get_param_json_values, create_df_from_param_json
from utils.seqgen_fincon import get_seqgen_fincon_values, create_df_from_seqgen_fincon
from utils.csds import get_csds_values, create_df_from_csds

from utils.compare import compare_parameters

###############################################################################
# PARSER
###############################################################################
def create_parser():
    """Create CLI argument parser."""
    # Create parent parser for shared arguments
    parent_parser = argparse.ArgumentParser(add_help=False) 

    parent_parser.add_argument(
        "-o", "--output", 
        type=pathlib.Path, 
        metavar='PATH', 
        help="Path to desired output location."
    )

    parent_parser.add_argument(
        "--verbose", 
        action='store_true', 
        help="Include all data from compared files in output."
    )
    
    parent_parser.add_argument(
        "--diff-only", 
        dest="diff_only",
        action='store_true', 
        help="Only output parameters that do not match."
    )
    
    parent_parser.add_argument(
        "--intersect-only", 
        dest="intersect_only",
        action='store_true', 
        help="Only output parameters that exist in both inputs."
    )

    # TODO: consider converting to 'choices' argument with 'xlsx (default)', 'json', or 'pandas'
    parent_parser.add_argument(
        "--to-json", 
        dest="to_json",
        action='store_true', 
        help="Output comparison as JSON."
    )

    parser = argparse.ArgumentParser(description="CLI for comparing parameter JSON and parasol queries.")
    subparsers = parser.add_subparsers(title='command', dest='command', required=True)

    # CREATE PARASOL-PARASOL PARSER
    parasol_only_parser = subparsers.add_parser(
        "parasol",
        description="Compare parasol query with parasol query.",
        parents=[parent_parser]
    )
    parasol_only_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_only_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_only_parser.add_argument("--scet1", required=True, help="A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--scet2", required=True, help="A SCET formatted time for parasol query 2 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_only_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values (ex: dev)")
    
    # CREATE PARASOL-JSON PARSER
    parasol_json_parser = subparsers.add_parser(
        "parasol_json",
        description="Compare parasol query with param.json.",
        parents=[parent_parser]
    )
    parasol_json_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_json_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_json_parser.add_argument("--scet", required=True, help="A SCET formatted time (ex: 2023-136T22:08:51.038)")
    parasol_json_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_json_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values (ex: dev)")
    parasol_json_parser.add_argument("--json", required=True, type=pathlib.Path, metavar='PATH', help="param.json to use for comparison")

    # CREATE JSON-JSON PARSER
    json_only_parser = subparsers.add_parser(
        "json",
        description="Compare param.json with param.json.",
        parents=[parent_parser]
    )
    json_only_parser.add_argument("--json1", required=True, type=pathlib.Path, metavar='PATH', help="Path to first param.json to generate comparison")
    json_only_parser.add_argument("--json2", required=True, type=pathlib.Path, metavar='PATH', help="Path to second param.json to generate comparison")

    # CREATE JSON-JSON PARSER
    seqgen_fincon_only_parser = subparsers.add_parser(
        "seqgen_fincon",
        description="Compare seqgen_fincon.json with seqgen_fincon.json.",
        parents=[parent_parser]
    )
    seqgen_fincon_only_parser.add_argument("--json1", required=True, type=pathlib.Path, metavar='PATH', help="Path to first seqgen_fincon.json to generate comparison")
    seqgen_fincon_only_parser.add_argument("--json2", required=True, type=pathlib.Path, metavar='PATH', help="Path to second seqgen_fincon.json to generate comparison")

    # CREATE JSON-JSON PARSER
    csds_only_parser = subparsers.add_parser(
        "csds",
        description="Compare CSDS query with CSDS query.",
        parents=[parent_parser]
    )
    csds_only_parser.add_argument("--collection-name", required=True, help="Collection Name for state data store (ex: 'STATE_MANAGER_DEMO')")
    csds_only_parser.add_argument("--scet1", required=True, help="A SCET formatted time (ex: 2023-136T22:08:51.038)")
    csds_only_parser.add_argument("--scet2", required=True, help="A SCET formatted time (ex: 2023-136T22:08:51.038)")
    csds_only_parser.add_argument("--env", default="dev", help="Venue for retrieving command values (ex: dev)")

    return parser

###############################################################################
# HELPERS
###############################################################################
def create_script_directories():
    """Create directories for script."""
    try:
        os.mkdir("data/parasol_responses")
        os.mkdir("data/csds_responses")
        os.mkdir("output")
    except:
        pass

def get_output_path(path):
    """Get or build output path provided by user."""
    output_basepath = Path(path) if path else Path.cwd().joinpath('output')
    output_basepath.mkdir(exist_ok=True)
    return output_basepath

def return_stats(df):
    """Print basic param_compare counts to console and return them."""
    total = df.shape[0]
    matches = df.loc[df['match'] == True].shape[0]
    non_matches = total - matches
    
    # print summary
    print("PARAMETERS:\t", total)
    print('MATCHES:\t', matches)
    print('NON-MATCHES:\t', non_matches)

    # return results for metadata
    return total, matches, non_matches

###############################################################################
# XLSX AND JSON WRITERS
###############################################################################  
def get_metadata_from_args(args):
    """Create CLI argument dictionary with string values for XLSX metadata."""
    arg_dict = args.__dict__;
    metadata = dict()
    for i in arg_dict.keys():
        metadata[i] = str(arg_dict[i])
    return metadata
 
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
# RUN MAIN & PARSE ARGUMENTS
###############################################################################
SUB_COMMANDS = ['parasol', 'param_json', 'seqgen_fincon', 'csds']

def main():
    create_script_directories()
    parser = create_parser()
    args = parser.parse_args()

    # log time the command was called (used for filename and metadata)
    OUTPUT_TIME = datetime.now()

    # COMMAND: compare parasol with parasol
    if args.command == 'parasol':
        response1 = get_parasol_values(args.host, args.session, args.scet1, args.vcid, args.env)
        response2 = get_parasol_values(args.host, args.session, args.scet2, args.vcid, args.env)
        df1 = create_df_from_parasol(response1)
        df2 = create_df_from_parasol(response2)
    
    # COMMAND: compare parasol with param.json
    elif args.command == 'parasol_json':
        response1 = get_parasol_values(args.host, args.session, args.scet, args.vcid, args.env)
        response2 = get_param_json_values(args.json)
        df1 = create_df_from_parasol(response1)
        df2 = create_df_from_param_json(response2)
    
    # COMMAND: compare param.json with param.json
    elif args.command == 'json':
        response1 = get_param_json_values(args.json1)
        response2 = get_param_json_values(args.json2)
        df1 = create_df_from_param_json(response1)
        df2 = create_df_from_param_json(response2)

    # COMMAND: compare param.json with param.json
    elif args.command == 'seqgen_fincon':
        response1 = get_seqgen_fincon_values(args.json1)
        response2 = get_seqgen_fincon_values(args.json2)
        df1 = create_df_from_seqgen_fincon(response1)
        df2 = create_df_from_seqgen_fincon(response2)

    # COMMAND: compare param.json with param.json
    elif args.command == 'csds':
        response1 = get_csds_values(args.collection_name, args.scet1, args.env)
        response2 = get_csds_values(args.collection_name, args.scet2, args.env)
        df1 = create_df_from_csds(response1)
        df2 = create_df_from_csds(response2)
        
    # CREATE METADATA FOR PARAMETERS AND RETURN REGARDLESS OF INPUTS
    df = compare_parameters(df1, df2, args.verbose, args.intersect_only, args.diff_only)

    # print statistics from comparison
    total, match_count, non_match_count = return_stats(df)

    # get metadata
    metadata = get_metadata_from_args(args)
    metadata["Workbook created"] = OUTPUT_TIME.strftime("%Y-%m-%dT%H:%M:%S.%f")
    metadata["Parameters"] = total
    metadata["Matches"] = match_count
    metadata["Non-Matches"] = non_match_count
    
    # return in user-designated format
    output_filename = f'{OUTPUT_TIME.strftime("%Y_%m_%dT%H_%M_%S")}_{args.command}'
    output_filepath = get_output_path(args.output).joinpath(output_filename)
    if args.to_json:
        create_json(df, f"{output_filepath}.json", metadata = dict())
    else:
        create_xlsx(df, f"{output_filepath}.xlsx", metadata)

if __name__ == "__main__":
    main()