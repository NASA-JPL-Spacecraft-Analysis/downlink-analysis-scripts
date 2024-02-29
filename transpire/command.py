import re, os, logging, struct, click, glob

import xmltodict

from dictionary import Dictionary, __DICTIONARY_LOCATION__

from dplib.clipper import parse_dp
from jpl_time import Time, Duration

def rich_logger(level=logging.WARNING, logger_name='rich'):
    '''Establishes a "proper" ``logging`` instance via the ``rich`` module.

    :param level: ``logging`` module logging level, e.g. ``logging.INFO``. Defaults to ``logging.WARNING``.
    :type level: ``logging`` level.
    :param datefmt: The string format for the date/time printing. Defaults to ``"[%Y-%jT%H:%M:%S]"``,
    :type datefmt: ``str``

    :Example: All the levels!

    >>> import logging
    >>> logger = rich_logger(level=logging.INFO)
    >>> logger.info('This is an INFO message, my friend.')
    '''
    logging.basicConfig( level=level, format='%(message)s')
    return logging.getLogger(logger_name)


def fancy_repr_html(class_name, repr_data):
    title = f'<span style="color:steelblue; font-weight: bold;">{class_name}</span>'
    data = ', '.join(
        [f'<code><span style="color: grey;">{k}</span>=<span style="color: green;">{v}</span></code>' for k, v in
         repr_data.items()])
    return f'{title}({data})'

def stringid_from_vcid(vcid):
    if vcid in [0,1]:
        return 'A'
    elif vcid in [32,33]:
        return 'B'
    return None


def extract_dictionary_path_from_emd(dp, emd=None):
    '''Unpacks the ".emd" file for the supplied .dat and extracts the path to the dictionary from this EMD. The EMD is assumed to be adjacent if not specified. If either the .dat or the (inferred or supplied) .emd file don't exist, returns ``None``.

    :param dp: Path to a Data Product ``.dat`` file. Required.
    :type dp: ``str`` (valid system path)
    :param emd: Path to a Data Product ``.emd`` file. If not supplied, the EMD filename is inferred from the ``.dat`` and assumed to be immediately adjacent to that ``.dat``.
    :type emd: ``str`` (valid system path)
    :return: ``str`` (valid system path) or ``None``

    :Example: Basic usage:

    >>> extract_dictionary_path_from_emd('/path/to/0032_0631149834-0026853-1.dat')
    '/proj/europa/fs/rc_dict/eurc/R8.0.0.0_RC1'

    :Example: Supply the EMD manually if for some reason it's not adjacent:

    >>> dp = extract_dictionary_path_from_emd('/path/to/0032_0631149834-0026853-1.dat', emd='/other/path/to/0032_0631149834-0026853-1.emd')
    '''

    _log = rich_logger(level=logging.WARNING, logger_name='eurc_vnv.common')

    # check that the DP exists
    if not os.path.exists(dp):
        _log.warning(f'File "{dp}" does not exist. Returning None.')
        return None, None

    # construct the EMD filename and check for existence
    emd_file = f'{os.path.splitext(dp)[0]}.emd' if emd is None else emd
    if not os.path.exists(emd_file):
        raise Exception(f'Inferred EMD file "{os.path.basename(emd_file)}" does not exist adjacent to "{dp}".')
        # _log.warning(f'Inferred EMD file "{os.path.basename(emd_file)}" does not exist adjacent to "{dp}". Returning None.')
        # return None, None

    # read the EMD file
    with open(emd_file, 'r') as the_emd_file:
        read_emd = the_emd_file.read()

    # turn it into a Dict
    emd_dict = xmltodict.parse(read_emd)

    # extract what we care about and insert "eurc" to get a valid path.
    sessionId = emd_dict['mm-emd:EarthProductMetadata']['mm-emd:SessionInformation']['mpcs:SessionId']
    dictionary_path = os.path.join(sessionId['mpcs:FswDictionaryDir'], 'eurc', sessionId['mpcs:FswDictionaryVersion'])
    dictionary_version = sessionId['mpcs:FswDictionaryVersion']

    return dictionary_path, dictionary_version

class Command:

    '''A class to reason about FSW and HDW commands.

    :param dictionary_path: Path to the folder containing a ``command.xml`` file, per the ``Dictionary`` class. If not provided, defaults to the default of that class.
    :type dictionary_path: ``str`` 
    '''

    # the FSW release where the opcode no longer appears in the first two bytes of the Arguments data in Command History DPs
    opcode_removal_breakpoint = '10_1_0_0'

    def __init__(self, dictionary_path=__DICTIONARY_LOCATION__, log_level=logging.INFO):
        log_level = logging.INFO
        self.log = rich_logger(level=log_level, logger_name='Command')

        # load the command dictionary
        #dictionary_path = "/Users/fhy/git/eas/clipper/fhy_sandbox/dp100ocs/fsw_dicts/eurc/EURC_R10_2_0_0"
        self.dictionary_path = dictionary_path
        self.Dictionary = Dictionary(dictionary_path=dictionary_path, ingest_all=False)
        self.Dictionary.ingest_command()
        self.Dictionary.ingest_param()

        # set decimal precision on Time object reprs
        self.Time = Time()
        self.Time.set_output_decimal_precision(6)

        # translation from FSW types to struct types
        self.type_map = {
            'integer_arg': {
                8: '>b',
                16: '>h',
                32: '>i',
                64: '>q'
            },
            'unsigned_arg': {
                8: '>B',
                16: '>H',
                32: '>L',
                64: '>Q'
            },
            'float_arg': {
                32: '>f',
                64: '>d'
            },
            'enum_arg': {
                8: '>B',
                16: '>H',
                32: '>L',
                64: '>Q'
            }
        }

    def __repr__(self):
        return f'Command(dictionary_path="{self.dictionary_path}", commands={len(self.Dictionary.command)}, parameters={len(self.Dictionary.param)})'

    def _repr_html_(self):
        return fancy_repr_html('Command', dict(dictionary_path=f'"{self.dictionary_path}"', commands=len(self.Dictionary.command), parameters=len(self.Dictionary.param)))
        
    def extract_command_history(self, dat, extract_enums=True, pretty=True):

        '''Decodes an APID 100 Command History data product into a human-readable list per the command dictionary in ``self.Dictionary``. Handles all argument types including repeat and variable-length strings. 

        :param dat: Full path to ``.dat`` file for decoding. Returns ``None`` if does not exist.
        :type dat: ``str`` (valid file path)
        :param extract_enums: Whether to translate enumerated arguments from their raw integer to a string containing both the integer and the enumerated value per the command dictionary; also includes system parameter data via the parameter dictionary. Defaults to ``True``. Note that the ``Dictionary`` object can be parsed for its ``command_enum`` attribute after the fact if you want to do it yourself (thus preserving the original non-enumerated values for... whatever!).
        :type extract_enums: ``bool``
        :param pretty: Joins the arguments into a key-value string pair (e.g. ``"arg1=7.0, arg2='foobar', ..."``) for pretty display. Defaults to ``True``. Note that this turns the "arguments" key into a string rather than a list of key-value pairs.
        :type pretty: ``bool``
        :return: ``list`` of executed commands and their arguments in the order provided by the APID 100 DP (which is presumably SCLK-ordered). Other metadata for each command are provided: command source (e.g. "VC1"), command number, sequence engine number, validation status, CCO flag state, and the opcode. That is, all data fields from each item in this DP are returned, with no exceptions.
        '''

        # get the "underscored" version of the FSW version from the EMD -- see later
        _, dp_fsw_version = extract_dictionary_path_from_emd(dat)
        dp_fsw_version = dp_fsw_version.replace('EURC_R', '')
        # (yes, you can say "<" on a string as long as the formats are coming in identically.)
        if dp_fsw_version < self.opcode_removal_breakpoint:
            self.log.warning(f'DP FSW version "{dp_fsw_version}" is less than "{self.opcode_removal_breakpoint}" -- accounting for extra opcode data in the DP...')
        
        # parse it with fast freaking magic. note that "dictionary_version" value has decimals instead of underscores
        # but parse_dp is tolerant of that format.
        with parse_dp(dat, dictionary_path=self.Dictionary.dictionary_path, dictionary_version=self.Dictionary.version) as the_dp:
            dp_content = the_dp.data
            dp_metadata = the_dp.metadata
            dp_metadata.update(the_dp.session_info)

        extracted = []
        for c in dp_content['repeat_block']:

            # build the record base
            this = { 
                'filename': os.path.basename(dat), 
                'sessionId': dp_metadata['SessionId']['Number'], 
                'stringId': stringid_from_vcid(dp_metadata['Vcid']) 
            }
            for k, v in c.items():
                if k == 'Arguments':
                    continue
                # we force these types because the parse_dp structure doesn't like getting de-pickled (e.g. in a session report cache)
                # because they use custom types.
                this.setdefault('time_seconds', int(c['time_seconds']))
                this.setdefault('time_subseconds', int(c['time_subseconds']))
                this.setdefault('cmd_source', str(c['cmd_source']))
                this.setdefault('cmd_number', int(c['cmd_number']))
                this.setdefault('seq_engine_number', int(c['seq_engine_number']))
                this.setdefault('cmd_validation_status', str(c['cmd_validation_status']))
                this.setdefault('cmd_constraint_override', str(c['cmd_constraint_override']))
                this.setdefault('opcode', int(c['opcode']))
                this.setdefault('bytes_of_arguments', int(c['bytes_of_arguments']))

            # fix the opcode, good lord
            _pf = f'{this["opcode"]:04x}'.upper()
            this['opcode'] = f'0x{_pf}'

            # get the command stem because opcodes are for losers
            if this['opcode'] not in self.Dictionary.opcodes:
                self.log.warning(f'opcode="{this["opcode"]}" does not exist in your command dictionary.')
                this.setdefault('stem', None)
            else:
                this.setdefault('stem', self.Dictionary.opcodes[this['opcode']]['stem'])

            # convert to proper SCLKD and SCET
            t = float(this['time_seconds']) + float(this['time_subseconds']) / float(2**32) # subseconds is 4-byte number in this context
            this.setdefault('sclk', t)

            # print("!!\n!!\n!! Todo: Figure out why jpltime/chronos/spice is not happy with converting scet to sclk!!\n!!\n!!\n")
            # I am guessing I need some kind of chronos file setup
            this.setdefault('scet', self.Time.from_sclkd(t).to_scet())
            # this.setdefault('scet', self.Time.from_sclkd(t, spacecraft_id=-159).to_scet()) #passing in spacecraft id manually does not work either
            # this.setdefault('scet', "!!! *** ^^^ TODO: SEARCH_FOR_from_sclkd_IN_command.py  ^^^ *** !!!")

            # extract the list of bytes from the Arguments field
            argument_data = [ _['argument_bytes'] for _ in c['Arguments'] ]

            # if FSW is less than R10.0.0.0, the opcode takes up the first two bytes; skip them. otherwise take as-is.
            # (yes, you can say "<" on a string as long as the formats are coming in identically.)
            if dp_fsw_version < self.opcode_removal_breakpoint:
                argument_data = argument_data[2:]
            
            # build the packed data based on the number of bytes in this argument set
            packed_argument_data = struct.pack(f'>{"B"*len(argument_data)}', *argument_data)
            
            # initialize our offset position within the argument_data for this command
            position = 0

            # now, associate the arguments to the dictionary. skip if no arguments (i.e. is a HDW command).
            this['arguments'] = []
            if this['stem'] is not None and this['stem'] in self.Dictionary.command and 'arguments' in self.Dictionary.command[this['stem']]:

                # check that we have the right number of arguments. this can be 0 if command validation failed
                # before argument validation, and the arguments don't get populated. if cmd_validation_status 
                # is non-0 (indicating a failure) but there are arguments to parse, we will try to do so just
                # to ensure we show everything we can. 
                # anwyays, if we don't have the right number of arguments, then skip extraction and just 
                # append the record without that data (but keep everything else).
                n_args_reqd = len(self.Dictionary.command[this['stem']]['arguments'])
                if len(argument_data) == 0 and n_args_reqd != 0:
                    self.log.warning(f'Command {this} contains 0 arguments in the DP but requires {n_args_reqd} arguments. Skipping argument extraction.')
                    extracted.append(this)
                    continue
                
                for arg in self.Dictionary.command[this['stem']]['arguments']:
                    
                    # if repeat argument, gotta loop-dee-loop
                    if arg['argument_type'] == 'repeat_arg':
                            
                        arg_value_repeated = []

                        # "packed_argument_data[position]" is the total number of repeats identified herein.
                        n_repeat_args = packed_argument_data[position]

                        # if this first byte is 0 then there are no repeated values for this argument name.
                        if n_repeat_args == 0:
                            arg_value_repeated.append(None)
                        
                        # move past the first byte
                        position += 1

                        # multi-element repeat arguments alternate through their sets (e.g. if there are two args within
                        # this repeat argument, it'll do 1 then 2 then 1 then 2 then... etc.). thus, for the total number 
                        # of repeats identified by the first byte, loop through each set and extract.
                        for _ in range(0, n_repeat_args):

                            for rarg in arg['repeat_arguments']:
                                # extract!
                                arg_value, advance_by = self._extract_argument_value(rarg, packed_argument_data, position, extract_enums=extract_enums)
                                # append!
                                arg_value_repeated.append({rarg['argument_name']: arg_value})
                                # advance!
                                position += advance_by

                        # set this repeat arg to the array of key-values, not a key-value pair like non-repeats
                        this['arguments'].append(dict(argument_name=arg['argument_name'], argument_value=arg_value_repeated))

                            
                    else:
                        
                        # extract
                        arg_value, advance_by = self._extract_argument_value(arg, packed_argument_data, position, extract_enums=extract_enums)

                        # set the arg value into this record
                        this['arguments'].append(dict(argument_name=arg['argument_name'], argument_value=arg_value))
                        
                        # advance the offset position by the number of bytes we've processed heretofore
                        position += advance_by
                    
            # now post-annotate the parameter commands for enum_param types. other annotations could be done
            # at the single-argument level but parameter commands require knowledge across command arguments,
            # specifically "param_id" so we can look it up in the dictionary and get its enum map. must have
            # extract_enums=True (otherwise why bother), it must be a parameter command, and it must have
            # 'param_id' and 'value' argument names.
            if extract_enums is True and this['stem'] is not None and this['stem'].startswith('DDM_SET_SYS_PARAM_') and 'param_id' in this['arguments'] and 'value' in this['arguments']:
                # since extract_enums=True already we know we need to look up param_name, not param_id...
                _name = this['arguments']['param_id']
                # ... except sometimes a bad argument can be used intentionally, so the enumeration may
                # have failed beforehand, causing a name lookup to fail. cover this case.
                _types = None
                if _name in self.Dictionary.param_by_name:
                    _types = list(self.Dictionary.param_by_name[_name]['parameter_type'])
                elif _name in self.Dictionary.param:
                    _types = list(self.Dictionary.param[_name]['parameter_type'])
                # only continue if type of the parameter is 'enum_param'.
                if _types and _types[0] == 'enum_param':
                    # get the enumeration name from the dictionary.
                    _enum_name = self.Dictionary.param_by_name[_name]['parameter_type']['enum_param']['@enum_name']
                    # loop on the enumeration mapping until the numeric value is found for this command instance, 
                    # then replace the argument value with the enumeration.
                    for e in self.Dictionary.param_enums[_enum_name]['values']['enum']:
                        if arg_value == int(e['@numeric']):
                            this['arguments']['value'] = e['@symbol']
                            # break once you've found it
                            break

            # append "this"
            extracted.append(this)

        # set for pretty display if asked for; otherwise you just get back the key-value structure.
        if pretty:
            for e in extracted:
                e['arguments'] = ', '.join([ f'{a["argument_name"]}={a["argument_value"]}' for a in e['arguments'] ])

        return extracted

    def _extract_argument_value(self, argument, packed_argument_data, position, extract_enums=True):

        '''The magic extractor of the raw argument data bytes. The logic here is to loop through each byte and extract the data depending on the specified type (e.g. string, integer, float, ...) and advance the pointer for the higher-level caller ``extract_command_history``.

        - argument             : the argument metadata (name/type/length/etc.)
        - packed_argument_data : the bytes of the argument data from the data product
        - position             : the current byte position within packed_argument_data
        - extract_enums        : whether to convert enumerations of argument values to their string per the dictionary
        '''

        # variable-length string arguments are special!
        if argument['argument_type'] == 'var_string_arg':
            # get n_characters from the current position
            n_characters = packed_argument_data[position]
            # if the first byte for this argument is 0, return None and skip the whole byte (by returning "None" to data and "1" to "advance_by")
            if n_characters == 0:
                return None, 1
            # else, skip position by 1 to advance past the var count byte and further advance by the number of characters identified in this first byte
            fmt = f'>{"B"*(n_characters)}' 
            # advance_by is the number of characters plus 1 (the field telling us how many characters)
            advance_by = n_characters + 1
            # set start and end positions of the byte range, less simply -- start at +1, which is where the characters start,
            # and end at at n_characters.
            start = position + 1
            end = start + n_characters
        else:
            # in the case of non-variable argugment lengths, advance_by is the size of the argument per the dictionary
            advance_by = int(argument['argument_length']/8) # divide by 8 for bits-to-bytes, since our packed data are in bytes
            fmt = self.type_map[argument['argument_type']][argument['argument_length']]
            # set start and end positions of the byte range, simply
            start = position
            end = start + advance_by
        
        # unpack the data for this byte range. POINTERS?! WHERE WE'RE GOING WE DON'T NEED POINTERS!
        unpacked = struct.unpack(fmt, packed_argument_data[start:end])
        
        # if it's a string arg, use all the bytes and chr-ify them
        if argument['argument_type'] == 'var_string_arg':
            _av = ''.join([chr(i) for i in unpacked])
            # it just seems right to proper-quote a string arg... man...
            arg_value = f'"{_av}"'
        else:
            # else it's just the single value (which may be a range of bytes); unpack returns a 1-element tuple so must pull out 0th index.
            arg_value = unpacked[0]
            # check if enum_arg and extract the enumeration if asked for.
            if argument['argument_type'] == 'enum_arg' and extract_enums is True:
                if arg_value in self.Dictionary.command_enum[argument['argument_enum']]:
                    arg_value = self.Dictionary.command_enum[argument['argument_enum']][arg_value]
                else:
                    self.log.debug(f'Argument name={argument["argument_name"]} with value={arg_value} is not in the enumeration ({self.Dictionary.command_enum[argument["argument_enum"]]}). Annotating nothing.')
            # special handling for param_id translation to a useful name.
            elif argument['argument_name'] == 'param_id' and extract_enums is True:
                # 0-pad the hex value to 8 characters (nice), then upper all the chars (guh) so it matches the dictionary convention.
                _id = f'0x{f"{arg_value:08x}".upper()}'
                # sometimes the param.xml doesn't exist because reasons. verify that it exists and the param ID also exists in it.
                if self.Dictionary.param is not None and _id in self.Dictionary.param:
                    arg_value = self.Dictionary.param[_id]['@param_name']
                else:
                    self.log.warning(f'"{_id}" is not in the selected dictionary, or the dictionary object is null. Cannot enumerate this parameter.')

        # return the unpacked data and the amount to advance the position
        return arg_value, advance_by

