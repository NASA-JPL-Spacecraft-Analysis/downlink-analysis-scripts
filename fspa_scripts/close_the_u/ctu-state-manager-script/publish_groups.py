import json
import sys

from typing import Any, Dict, List

import close_the_u

MAX_PAYLOAD_SIZE_MB = 2


def _get_json_size_mb(payload: dict):
    return sys.getsizeof(json.dumps(payload)) / (1024 * 1024)


def _parse_dict(data: dict, top_key: str, main_key: str, optional_key: str = None, optional_key2: str = None) -> dict:
    """Parse specified keys in the given data dictionary

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


def _find_state_identifier(state_identifier: str, state_dict: dict) -> str:
    identifier = ''

    states = state_dict['data']['states']
    for state in states:
        for key, value in state.items():
            if key == 'identifier' and value == state_identifier:
                identifier = state['id']

    return identifier


def _send_states(collection_id: str, batched_states: List, environment: str) -> None:
    try:
        batch_count = len(batched_states)
        print(f'Sending {batch_count} Batched States to State Manager')

        for idx, batch in enumerate(batched_states):
            response = close_the_u.state_manager.create_states(collection_id, batch, environment)

            if 'errors' in response and len(response['errors']):
                print(f"Failed to send {idx+1} of {batch_count}. Error: {response['errors'][0]['message']}")
            else:
                print(f'Successfully sent {idx+1} of {batch_count}')
    except Exception as e:
        print(e)


def _create_and_batch_states(state_records: dict, valueType: str) -> List[List[Dict]]:
    current_batch_size: float = 0
    batches: List[List[Dict]] = []
    states: List[Dict] = []

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

        if record['dataType'] == 'enum':
            # create state enumerations
            record['enumerations'] = []
            for key, value in state['enumerations'].items():
                enum_name_value = {}
                enum_name_value['label'] = key
                enum_name_value['value'] = value
                record['enumerations'].append(enum_name_value)

        record_size = _get_json_size_mb(record)
        if (record_size + current_batch_size) < MAX_PAYLOAD_SIZE_MB:
            states.append(record)
            current_batch_size += record_size
        else:
            batches.append(states)
            states = [record]
            current_batch_size = record_size

    return batches


# Query the state IDs from SM and add it to the group mapping
def _generate_group_mapping(collection_id: str, group_dict: dict, environment: str) -> List[Dict]:
    states = close_the_u.state_manager.get_states(collection_id, env=environment)
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
                            id = _find_state_identifier(state_identifier, states)
                            the_mapping['itemIdentifier'] = id
                            the_mapping['identifier'] = state_identifier
                        the_mapping['itemType'] = 'State'
                    this_group_mapping.append(the_mapping)
        this_group['groupMappings'] = this_group_mapping
        groups.append(this_group)

    return groups


def _send_groups(collection_id: str, groups: list, environment: str) -> None:
    group_dict = {'group': groups}

    try:
        # For each state in a group find its associated ID in SM
        groups = _generate_group_mapping(collection_id, group_dict, environment)

        group_count = len(groups)
        print(f'Sending {group_count} Groups to State Manager')

        response = close_the_u.state_manager.create_groups(collection_id, groups, environment)

        if 'errors' in response and len(response['errors']):
            print(f"Failed to send. Error: {response['errors'][0]['message']}")
        else:
            print(f'Successfully sent.')
    except Exception as e:
        print(e)


def parse_channel(data: dict) -> tuple[list, list]:
    top_level_key = 'telemetry_dictionary'
    state_key = 'telemetry_definitions'
    enum_key = 'enum_definitions'
    group_key = 'telemetry_groups'
    parsed_data = _parse_dict(data, top_level_key, state_key, enum_key, group_key)
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
            'enumerations': {},
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
        group = {'groupName': None, 'channelMappings': []}
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
    parsed_data = _parse_dict(data, top_level_key, state_key, enum_key, group_key)
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
            'enumerations': {},
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
                                param_type = type_name[: -len('_param')]
                                parameter_mapping['type'] = param_type
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
        group = {'identifier': None, 'groupMappings': []}
        if isinstance(item, dict):
            for key, value in item.items():
                if key == '@param_group_name':
                    group['identifier'] = value
                if key == 'group_params':
                    inner_values = value.get('group_param')
                    for item in inner_values:
                        group_map = {'identifier': item, 'itemType': 'State'}
                        group['groupMappings'].append(group_map)

        group_list.append(group)

    return (state_list, group_list)


def map_channel_groups(channel_def: list, channel_groups: list) -> list:
    channel_mapping = []
    for item in channel_groups:
        group = {'identifier': None, 'groupMappings': []}
        if isinstance(item, dict):
            group['identifier'] = item['groupName']
            # for each group_channel find the State identifier in channel def
            for group_channel in item['channelMappings']:
                channel_id = group_channel
                for definition in channel_def:
                    group_mapping = {'itemIdentifier': None, 'identifier': None, 'itemType': 'State'}
                    if definition['channelId'] == channel_id:
                        # find the state identifier based on channelId
                        group_mapping['identifier'] = definition['identifier']
                        group['groupMappings'].append(group_mapping)
                        break
            channel_mapping.append(group)
    return channel_mapping


def generate_groups(groups: list, states: list, collection_id: str, value_type: str, environment: str):
    # Create the states in SM to generate an ID
    batched_states = _create_and_batch_states(states, value_type)
    _send_states(collection_id, batched_states, environment)

    _send_groups(collection_id, groups, environment)
