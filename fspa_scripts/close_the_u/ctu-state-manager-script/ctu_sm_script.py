import xmltodict
import argparse
import json
import close_the_u
from publish_groups import *
from publish_constraints import *
from publish_events import *
from publish_commands import *

ENVIRONMENT = 'dev'

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


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="close-the-u wrapper script")
    arg_parser.add_argument('-i', '--input', dest='input_file', required=True, help='input file: type is of XML and is REQUIRED')
    arg_parser.add_argument('-c', '--collectionId', dest='collection_id', required=True, help='collection id to be used: REQUIRED')
    arg_parser.add_argument('-m', '--mode', dest='mode', choices=['channel', 'parameter','flight_rules', 'evr', 'fault_monitors', 'command'], required=True, help='Publish SM groups with channel.xml or parameter.xml. Publish SM constraints with flight_rules.xml or fault_monitors.xml. Publish SM events with evr.xml. Publish SM commands with command.xml. mode:  REQUIRED')
    arg_parser.add_argument('-e', '--environment', dest='environment', default=ENVIRONMENT, required=False, help='The environmental server to use')
    args = arg_parser.parse_args()
    
    mode = args.mode
    input_file = args.input_file
    collection_id = args.collection_id
    environment = args.environment
    
    data = convert_xml(input_file)
    valueType = ''
    if mode == 'channel':
        state_output, group_output = parse_channel(data)
        valueType = 'channel'
        groups = map_channel_groups(state_output, group_output)
        generate_groups(groups, state_output, collection_id, valueType, environment)
    if mode == 'parameter':
        state_output, group_output = parse_param(data)
        valueType = 'fsw_parameter'
        groups = group_output
        generate_groups(groups, state_output, collection_id, valueType, environment)
    if mode == 'flight_rules':
        constraints = parse_flight_rules(data, collection_id)
        close_the_u.state_manager.create_constraints(collection_id, constraints, environment)
    if mode == 'fault_monitors':
        constraints = parse_fault_monitors(data, collection_id)
        close_the_u.state_manager.create_constraints(collection_id, constraints, environment)
    if mode == 'evr':
        events = parse_evr(data, collection_id)
        close_the_u.state_manager.create_events(collection_id, events, environment)
    if mode == 'command':
        commands = parse_commands(data, collection_id)
        close_the_u.state_manager.create_commands(collection_id, commands, environment)
    
if __name__ == "__main__":
   main()