import xmltodict
import argparse


def convert_xml(input_file: str) -> dict:
    with open(input_file, 'r') as file:
        xml_data = file.read()
        
        data_dict = xmltodict.parse(xml_data)
        return data_dict


def parse_channel(data: dict):
    top_level_key = 'telemetry_dictionary'
    group_key = 'telemetry_groups'
    dict = parse_dict(data, top_level_key, group_key)
    print(dict)
    
    
def parse_param(data: dict):
    top_level_key = 'param-def'
    group_key = 'parameter_groups' 
    dict = parse_dict(data, top_level_key, group_key)
    print(dict)
    
    
def parse_dict(data: dict, top_key: str, main_key: str) -> dict:
    parsed_dict = {}
    if top_key in data:
        for key, value in data[top_key][main_key].items():
            parsed_dict[key] = value
                
    return parsed_dict
    
def main(mode, input_file, output_file) -> None:
    # currently script will simply parse channel or param files
    data = convert_xml(input_file)
    if mode == 'channel':
        parse_channel(data)
    if mode == 'param':
        parse_param(data)
        
        
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="close-the-u wrapper script")
    arg_parser.add_argument('-m', '--mode', dest='mode', choices=['channel', 'param'], required=True, help='run mode')
    arg_parser.add_argument('-i', '--input', dest= 'input_file', required=False, help='input file')
    arg_parser.add_argument('-o', '--output', dest='output_file', required=False, help='output file')
    args = arg_parser.parse_args()
    main(args.mode, args.input_file, args.output_file)