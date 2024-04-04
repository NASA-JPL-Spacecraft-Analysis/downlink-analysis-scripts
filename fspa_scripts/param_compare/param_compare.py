#!/usr/bin/env python

"""
FSW comparison script. Compare Parasol queries and parm.json and generate human-readable output.
"""

import argparse
import json
import os
import parasol
import sys
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime
# import xlsxwriter

GROUP = "no_group"
COPY = "COPY_0"

###############################################################################
# QUERY HELPERS
###############################################################################
def _get_env_venue(env):
    """Get venue to query parasol by environment."""
    if env == "dev":
        return {
            "parasol_host": "parasol.eurc-dev.jpl.nasa.gov",
            "cookie_name": "ecDevRhel8Sso",
        }


def get_parameter_values(host, session, scet, vcid, env):
    """Get and return parasol query based on provided CLI arguments."""

    # create filename for response
    filename = "./parasol_responses/{}_{}_{}_{}.json".format(
        host, session, scet, vcid
    )

    if os.path.exists(filename):
        print("Using saved response for Parasol for parameter values...")
        with open(filename) as parasol_parameter_values:
            return json.load(parasol_parameter_values)

    else:
        print("Making request to Parasol for parameter values...")
        venue = _get_env_venue(env)
        try:
            response = parasol.get_parameter_values(
                phase="cruise",
                auth_type="cam",
                parasol_host=venue["parasol_host"],
                cookie_name=venue["cookie_name"],
                time_str=scet,
                time_type="scet",
                session_host=host,
                session_id=session,
                vcid=vcid,
            )
        except parasol.exceptions.ParasolAuthException as exc:
            print("Oh no! You forgot to login!")
            raise exc
        except parasol.exceptions.ParasolBaseException as exc:
            print("Something else happened!")
            raise exc

        print("Received response from Parasol.")

        with open(filename, "w") as json_file:
            json.dump(
                response, json_file, indent=4, sort_keys=False, separators=(",", ": ")
            )

        return response


###############################################################################
# XLSX HELPERS
###############################################################################
    
def add_workbook_formats(workbook):
    """make cell formats to use in conditional formatting, metadata"""
    green_format = workbook.add_format({'bg_color':   '#C6EFCE','font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color':   '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color':   '#FFC7CE','font_color': '#9C0006'})
    bold_format = workbook.add_format({'bold': True})
    return green_format, yellow_format, red_format, bold_format
    

def add_metadata_worksheet(workbook, metadata):
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


###############################################################################
# XLSX WRITERS
###############################################################################
def create_parasol_parasol_xlsx(args, df):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter("output/parasol_parasol.xlsx", engine="xlsxwriter")
    
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name="compare")
    
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    compare_worksheet = writer.sheets["compare"]
    
    # make cell formats to use in conditional formatting, metadata
    green_format = workbook.add_format({'bg_color':   '#C6EFCE','font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color':   '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color':   '#FFC7CE','font_color': '#9C0006'})
    
    # set better column widths for compare
    compare_worksheet.set_column("E:E", 45) # 'name'
    compare_worksheet.set_column("F:F", 20) # 'non_volatile_value'
    compare_worksheet.set_column("I:I", 20) # 'non_volatile_value_2'
    compare_worksheet.set_column("L:L", 20) # 'match'

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

    # Add metadata from queries
    metadata = {
        "Host:": args.host,
        "Session:": f"{args.session}",
        "SCET 1:": args.scet1,
        "SCET 2:": args.scet2,
        "VCID:": f"{args.vcid}",
        "env:": args.env,
        "Workbook created:": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
    add_metadata_worksheet(workbook, metadata)

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()


def create_parasol_json_xlsx(args, df):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter("output/parasol_json.xlsx", engine="xlsxwriter")
    
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name="compare")
    
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    compare_worksheet = writer.sheets["compare"]
    
    # make cell formats to use in conditional formatting, metadata
    green_format = workbook.add_format({'bg_color':   '#C6EFCE','font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color':   '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color':   '#FFC7CE','font_color': '#9C0006'})
    
    # set better column widths for compare
    compare_worksheet.set_column("E:E", 45) # 'name'
    compare_worksheet.set_column("F:F", 20) # 'non_volatile_value'
    compare_worksheet.set_column("N:N", 20) # 'value'
    compare_worksheet.set_column("Q:Q", 20) # 'match'

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

    # Add metadata from queries
    metadata = {
        "Host:": args.host,
        "Session:": f"{args.session}",
        "SCET:": args.scet,
        "JSON PATH:": str(args.json),
        "VCID:": f"{args.vcid}",
        "env:": args.env,
        "Workbook created:": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
    add_metadata_worksheet(workbook, metadata)

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()


def create_json_json_xlsx(args, df):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter("output/json_json.xlsx", engine="xlsxwriter")
    
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name="compare")
    
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    compare_worksheet = writer.sheets["compare"]
    
    # make cell formats to use in conditional formatting, metadata
    green_format = workbook.add_format({'bg_color':   '#C6EFCE','font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color':   '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color':   '#FFC7CE','font_color': '#9C0006'})
    
    # set better column widths for compare
    compare_worksheet.set_column("C:C", 45) # 'name'
    compare_worksheet.set_column("H:H", 20) # 'value_1'
    compare_worksheet.set_column("P:P", 20) # 'value_2'
    compare_worksheet.set_column("S:S", 20) # 'match'

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

    # Add metadata from queries
    metadata = {
        "JSON 1 PATH:": str(args.json1),
        "JSON 2 PATH:": str(args.json2),
        "Workbook created:": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
    add_metadata_worksheet(workbook, metadata)

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()


###############################################################################
# COMPARE FUNCTIONS
###############################################################################
def compare_parasol(args, response1, response2):
    # create excel output.
    rows_list1 = []
    for module_name, module in response1.items():
        print("Comparing parameters for query 1, module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            row = {
                "module": module_name,
                "group": GROUP,
                "copy": COPY,
                "name": parameter_name,
                "value": parameter['non-volatile']['value'],
                "evidence": parameter['non-volatile']['evidence'],
                "evidence_status": parameter['non-volatile']['evidence_status'],
            }
            rows_list1.append(row)
        print('Processed parasol response 1.')

    # create dataframe based on rows
    df1 = pd.DataFrame(rows_list1)
    
    rows_list2 = []
    for module_name, module in response2.items():
        print("Comparing parameters for query 2, module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            row = {
                "module": module_name,
                "group": GROUP,
                "copy": COPY,
                "name": parameter_name,
                "value": parameter['non-volatile']['value'],
                "evidence": parameter['non-volatile']['evidence'],
                "evidence_status": parameter['non-volatile']['evidence_status'],
            }
            rows_list2.append(row)
        print('Processed parasol response 2.')

    # create dataframe based on rows
    df2 = pd.DataFrame(rows_list2)

    # merge dataframes from each query
    df = pd.merge(df1, df2, how="outer", on=["module", "group", "copy", "name"], suffixes=("_1", "_2"))
    print(df.head())
    df['match'] = df['value_1'] == df['value_2']
    
    # create worksheet for parasol-parasol comparison script
    create_parasol_parasol_xlsx(args, df)
    
def compare_parasol_json(args, parasol_response, json_data):
    # create excel output.
    rows_list1 = []
    for module_name, module in parasol_response.items():
        print("Comparing parameters for query 1, module {}".format(module_name))
        for parameter_name, parameter in module[GROUP][COPY].items():
            row = {
                "module": module_name,
                "group": GROUP,
                "copy": COPY,
                "name": parameter_name,
                "value": parameter['non-volatile']['value'],
                "evidence": parameter['non-volatile']['evidence'],
                "evidence_status": parameter['non-volatile']['evidence_status'],
            }
            rows_list1.append(row)
        print('Processed parasol response 1.')

    # create dataframe based on rows
    df1 = pd.DataFrame(rows_list1)

    df2 = pd.json_normalize(json_data['parameter_file']['parameter_list'])

    # merge dataframes from each query
    df = pd.merge(df1, df2, how="outer", on=["name"], suffixes=("_parasol", "_json"))
    df['match'] = df['value_parasol'] == df['value_json']
    
    # create worksheet for parasol-parasol comparison script
    create_parasol_json_xlsx(args, df)

def compare_json(args, json1, json2):
    print("Comparing json1 with json2 path inputs.")
    df1 = pd.json_normalize(json1['parameter_file']['parameter_list'])
    print(df1.info())

    df2 = pd.json_normalize(json2['parameter_file']['parameter_list'])
    print(df2.info())

    # merge dataframes from each query
    df = pd.merge(df1, df2, how="outer", on=["name"], suffixes=("_1", "_2"))
    df['match'] = df['value_1'] == df['value_2']
    
    # create worksheet for parasol-parasol comparison script
    create_json_json_xlsx(args, df)

###############################################################################
# RUN MAIN, ARG PARSER
###############################################################################
def setup():
    """Create missing directories for script."""
    try:
        os.mkdir("parasol_responses")
        os.mkdir("output")
    except:
        pass

def main():
    setup()

    # CREATE PARSER
    parser = argparse.ArgumentParser(description="CLI for comparing parameter JSON and parasol queries.")
    parser.add_argument("-o", "--output", default="XLSX", help="format to write output response (XLSX or JSON)")

    subparsers = parser.add_subparsers(title='command', dest='command')

    # PARASOL-PARASOL PARSER
    parasol_only_parser = subparsers.add_parser(
        "parasol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two parasol queries by time1 and time2.")
    
    parasol_only_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_only_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_only_parser.add_argument("--scet1", required=True, help="A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--scet2", required=True, help="A SCET formatted time for parasol query 2 (ex: 2023-136T22:08:51.038)")
    parasol_only_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_only_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    
    # PARASOL-JSON PARSER
    parasol_json_parser = subparsers.add_parser(
        "parasol_json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two parasol queries by scet1 and scet2.")
    
    parasol_json_parser.add_argument("--host", required=True, help="Session host on parasol (ex: eurcits001)")
    parasol_json_parser.add_argument("--session", required=True, help="Session id on parasol (ex: 578)")
    parasol_json_parser.add_argument("--scet", required=True, help="A SCET formatted time (ex: 2023-136T22:08:51.038)")
    parasol_json_parser.add_argument("--vcid", type=int, default=0, help="VCID 0 or 1 (ex: 0)")
    parasol_json_parser.add_argument("--env", default="dev", help="Venue for retrieving parameter values and publishing (ex: dev)")
    parasol_json_parser.add_argument("--json", required=True, type=pathlib.Path, metavar='PATH', help="param.json to use for comparison")

    # JSON-JSON PARSER
    json_only_parser = subparsers.add_parser(
        "json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two param.json files.")
    
    json_only_parser.add_argument("--json1", required=True, type=pathlib.Path, metavar='PATH', help="Path to first param.json to generate comparison")
    json_only_parser.add_argument("--json2", required=True, type=pathlib.Path, metavar='PATH', help="Path to second param.json to generate comparison")

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
        parasol = get_parameter_values(args.host, args.session, args.scet, args.vcid, args.env)

        try:
            with open(args.json, "r") as json_file:
                json_data = json.load(json_file)
        except FileNotFoundError:
            sys.exit(f'ERROR: file \'{args.json1}\' cannot be found.')

        compare_parasol_json(args, parasol, json_data)
    
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