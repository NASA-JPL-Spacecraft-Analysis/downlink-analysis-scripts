import close_the_u
ENVIRONMENT = 'dev'


def parse_channel(data: dict) -> tuple[list, list]:
    top_level_key = 'telemetry_dictionary'
    state_key = 'telemetry_definitions'
    enum_key = 'enum_definitions'
    group_key= 'telemetry_groups'
    parsed_data = parse_dict(data, top_level_key, state_key, enum_key, group_key)
    state_list = []
    # create mapping of channel definitions and channel enums
    for key in parsed_data['telemetry']:
        channel_mapping = {
            'channelId': None,
            'identifier': None,
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
                    channel_mapping['channelId'] = value
                elif sub_key == '@name':
                    channel_mapping['identifier'] = value
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
                    for key in parsed_data['enum_table']:
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

        state_list.append(channel_mapping)
        
    # derive groups from channel_groups
    group_list = []
    for item in parsed_data['group']:
        group = {
            'groupName': None,
            'channelMappings': []
        }
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '@group_name':
                    group['groupName'] = value
                if key == 'group_channel':
                    for item in value:
                        group['channelMappings'].append(item)
                        
        group_list.append(group)
    return (state_list, group_list)
    
    
def parse_param(data: dict) -> tuple[list, list]:
    top_level_key = 'param-def'
    state_key = 'param'
    enum_key = 'enum_definitions'
    group_key = 'parameter_groups'
    parsed_data = parse_dict(data, top_level_key, state_key, enum_key, group_key)
    state_list = []
    # derive parameter definitions first to obtain enum name
    for item in parsed_data['list']:
        parameter_mapping = {
            'channelId': None,
            'identifier': None,
            'type': None,
            'ops_category': None,
            'description': None,
            'units': None,
            'enumerations': {}
        }
         # derive parameter definitions first to obtain enum name
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '@param_id':
                    parameter_mapping['channelId'] = value
                elif key == '@param_name':
                    parameter_mapping['identifier'] = value
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
                        for key in parsed_data['enum_table']:
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

        state_list.append(parameter_mapping)
        
    # derive groups from parameter_groups
    group_list = []
    for item in parsed_data['parameter_group']:
        group = {
            'identifier': None,
            'groupMappings': []
        }
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '@param_group_name':
                    group['identifier'] = value
                if key == 'group_params':
                    inner_values = value.get('group_param')
                    for item in inner_values:
                        group_map = {
                            'identifier': item,
                            'itemType': 'State'
                        }
                        group['groupMappings'].append(group_map)
        
        group_list.append(group)
                        
    return (state_list, group_list)
    

def parse_dict(data: dict, top_key: str, main_key: str, optional_key: str = None, optional_key2: str = None) -> dict:
    """ Parse specified keys in the given data dictionary
        
        Args:
        data (dict): **[REQUIRED]** the json data to extract from
        top_key (str): **[REQUIRED]** the top most key of the data dictionary
        main_key (str): **[REQUIRED]** the primary key nested within the top most key
        optional_key (str): any additional key nested within the top most key (default: none)
        optional_key2 (str): any additional key nested within the top most key (default: none)

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
    if optional_key2 is not None:
        for key, value in data[top_key][optional_key2].items():
            parsed_dict[key] = value
    return parsed_dict


def create_states(collection_id: str, state_records: dict, valueType: str) -> None:
    states = []
    for state in state_records:
        if isinstance(state, dict):
            record = {}
            record['channelId'] = state['channelId']
            record['restricted'] = False
            record['identifier'] = state['identifier']
            record['type'] = valueType
            record['dataType'] = state['type']
            record['subsystem'] = state['ops_category']
            record['source'] = 'flight'
            record['description'] = state['description']
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


def map_channel_groups(channel_def: list, channel_groups: list) -> list:
    channel_mapping = []
    for item in channel_groups:
        group = {
            'identifier': None,
            'groupMappings': []
        }
        if isinstance(item, dict):
            group['identifier'] = item['groupName']
            # for each group_channel find the State identifier in channel def
            for group_channel in item['channelMappings']:
                channel_id = group_channel
                for definition in channel_def:
                    group_mapping = {
                    'itemIdentifier': None,
                    'identifier': None,
                    'itemType': 'State'
                    }
                    if definition['channelId'] == channel_id:
                        # find the state identifier based on channelId
                        group_mapping['identifier'] = definition['identifier']
                        group['groupMappings'].append(group_mapping)
                        break
            channel_mapping.append(group)          
    return channel_mapping                


def find_state_identifier(state_identifier, state_dict) -> str:
    identifier = ''
    states = state_dict['data']['states']
    for state in states:
        for key, value in state.items():
            if key == 'identifier' and value == state_identifier:
                identifier = state['id']
                print('state id found:', identifier)
    return identifier
             

# Query the state IDs from SM and add it to the group mapping
def generate_group_mapping(collection_id, group_dict) -> list:
    states = {}
    states = close_the_u.state_manager.get_states(collection_id, env=ENVIRONMENT)
    groups = []
    # Find each state id for each given group
    for group in group_dict['group']:
        this_group = {}
        this_group['identifier'] = group['identifier']
        this_group_mapping = []
        for key, value in group.items():
            if key == 'groupMappings':
                for item in value:
                    the_mapping = {}
                    for inner_key, inner_value in item.items():
                        if inner_key == 'identifier':
                            state_identifier = inner_value
                            id = find_state_identifier(state_identifier, states)
                            the_mapping['itemIdentifier'] = id
                            the_mapping['identifier'] = state_identifier
                        the_mapping['itemType'] = 'State'
                    this_group_mapping.append(the_mapping)
        this_group['groupMappings'] = this_group_mapping
        groups.append(this_group)
    
    return groups

def generate_groups(groups: list, states: list, collection_id: str, value_type: str):
    group_dict = {'group': groups}
    # Create the states in SM to generate an ID
    create_states(collection_id, states, value_type)
    # For each state in a group find its associated ID in SM 
    groups = generate_group_mapping(collection_id, group_dict)
    close_the_u.state_manager.create_groups(collection_id, groups, ENVIRONMENT)