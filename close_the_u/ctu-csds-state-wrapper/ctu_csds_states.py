#!/usr/bin/env python
import argparse
import json

import os
import pandas as pd
import re

from datetime import datetime
from close_the_u import state_data_store


def _get_file_type(filename):
    extension_regex = r'[^.]+$'
    return re.search(extension_regex, filename).group()


def _write_file_type(response, output):
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


def _ensure_required_csds_keys(datum):
    CSDS_DEFAULTS = {
        'name': None,
        'scet': None,
        'value': -99999,
        'valueType': 'PREDICTED',
    }

    for key, value in CSDS_DEFAULTS.items():
        if key not in datum:
            datum[key] = value

    return datum


def _validate_state_data(list_data, collection_name):
    print(f'Validating {len(list_data)} states for CSDS')

    for datum in list_data:
        # handle required keys for create states
        datum = _ensure_required_csds_keys(datum)

        # set collection name
        datum['collectionName'] = collection_name

        # remove id before insertion
        if 'id' in datum:
            del datum['id']

        # TODO handle CSDS enums

    return list_data


def _csv_to_list(filename):
    try:
        data_frame = pd.read_csv(
            filename,
            skipinitialspace=True,
            usecols=lambda x: not x.startswith('Unnamed'),
        )
        data = data_frame.to_dict(orient='records')

        return data

    except Exception as e:
        print('Exception: _csv_to_array')
        print(e)


def _json_to_list(filename):
    try:
        with open(filename, 'r') as json_file:
            data = json.load(json_file)

        return data

    except Exception as e:
        print('Exception: _json_to_list')
        print(e)


def _create_csds_states(states, output):
    print(f'Inserting {len(states)} states for CSDS')
    response = state_data_store.create_states(states, env='dev')

    try:
        if response['data']['createStates']['success'] == True:
            print(f'Successfully inserted {len(states)} in CSDS and wrote {output} response')
    except Exception as e:
        print(e)


def _get_csds_states(collection_name, output):
    print(f'Quering {collection_name} in states for CSDS')
    response = state_data_store.get_states(collection_name, env='dev')

    try:
        if response['data']['states']:
            _write_file_type(response['data']['states'], output)
            print(f'Successfully retrieved states in CSDS and wrote {output} response')
    except Exception as e:
        print(e)


def setup():
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
    parser.add_argument(
        '-i',
        '--input',
        help='path to the csv or json input file (ex: ./sample.csv)'
    )

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
            data = _validate_state_data(list_data, args.collection)

        elif filetype == 'json':
            list_data = _json_to_list(args.input)
            data = _validate_state_data(list_data, args.collection)

        else:
            print(f'Please provide a valid .csv or .json file.')
            return

        if data is not None:
            _create_csds_states(data, args.output)

    if args.action == 'QUERY_STATES':
        _get_csds_states(args.collection, args.output)


if __name__ == '__main__':
    main()
