import xmltodict
import argparse
import json
import close_the_u
        
def convert_xml(input_file: str) -> dict:
    with open(input_file, 'r') as file:
        xml_data = file.read()
        data_dict = xmltodict.parse(xml_data)
        return data_dict


def parse_channel(data: dict) -> list:
    top_level_key = 'telemetry_dictionary'
    telemetry_key = 'telemetry_definitions'
    enum_key = 'enum_definitions'
    groups = parse_dict(data, top_level_key, telemetry_key, enum_key)
    enum_list = []
    
    # create mapping of channel definitions and channel enums
    for key in groups['telemetry']:
        channel_mapping = {
            'abbreviation': None,
            'name': None,
            'type': None,
            'ops_category': None,
            'enumerations': {}
        }
        # derive definition first to obtain enum name
        if isinstance(key, dict):
                for sub_key, value in key.items():
                    if sub_key == '@abbreviation':
                        channel_mapping['abbreviation'] = value
                    elif sub_key == '@name':
                        channel_mapping['name'] = value
                    elif sub_key == '@type':
                        channel_mapping['type'] = value
                    elif sub_key == 'categories':
                        category = value.get('ops_category', '')
                        channel_mapping['ops_category'] = category
                    elif sub_key == 'enum_format':
                        enum_name = value['@enum_name']
                        # derive enums from enum name
                        for key in groups['enum_table']:
                            if isinstance(key, dict):
                                for sub_key, value in key.items():
                                    if sub_key == '@name' and value == enum_name:
                                        # access values from the inner dictionary
                                        inner_values = key.get('values', {}).get('enum', [])
                                        for item in inner_values:
                                            if isinstance(item, dict):
                                                enum_member = item['@symbol']
                                                enum_value = item['@numeric']
                                                channel_mapping['enumerations'][enum_member] = enum_value
                                                                
        enum_list.append(channel_mapping)
    return enum_list
    
    
def parse_param(data: dict) -> list:
    top_level_key = 'param-def'
    parameter_group = 'param'
    enum_key = 'enum_definitions'
    groups = parse_dict(data, top_level_key, parameter_group, enum_key)
    enum_list = []
    # derive definition first to obtain enum name
    for item in groups['list']:
        parameter_mapping = {
            'param_id': None,
            'param_name': None,
            'type': None,
            'ops_category': None,
            'enumerations': {}
        }
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '@param_id':
                    parameter_mapping['param_id'] = value
                elif key == '@param_name':
                    parameter_mapping['param_name'] = value
                elif key == '@type':
                    parameter_mapping['type'] = value
                elif key == 'categories':
                    category = value.get('ops_category', '')
                    parameter_mapping['ops_category'] = category
                elif key == 'parameter_type':
                    if isinstance(value, dict):
                        for index, (sub_key, _) in enumerate(value.items()):
                            if index == 0:
                                type_name = sub_key
                                # slice the param suffix
                                type = type_name[:-len('_param')]
                                parameter_mapping['type'] = type
                    if isinstance(value, dict):
                        enum_name = value.get('enum_param', {}).get('@enum_name', '')
                        # derive enums from enum name
                        for key in groups['enum_table']:
                            if isinstance(key, dict):
                                for sub_key, value in key.items():
                                    if sub_key == '@name' and value == enum_name:
                                        # access values from the inner dictionary
                                        inner_values = key.get('values', {}).get('enum', [])
                                        for item in inner_values:
                                            if isinstance(item, dict):
                                                enum_member = item['@symbol']
                                                enum_value = item['@numeric']
                                                parameter_mapping['enumerations'][enum_member] = enum_value
                                        
        enum_list.append(parameter_mapping)
    return enum_list
    

def parse_dict(data: dict, top_key: str, main_key: str, optional_key: str = None) -> dict:
    """ Parse specified keys in the given data dictionary
        
        Args:
        data (dict): **[REQUIRED]** the json data to extract from
        top_key (str): **[REQUIRED]** the top most key of the data dictionary
        main_key (str): **[REQUIRED]** the primary key nested within the top most key
        optional_key (str): any additional key nested within the top most key (default: none)

    Returns:
       A dictionary with the requested parsed items from the given input data
    """
    parsed_dict = {}
    if top_key in data:
        if isinstance(data[top_key][main_key], dict):
            for key, value in data[top_key][main_key].items():
                parsed_dict[key] = value
        elif isinstance(data[top_key][main_key], list):
            parsed_dict['list'] = []
            for item in data[top_key][main_key]:
                parsed_dict['list'].append(item)
    if optional_key is not None:
        for key, value in data[top_key][optional_key].items():
            parsed_dict[key] = value
    return parsed_dict


def write_to_output_file(data: dict, output_file: str):
    with open(output_file, 'w') as json_file:
            json.dump(data, json_file)


def read_from_json(filename: str) -> dict:
    with open(filename) as f:
        data = json.load(f)
    return data


def create_state():
    # TODO
    pass


def main(mode: str, input_file: str, output_file: str, collection_id: str) -> None:
    # currently script will simply parse channel or param files
    data = convert_xml(input_file)
    if mode == 'channel':
        output = parse_channel(data)
    if mode == 'parameter':
        output = parse_param(data)
        
    group_dict = {'data': output}
    write_to_output_file(group_dict, output_file)
    read_from_json(output_file)
        
        
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="close-the-u wrapper script")
    arg_parser.add_argument('-m', '--mode', dest='mode', choices=['channel', 'parameter'], required=True, help='run mode')
    arg_parser.add_argument('-i', '--input', dest='input_file', required=True, help='input file')
    arg_parser.add_argument('-o', '--output', dest='output_file', default='output.json', required=False, help='output file')
    arg_parser.add_argument('-c', '--collectionId', dest='collection_id', required=True, help='collection id to be used')
    args = arg_parser.parse_args()
    main(args.mode, args.input_file, args.output_file, args.collection_id)