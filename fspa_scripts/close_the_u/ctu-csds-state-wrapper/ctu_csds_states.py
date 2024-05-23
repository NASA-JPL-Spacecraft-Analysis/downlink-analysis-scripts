#!/usr/bin/env python
import argparse
import json
import os
import re
import requests
import sys

import pandas as pd

from close_the_u import state_data_store
from datetime import datetime
from typing import Any, Dict, List, Optional

CSDS_REQUIRED_FIELDS = ['name', 'scet', 'value', 'type', 'valueType']


def _get_file_type(filename: str) -> Optional[re.Match]:
    extension_regex = r'[^.]+$'
    return re.search(extension_regex, filename).group()


def _write_file_type(response: Dict[str, Any], output: str) -> None:
    print(f'Writing states to {output} file for CSDS')

    current_time = datetime.now()
    file_name = current_time.strftime('%Y-%m-%dT%H:%M:%S')

    if output == 'JSON':
        file_path = f'./json_responses/{file_name}.json'

        with open(file_path, 'w') as json_file:
            json.dump(response, json_file)

    if output == 'CSV':
        file_path = f'./csv_responses/{file_name}.csv'

        df = pd.DataFrame(response)
        df.to_csv(file_path, index=False)


def _format_state_data(datum: Dict[str, Any], collection_name: str) -> Dict[str, Any]:
    state_data = {}

    for key, value in datum.items():
        if key != 'id':
            state_data[key] = value

        if key == 'valueType':
            state_data[key] = value.upper()

    state_data['collectionName'] = collection_name

    return state_data


def _create_state_data(list_data: List[Dict[str, Any]], collection_name: str) -> List[Dict[str, Any]]:
    print(f'Validating {len(list_data)} states for CSDS')

    state_data_list = []
    for datum in list_data:
        state_data_list.append(_format_state_data(datum, collection_name))

    return state_data_list


def _validate_csv_header(headers: List) -> None:
    if not set(CSDS_REQUIRED_FIELDS).issubset(set(headers)):
        raise ValueError(f'CSV must include required headers: {CSDS_REQUIRED_FIELDS}')


def _csv_to_list(filename: str) -> Dict[str, Any]:
    try:
        data_frame = pd.read_csv(
            filename,
            skipinitialspace=True,
            usecols=lambda x: not x.startswith('Unnamed'),
        )

        headers = data_frame.columns.tolist()
        _validate_csv_header(headers)

        data = data_frame.to_dict(orient='records')
        return data

    except Exception as e:
        print(f'Validation Exception: {e}')
        sys.exit(1)


def _json_to_list(filename: str) -> Dict[str, Any]:
    try:
        with open(filename, 'r') as json_file:
            data = json.load(json_file)

        for datum in data:
            headers = datum.keys()
            _validate_csv_header(headers)

        return data

    except Exception as e:
        print(f'Validation Exception: {e}')
        sys.exit(1)


def _create_csds_states(states: List[Dict[str, Any]]) -> None:
    print(f'Inserting {len(states)} states for CSDS')

    try:
        response = state_data_store.create_states(states, env='dev')

        success = response['data']['createStates']['success']
        if success == True:
            print(f'Successfully inserted {len(states)} State(s) in CSDS')
        else:
            message = response['data']['createStates']['message']
            print(f'Failed to insert: {message}')
    except Exception as e:
        print(f'Error: {e}')


def _get_csds_states(collection_name: str, output: str) -> None:
    print(f'Quering {collection_name} in states for CSDS')

    try:
        response = state_data_store.get_states(collection_name, env='dev')

        if response['data']['states']:
            _write_file_type(response['data']['states'], output)
            print(f'Successfully retrieved states in CSDS and wrote {output} response')
    except Exception as e:
        print(e)


def setup() -> None:
    try:
        os.mkdir('csv_responses')
        os.mkdir('json_responses')
    except:
        pass


def main():
    setup()

    parser = argparse.ArgumentParser(description='Publish or Query States from Clipper State Data Store')
    parser.add_argument(
        '-a',
        '--action',
        required=True,
        help='session id on parasol (ex: LOAD_STATES or QUERY_STATES)',
    )
    parser.add_argument(
        '-c',
        '--collection',
        required=True,
        help='name of the collection in csds (ex: mast-fsw-params)',
    )
    parser.add_argument('-i', '--input', help='path to the csv or json input file (ex: ./sample.csv)')

    parser.add_argument(
        '-o',
        '--output',
        default='JSON',
        help='format to write output response (ex: CSV or JSON',
    )

    args = parser.parse_args()

    if args.action == 'LOAD_STATES':
        if args.input is None:
            print('Please pass in a valid path to a .csv or .json file')
            return

        if not os.path.exists(args.input):
            print(f'File {args.input} could not be found. Please check the file path.')
            return

        filetype = _get_file_type(args.input)

        data = None
        if filetype == 'csv':
            list_data = _csv_to_list(args.input)
            data = _create_state_data(list_data, args.collection)

        elif filetype == 'json':
            list_data = _json_to_list(args.input)
            data = _create_state_data(list_data, args.collection)

        else:
            print(f'Please provide a valid .csv or .json file.')
            return

        if data is not None:
            _create_csds_states(data)

    if args.action == 'QUERY_STATES':
        _get_csds_states(args.collection, args.output)


if __name__ == '__main__':
    main()
