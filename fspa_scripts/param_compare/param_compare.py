#!/usr/bin/env python

"""
FSW parameter comparison script. Compare Parasol, param.json, SEQGEN fincons, 
and/or CSDS with one another and view a human-readable output in XLSX or JSON.
"""

import argparse
import json
import os
import sys
import pathlib
import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.parasol import get_parasol_values, create_df_from_parasol
from utils.param_json import get_param_json_values, create_df_from_param_json
from utils.seqgen_fincon import get_seqgen_fincon_values, create_df_from_seqgen_fincon
from utils.csds import get_csds_values, create_df_from_csds

from utils.compare import compare_parameters

from utils.constants import INPUT_TYPES, INPUT_TYPE_ARG_COUNTS

###############################################################################
# PARSER TEXT
###############################################################################
PARSER_DESCRIPTION = """CLI for comparing parameters from several formats: parasol, csds, param.json, seqgen_fincon.json."""

PARSER_INPUT_HELP = """commands: {parasol, param_json, seqgen_fincon, csds}
required arguments:
    parasol:
        host        Session host on parasol (ex: eurcits001)
        session     Session id on parasol (ex: 830)
        scet        A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)
        vcid        VCID 0 or 32 (ex: 0)
        env         Venue for retrieving parameter values (ex: dev)
    param_json:
        path        Path to json file.
    seqgen_fincon:
        path        Path to json file.
    csds:
        collection  Collection Name for state data store (ex: 'STATE_MANAGER_DEMO')
        env         Venue for retrieving parameter values (ex: dev)
"""

###############################################################################
# HELPERS
###############################################################################
def create_directories():
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
def validate_input_arguments(inputs):
    """Validate nargs is used with all required positional arguments."""
    input_type = inputs[0] # should be valid input type
    input_arg_count = len(inputs) - 1

    if input_type not in INPUT_TYPES:
        return sys.exit(f"Input type '{input_type}' does not exist. Valid types are 'parasol', 'param_json', 'seqgen_fincon', or 'csds'.")
    
    if input_arg_count != INPUT_TYPE_ARG_COUNTS[input_type]:
        sys.exit(f"You provided {input_arg_count} arguments to {input_type}, where {INPUT_TYPE_ARG_COUNTS[input_type]} are expected. Read '-h' for command exmaples.")

def get_values_from_input(inputs):
    """Return pandas DataFrame of values from appropriate data source."""
    input_type = inputs[0]

    if input_type == 'parasol':
       response = get_parasol_values(*inputs[1:])
       return create_df_from_parasol(response)
    elif input_type == 'param_json':
        response = get_param_json_values(*inputs[1:])
        return create_df_from_param_json(response)
    elif input_type == 'seqgen_fincon':
        response = get_seqgen_fincon_values(*inputs[1:])
        return create_df_from_seqgen_fincon(response)
    elif input_type == 'csds':
        response = get_csds_values(*inputs[1:])
        return create_df_from_csds(response)

def main():
    create_directories()
    parser = argparse.ArgumentParser(
        description=PARSER_DESCRIPTION, 
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input1", required=True, nargs='+', type=str, help=PARSER_INPUT_HELP)
    parser.add_argument("--input2", required=True, nargs='+', type=str, help=PARSER_INPUT_HELP)
    parser.add_argument("--verbose", action='store_true', help="Include all data from compared files in output.")
    parser.add_argument("--diff-only", dest="diff_only",action='store_true', help="Only output parameters that do not match.")
    parser.add_argument("--intersect-only", dest="intersect_only",action='store_true', help="Only output parameters that exist in both inputs.")
    parser.add_argument("--to-json", dest="to_json", action='store_true', help="Output comparison as JSON.") # TODO: consider choices with 'xlsx', 'json', or 'pandas'
    parser.add_argument("--output", type=pathlib.Path, metavar='PATH', help="Path to desired output location.")
    args = parser.parse_args()
    
    # validate input types
    validate_input_arguments(args.input1)
    validate_input_arguments(args.input2)
    
    # query/load data and conver to pandas DataFrames
    df1 = get_values_from_input(args.input1)
    df2 = get_values_from_input(args.input2)

    # compare parameters
    df = compare_parameters(df1, df2, args.verbose, args.intersect_only, args.diff_only)

    # print statistics from comparison
    total, match_count, non_match_count = return_stats(df)

    # get metadata
    OUTPUT_TIME = datetime.now()
    metadata = get_metadata_from_args(args)
    metadata["Workbook created"] = OUTPUT_TIME.strftime("%Y-%m-%dT%H:%M:%S.%f")
    metadata["Parameters"] = total
    metadata["Matches"] = match_count
    metadata["Non-Matches"] = non_match_count
    
    # return in user-designated format
    output_filename = f'{OUTPUT_TIME.strftime("%Y_%m_%dT%H_%M_%S")}_{args.input1[0]}_{args.input2[0]}'
    output_filepath = get_output_path(args.output).joinpath(output_filename)
    if args.to_json:
        create_json(df, f"{output_filepath}.json", metadata = dict())
    else:
        create_xlsx(df, f"{output_filepath}.xlsx", metadata)

if __name__ == "__main__":
    main()