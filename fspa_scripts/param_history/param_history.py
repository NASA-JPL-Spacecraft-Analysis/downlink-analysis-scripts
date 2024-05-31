#!/usr/bin/env python

"""
FSW parameter comparison script. Compare parameter history from CSDS or Parasol
and view a human-readable output in XLSX or JSON.
"""

import argparse
import json
import os
import sys
import pathlib
from pathlib import Path
from datetime import datetime
import requests
import logging
import pandas as pd

if __name__ == "__main__":
    # This will be used if someone is running `python fspa_scripts/param_history/param_history.py ...`
    from utils.parasol import get_parasol_values, create_df_from_parasol
    from utils.csds import get_csds_values, create_df_from_csds
    from utils.history import generate_history_matrix, generate_history_list 
    from utils.constants import INPUT_TYPES, INPUT_TYPE_ARG_COUNTS
else:
    # This will be used if someone is running `param_comapre ...`
    from .utils.parasol import get_parasol_values, create_df_from_parasol
    from .utils.csds import get_csds_values, create_df_from_csds
    from .utils.history import generate_history_matrix, generate_history_list
    from .utils.constants import INPUT_TYPES, INPUT_TYPE_ARG_COUNTS

# setup logging
FORMAT = "[%(levelname)s] [%(asctime)s]: %(message)s"
requests.packages.urllib3.disable_warnings()

###############################################################################
# PARSER TEXT
###############################################################################
PARSER_DESCRIPTION = """CLI for comparing parameter history from csds or parasol."""

PARSER_INPUT_HELP = """commands: {csds, parasol}
required arguments:
    parasol:
        host        Session host on parasol (ex: eurcits001)
        session     Session id on parasol (ex: 830)
        start_time  A SCET formatted start time for parasol history (ex: 2023-136T22:08:51.038)
        end_time    A SCET formatted end time for parasol history (ex: 2023-136T22:08:51.038)
        vcid        VCID 0 or 32 (ex: 0)
        volatility  Use parasol volatile values (options: 'vol' or 'nvm')
        env         Venue for retrieving parameter values (ex: dev)
    csds:
        collection  Collection Name for state data store (ex: 'fsw-params-eurcits001-844')
        env         Venue for retrieving parameter values (ex: dev)
"""


###############################################################################
# HELPERS
###############################################################################
def _create_directories():
    """Create directories for script."""
    try:
        os.mkdir("data")
        os.mkdir("data/parasol_responses")
        os.mkdir("data/csds_responses")
        os.mkdir("output")
    except:
        pass

def _return_stats(df):
    """Print basic param_history counts to console and return them."""
    total = df.shape[0]
    changes = df.loc[df['change'] == True].shape[0]
    non_changes = total - changes
    
    # print summary
    print(f"PARAMETERS:\t{total}\nCHANGES:\t{changes}\nUNCHANGED:\t{non_changes}")

    # return results for metadata
    return total, changes, non_changes

def _get_output_path(path):
    """Get or build output path provided by user."""
    output_basepath = Path(path) if path else Path.cwd().joinpath('output')
    output_basepath.mkdir(exist_ok=True)
    return output_basepath

###############################################################################
# XLSX AND JSON WRITERS
###############################################################################  
def _get_metadata_from_args(args):
    """Create CLI argument dictionary with string values for XLSX metadata."""
    arg_dict = args.__dict__;
    metadata = dict()
    for i in arg_dict.keys():
        metadata[i] = str(arg_dict[i])
    return metadata

def add_metadata_worksheet(workbook, metadata = dict()):
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

def create_xlsx_matrix(df, filename, metadata = dict()):
    """Create XLSX file from pandas dataframe."""
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    logging.info('Creating excel workbook...')
    writer = pd.ExcelWriter(filename, engine="xlsxwriter") # options={'strings_to_numbers': False}
    
    # Sort rows with matches first; then alphabetical by parameter name
    df.sort_values(by=['change', 'end value', 'name'], ascending=[False, False, True], inplace=True)
    
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name="history")
    
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    history_worksheet = writer.sheets["history"]
    
    # make cell formats to use in conditional formatting, metadata
    green_format = workbook.add_format({'bg_color': '#C6EFCE','font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color': '#FFC7CE','font_color': '#9C0006'})
    gray_format = workbook.add_format({'bg_color': '#EEEEEE','font_color': '#000000'})
    light_gray_format = workbook.add_format({'bg_color': '#FAFAFA','font_color': '#000000', })
    
    # set better column widths for compare
    name_col = 1 + df.columns.get_loc("name")
    change_col = 1 + df.columns.get_loc("change")
    end_value_col = 1 + df.columns.get_loc("end value")

    # Get the dimensions of the dataframe.
    (max_row, max_col) = df.shape
    history_worksheet.set_column(1, max_col, 20) # 'name'
    history_worksheet.set_column(name_col, name_col, 45) # 'name'

    logging.info('Formatting excel workbook...')

    # Apply conditional formatting to 'timestamp columns' column
    # first_timestamp_col = name_col + 1
    # last_timestamp_col = change_col - 1
    # history_worksheet.conditional_format(1, first_timestamp_col, max_row, last_timestamp_col, {
    #     'type': 'blanks',
    #     "format": light_gray_format
    # })

    # Apply conditional formatting to 'change' column
    history_worksheet.conditional_format(1, change_col, max_row, change_col, {
        "type": "cell",
        "criteria": "==",
        "value": "TRUE",
        "format": green_format
    })
    history_worksheet.conditional_format(1, change_col, max_row, change_col, {
        "type": "cell",
        "criteria": "==",
        "value": "FALSE",
        "format": red_format
    })
    
    # Apply conditional formatting to 'end_value' column
    history_worksheet.conditional_format(1, end_value_col, max_row, end_value_col, {
        "type": "cell",
        "criteria": "equal to",
        "value": '"SAME"',
        "format": gray_format
    })
    history_worksheet.conditional_format(1, end_value_col, max_row, end_value_col, {
        "type": "cell",
        "criteria": "equal to",
        "value": '"DIFFERENT"',
        "format": yellow_format
    })

    add_metadata_worksheet(workbook, metadata)

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()

def create_xlsx_list(df, filename, metadata = dict()):
    """Create XLSX file from pandas dataframe."""
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    logging.info('Creating excel workbook...')
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    
    # Sort rows with matches first; then alphabetical by parameter name
    df.sort_values(by=['name', 'scet'], ascending=[True, True], inplace=True)
    
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name="history")
    
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    history_worksheet = writer.sheets["history"]
    
    # make cell formats to use in conditional formatting, metadata
    green_format = workbook.add_format({'bg_color': '#C6EFCE','font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
    gray_format = workbook.add_format({'bg_color': '#EEEEEE','font_color': '#000000'})
    
    # set better column widths for compare
    name_col = 1 + df.columns.get_loc("name")
    # status_col = 1 + df.columns.get_loc("status")

    # Get the dimensions of the dataframe.
    (max_row, max_col) = df.shape
    history_worksheet.set_column(1, max_col, 20) # 'name'
    history_worksheet.set_column(name_col, name_col, 45) # 'name'

    logging.info('Formatting excel workbook...')

    # Apply conditional formatting to 'change' column
    # history_worksheet.conditional_format(1, status_col, max_row, status_col, {
    #     "type": "cell",
    #     "criteria": "equal to",
    #     "value": '"INITIAL"',
    #     "format": gray_format
    # })
    # history_worksheet.conditional_format(1, status_col, max_row, status_col, {
    #     "type": "cell",
    #     "criteria": "equal to",
    #     "value": '"CHANGE"',
    #     "format": yellow_format
    # })
    # history_worksheet.conditional_format(1, status_col, max_row, status_col, {
    #     "type": "cell",
    #     "criteria": "equal to",
    #     "value": '"FINAL"',
    #     "format": green_format
    # })
    
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
        return sys.exit(f"Input type '{input_type}' does not exist. Valid types are 'csds', or 'parasol'.")
    
    if input_arg_count != INPUT_TYPE_ARG_COUNTS[input_type]:
        sys.exit(f"Input type {input_type} expects {INPUT_TYPE_ARG_COUNTS[input_type]} arguments. You provided {input_arg_count}. Read '-h' for help.")


def get_values_from_input(inputs, auth_type):
    """Return pandas DataFrame of values from appropriate data source."""
    input_type = inputs[0]

    if input_type == 'parasol':
       response = get_parasol_values(*inputs[1:], auth_type=auth_type)
       return create_df_from_parasol(response, inputs[-2]) # -2 is volatility
    elif input_type == 'csds':
        response = get_csds_values(*inputs[1:])
        return create_df_from_csds(response)

def main():
    _create_directories()
    parser = argparse.ArgumentParser(
        description=PARSER_DESCRIPTION, 
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input", required=True, nargs='+', type=str, help=PARSER_INPUT_HELP)
    parser.add_argument("--verbose", action='store_true', help="Include all data from query in output. NOTE: Only applies to 'list' format.")
    parser.add_argument("--format", default='matrix', const='matrix', nargs='?', choices=('list','matrix'), help="Format parameter output as 'matrix' or 'list'.")
    parser.add_argument("--intersect-only", dest="intersect_only",action='store_true', help="Only output parameters that exist in every timestamp in parameter history.")
    parser.add_argument("--change-only", dest="change_only", action='store_true', help="Only output parameters that changed in given history.")
    parser.add_argument("--end-value", dest="end_value", default='all', const='all', nargs='?', choices=('same', 'different','all'), help="Only output parameters that are the 'same' or 'different' (default: %(default)s).")
    parser.add_argument("--to-json", dest="to_json", action='store_true', help="Output history as JSON.")
    parser.add_argument("--output", type=pathlib.Path, metavar='PATH', help="Path to desired output location.")
    parser.add_argument("--debug", help="Log param_history processing information to console.", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    parser.add_argument("--auth-type", default="csso", help="Authenticate with 'csso' (Parasol with Chillax) or 'cam' (Parasol with MCWS) (default: csso)")
    
    args = parser.parse_args()

    logging.basicConfig(format=FORMAT, level=args.loglevel, datefmt='%Y-%m-%d %H:%M:%S')
    
    # validate input types
    validate_input_arguments(args.input)
    
    # query/load data and conver to pandas DataFrames
    df = get_values_from_input(args.input, auth_type=args.auth_type)

     # get metadata
    OUTPUT_TIME = datetime.now()
    metadata = _get_metadata_from_args(args)
    metadata["Workbook created"] = OUTPUT_TIME.strftime("%Y-%m-%dT%H:%M:%S.%f")

    if args.format == 'matrix':
        # generate history
        df = generate_history_matrix(df, args.intersect_only, args.end_value, args.change_only)
        # print statistics from history
        total, change_count, non_change_count = _return_stats(df)
        metadata["Parameters"] = total
        metadata["Changes"] = change_count
        metadata["Non-Changes"] = non_change_count
    else:
        # generate history
        df = generate_history_list(df, args.intersect_only, args.end_value, args.change_only, args.verbose)
        # print statistics from history
        # total, change_count, non_change_count = _return_stats(df)
   
    # return in user-designated format
    output_filename = f'{OUTPUT_TIME.strftime("%Y_%m_%dT%H_%M_%S")}_{args.input[0]}'
    output_filepath = _get_output_path(args.output).joinpath(output_filename)
    if args.to_json:
        create_json(df, f"{output_filepath}.json", metadata = dict())
    else:
        if args.format == 'matrix':
            create_xlsx_matrix(df, f"{output_filepath}.xlsx", metadata)
        else:
            create_xlsx_list(df, f"{output_filepath}.xlsx", metadata)

if __name__ == "__main__":
    main()