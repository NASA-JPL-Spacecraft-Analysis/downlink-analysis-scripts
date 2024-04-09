import xmltodict
import argparse
import json
from publish_groups import *
from publish_constraints import *


def convert_xml(input_file: str) -> dict:
    with open(input_file, 'r') as file:
        xml_data = file.read()
        data_dict = xmltodict.parse(xml_data)
        return data_dict


def write_to_output_file(data: dict, output_file: str) -> None:
    with open(output_file, 'w') as json_file:
            json.dump(data, json_file)


def read_from_json(filename: str) -> dict:
    with open(filename) as f:
        data = json.load(f)
    return data


def main(mode: str, input_file: str, collection_id: str) -> None:
    # currently script will simply parse channel or param files
    data = convert_xml(input_file)
    valueType = ''
    if mode == 'channel':
        state_output, group_output = parse_channel(data)
        valueType = 'channel'
        groups = map_channel_groups(state_output, group_output)
        generate_groups(groups, state_output, collection_id, valueType)
    if mode == 'parameter':
        state_output, group_output = parse_param(data)
        valueType = 'fsw_parameter'
        groups = group_output
        generate_groups(groups, state_output, collection_id, valueType)
    if mode == 'constraint':
        flight_rules = parse_flight_rules(data, collection_id)
        create_constraints(collection_id, flight_rules)
        
        
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="close-the-u wrapper script", usage='ctu_sm_script.py [-h] -i INPUT_FILE -c COLLECTION_ID {groups,constraints} ...')
    arg_parser.add_argument('-i', '--input', dest='input_file', required=True, help='input file: REQUIRED')
    arg_parser.add_argument('-c', '--collectionId', dest='collection_id', required=True, help='collection id to be used: REQUIRED')
    sub_parser = arg_parser.add_subparsers(help='Publish groups or constraints to State Manager')
    # subparser for groups command
    parser_group = sub_parser.add_parser('groups', help='parse channel.xml or param.xml')
    parser_group.add_argument('-m', '--mode', dest='mode', choices=['channel', 'parameter'], required=True, help='file mode: REQUIRED')
    # subparser for contraints command
    parser_constraint = sub_parser.add_parser('constraints', help='parse flight_rules.xml')
    
    args = arg_parser.parse_args()
    mode = args.mode if hasattr(args, 'mode') else 'constraint'
    main(mode, args.input_file, args.collection_id)