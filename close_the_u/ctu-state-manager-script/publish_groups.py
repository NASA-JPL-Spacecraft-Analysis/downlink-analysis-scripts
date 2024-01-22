import xmltodict
import argparse
import json
import close_the_u
ENVIRONMENT = 'dev'


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
            'channeID': None,
            'groupName': None,
            'type': None,
            'ops_category': None,
            'description': None,
            'units': None,
            'enumerations': {}
        }
        raw_to_eng = False
        if 'raw_to_eng' in key:
            raw_to_eng = True
        # derive definition first to obtain enum name
        if isinstance(key, dict):
            for sub_key, value in key.items():
                if sub_key == '@abbreviation':
                    channel_mapping['channeID'] = value
                elif sub_key == '@name':
                    channel_mapping['groupName'] = value
                elif sub_key == '@type':
                    channel_mapping['type'] = value
                elif sub_key == 'categories':
                    category = value.get('ops_category', '')
                    channel_mapping['ops_category'] = category
                elif sub_key == 'description':
                    channel_mapping['description'] = value
                elif sub_key == 'raw_units' and raw_to_eng == False:
                    channel_mapping['units'] = value
                elif sub_key == 'raw_to_eng':
                    channel_mapping['units'] = key[sub_key]['eng_units']
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
            'channeID': None,
            'groupName': None,
            'type': None,
            'ops_category': None,
            'description': None,
            'units': None,
            'enumerations': {}
        }
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '@param_id':
                    parameter_mapping['channeID'] = value
                elif key == '@param_name':
                    parameter_mapping['groupName'] = value
                elif key == '@type':
                    parameter_mapping['type'] = value
                elif key == 'categories':
                    category = value.get('ops_category', '')
                    parameter_mapping['ops_category'] = category
                elif key == 'sysdesc':
                    parameter_mapping['description'] = value
                elif key == '@units':
                    parameter_mapping['units'] = value
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


def write_to_output_file(data: dict, output_file: str) -> None:
    with open(output_file, 'w') as json_file:
            json.dump(data, json_file)


def read_from_json(filename: str) -> dict:
    with open(filename) as f:
        data = json.load(f)
    return data


def create_states(collection_id: str, state_records: dict, valueType: str) -> None:
    new_states = state_records['data']
    states = []
    for state in new_states:
        if isinstance(state, dict):
            record = {}
            record['channelId'] = state['channeID']
            record['restricted'] = False
            record['identifier'] = state['groupName']
            record['type'] = valueType
            record['dataType'] = state['type']
            record['subsystem'] = state['ops_category']
            record['source'] = 'flight'
            states.append(record)
        if record['dataType'] == 'enum':
            # create state enumerations
            record['enumerations'] = []
            for key, value in state['enumerations'].items():
                enum_name_value = {}
                enum_name_value['label'] = key
                enum_name_value['value'] = value
                record['enumerations'].append(enum_name_value)
        
    close_the_u.state_manager.create_states(collection_id, states, ENVIRONMENT)
            

def main(mode: str, input_file: str, output_file: str, collection_id: str) -> None:
    # currently script will simply parse channel or param files
    data = convert_xml(input_file)
    valueType = ''
    if mode == 'channel':
        output = parse_channel(data)
        valueType = 'channel'
    if mode == 'parameter':
        output = parse_param(data)
        valueType = 'fsw_parameter'
        
    group_dict = {'data': output}
    write_to_output_file(group_dict, output_file)
    json_data = read_from_json(output_file)
    create_states(collection_id, json_data, valueType)
        
        
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="close-the-u wrapper script")
    arg_parser.add_argument('-m', '--mode', dest='mode', choices=['channel', 'parameter'], required=True, help='run mode')
    arg_parser.add_argument('-i', '--input', dest='input_file', required=True, help='input file')
    arg_parser.add_argument('-o', '--output', dest='output_file', default='output.json', required=False, help='output file')
    arg_parser.add_argument('-c', '--collectionId', dest='collection_id', required=True, help='collection id to be used')
    args = arg_parser.parse_args()
    main(args.mode, args.input_file, args.output_file, args.collection_id)