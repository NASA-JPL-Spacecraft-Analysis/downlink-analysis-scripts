#!/usr/bin/env python
import argparse
import json
import numbers
import os

import constants

import parasol
from close_the_u import state_data_store


def _getEnvVenue(env):
    if env == 'dev':
        return {
            'parasol_host': 'parasol.eurc-dev.jpl.nasa.gov',
            'cookie_name': 'ecDevRhel8Sso'
        }


def _insertStates(venue, states):
    response = state_data_store.create_states(states, env=venue)

    if response['data']['createStates']['success'] == True:
        print('Successfully inserted {} states into Clipper State Data Store'.format(len(states)))


def _composeState(args, parameter_name, volatility, data):
    state = None

    value = data['value']
    evidence = data['evidence'][0]

    state = {
        'sessionId': args.session,
        'collectionName': args.collection,
        'name': parameter_name,
        'scet': evidence['scet'],
        'volatility': volatility,
        'value': value if isinstance(value, numbers.Number) else -99999,
    }

    if state is not None:
        defaults = {
            'type': constants.TYPE,
            'valueType': constants.VALUE_TYPE
        }
        state.update(defaults)

    return state


def getParameterValues(args):
    filename = './parsol_params/{}_{}_{}_{}.json'.format(args.host, args.session, args.scet, args.vcid)

    if os.path.exists(filename):
        print('Using saved response for Parasol for parameter values')
        with open(filename) as parasol_parameter_values:
            return json.load(parasol_parameter_values)

    else:
        print('Making request to Parasol for parameter values')
        venue = _getEnvVenue(args.env)
        response = parasol.get_parameter_values(
            phase='cruise',
            time_str=args.scet,
            time_type='scet',
            session_host=args.host,
            session_id=args.session,
            vcid=args.vcid,
            auth_type='cam',
            parasol_host=venue['parasol_host'],
            cookie_name=venue['cookie_name']
        )
        print('Received response from Parasol')

        with open(filename, 'w') as json_file:
            json.dump(response, json_file, indent=4, sort_keys=False, separators=(',', ': '))

        return response


def buildModuleStates(args, response):
    for module_name, module in response.items():
        states = []
        print('Composing states for module {}'.format(module_name))

        for parameter_name, parameter in module[constants.GROUP][constants.COPY].items():
            for volatility, data in parameter.items():
                if volatility.upper() in [member.value for member in state_data_store.enum_classes['volatility']]:

                    try:
                        if isinstance(data, list):
                            data = data[0]

                        state = _composeState(args, parameter_name, volatility.upper(), data)
                        if state is not None:
                            states.append(state)

                    except ValueError as err:
                        print(err)
                        pass

        print('Composed {} states for module: {}'.format(len(states), module_name))
        _insertStates(args.env, states)


def setup():
    try:
        os.mkdir('parasol_responses')
    except:
        pass


def main():
    setup()

    parser = argparse.ArgumentParser(description='Publish FSW Parameters from Parasol to Clipper State Data Store')
    parser.add_argument('--host', required=True, help='session host on parasol (ex: eurcits001)')
    parser.add_argument('--session', required=True, help='session id on parasol (ex: 578)')
    parser.add_argument('--scet', required=True, help='a scet formatted time (ex: 2023-136T22:08:51.038)')
    parser.add_argument('--collection', required=True, help='name of the data store collection to publish parasol data (ex: eurcits001-578)')
    parser.add_argument('--vcid', type=int, default=0, help='vcid 0 or 1 (ex: 0)')
    parser.add_argument('--env', default='dev', help='venue for retrieving parameter values and publishing (ex: dev)')
    args = parser.parse_args()

    parasol_response = getParameterValues(args)
    buildModuleStates(args, parasol_response)


if __name__ == "__main__":
    main()
