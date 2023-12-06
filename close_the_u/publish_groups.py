import xmltodict
import argparse
import json

        
def convert_xml(input_file: str) -> dict:
    with open(input_file, 'r') as file:
        xml_data = file.read()
        
        data_dict = xmltodict.parse(xml_data)
        return data_dict


def parse_channel(data: dict) -> list:
    top_level_key = 'telemetry_dictionary'
    group_key = 'telemetry_groups'
    groups = parse_dict(data, top_level_key, group_key)
    group_list = []
    # build a hashmap between group_channel IDs and name
    for key in groups['group']:
        group_dict = {
            'group': None,
            'group_channels': []
        }
    
        for sub_key, value in key.items():
            if sub_key == '@group_name':
                group_dict['group'] = value
            elif sub_key == 'group_channel':
                if isinstance(value, list):
                    group_dict['group_channels'].extend(value)
            
        group_list.append(group_dict)
    return group_list
    
    
def parse_param(data: dict) -> dict:
    top_level_key = 'param-def'
    group_key = 'parameter_groups' 
    dict = parse_dict(data, top_level_key, group_key)
    pass
    
    
def parse_dict(data: dict, top_key: str, main_key: str) -> dict:
    parsed_dict = {}
    if top_key in data:
        for key, value in data[top_key][main_key].items():
            parsed_dict[key] = value
                
    return parsed_dict

def write_to_output_file(data: dict, output_file: str):
    with open(output_file, 'w') as json_file:
            json.dump(data, json_file)
    
def main(mode, input_file, output_file) -> None:
    # currently script will simply parse channel or param files
    data = convert_xml(input_file)
    if mode == 'channel':
        output = parse_channel(data)
    if mode == 'param':
        output = parse_param(data)
        
    group_dict = {'data': output}
    write_to_output_file(group_dict, output_file)
        
        
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="close-the-u wrapper script")
    arg_parser.add_argument('-m', '--mode', dest='mode', choices=['channel', 'param'], required=True, help='run mode')
    arg_parser.add_argument('-i', '--input', dest= 'input_file', required=False, help='input file')
    arg_parser.add_argument('-o', '--output', dest='output_file', required=False, help='output file')
    args = arg_parser.parse_args()
    main(args.mode, args.input_file, args.output_file)