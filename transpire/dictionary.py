import os, logging, xmltodict, pickle, click, glob, re, sys, json
from bs4 import BeautifulSoup

#__dd = '/dict/eurc/current/'

print("\n!!\n!!\n!! dictionary.py comment out __dd fhy stuff before commit !!\n!!\n!!\n")
__dd = "/Users/fhy/git/eas/clipper/fhy_sandbox/dp100ocs/fsw_dicts/eurc/EURC_R10_2_0_0/"

__DICTIONARY_LOCATION__ = __dd if os.path.exists(__dd) else os.path.join(os.environ['DICT'], 'current')
__DICTIONARY_CACHE_LOCATION__ = '/proj/europa/fs/tools/.dictionary'
__CACHE_FILENAME_TEMPLATE__ = '{}.Dictionary.pickle'


#def rich_logger(level=logging.WARNING, datefmt=f'[{UTC_FMT_TRUNCATED}]', logger_name='rich'):
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

class DictionaryError(Exception):
    pass
class Dictionary:

    '''Manages the ingestion of FSW dictionaries as more convenient Python objects.

    :param dictionary_path: The directory containing the XML dictionaries. Defaults to latest release in ``__DICTIONARY_LOCATION__`` "current".
    :type dictionary_path: ``str``
    :param ingest_all: Indicates that all dictionaries should be ingested. Defaults to ``False``.
    :type ingest_all: ``bool``
    :param cache: Indicates that the ingested dictionaries should be cached/pickled. Defaults to ``False``. CURRENTLY STUBBED.
    :type cache: ``bool``
    :param cache_to: The location to store the cached dictionary, if ``cache=True``. Defaults to ``__DICTIONARY_CACHE_LOCATION__``. CURRENTLY STUBBED.
    :type cache_to: ``str`` (path)
    :param log_level: Logging level per the ``logging`` module. Defaults to ``logging.WARNING``.
    :type log_level: ``logging`` level

    :Example: Give it your own path, and inspect some of its attributes extracted from the headers of our dictionaries:

    >>> D = Dictionary(dictionary_path='/dict/eurc/EURC_R10_1_0_2')
    >>> D.version # probably "8.0.1.2"
    >>> D.mission_name # "EUROPA_CLIPPER"

    :Example: Get all the dictionaries for the default release:

    >>> D = Dictionary(ingest_all=True)
    >>> D.apid    # APID dictionary
    >>> D.channel # Channel dictionary
    >>> # ... etc.

    :Example: Only ingest, say, the APID dictionary:

    >>> D = Dictionary()  # ingest_all defaults to False
    >>> d.ingest_apid()
    >>> d.apid            # the APID dictionary
    '''

    def __init__(self, dictionary_path=__DICTIONARY_LOCATION__, ingest_all=False, cache=False, cache_to=__DICTIONARY_CACHE_LOCATION__, log_level=logging.WARNING):

        self.log = rich_logger(level=log_level, logger_name='Dictionary')
        self.cache = cache
        self.cache_to = cache_to
        
        dictionary_path = os.path.abspath(dictionary_path)
        if not os.path.exists(dictionary_path):
            raise DictionaryError(f'"{dictionary_path}" does not exist!')
        if not os.path.isdir(dictionary_path):
            raise DictionaryError(f'"{dictionary_path}" is not a directory!')
        self.dictionary_path = dictionary_path
        
        # for the version etc. info, open the APID XML because it's fast.
        _dict_info = self._read_xml('apid.xml')
        if _dict_info is None:
            raise DictionaryError('Could not parse the APID XML file, so I cannot figure out anything about this build.')
        dictionary = xmltodict.parse(_dict_info)
        for k,v in dictionary['apid_dictionary']['header'].items():
            setattr(self, k.replace('@',''), v)

        if ingest_all is True:
            self._ingest_all()
        
    def __repr__(self):
        return f'Dictionary(version="{self.version}", dictionary_path="{self.dictionary_path}", apids={len(getattr(self, "apid",[]))}, channels={len(getattr(self, "channel",[]))}, commands={len(getattr(self, "command",[]))}, evrs={len(getattr(self, "evr",[]))}, instrument_commands={len(getattr(self, "instrument_commands",[]))}, monitor_responses={len(getattr(self, "monitor_responses",[]))}, parameters={len(getattr(self, "param",[]))})'

    def _repr_html_(self):
        return fancy_repr_html('Dictionary', dict(version=f'"{self.version}"', dictionary_path=f'"{self.dictionary_path}"', apids=len(getattr(self, 'apid',[])), channels=len(getattr(self, 'channel',[])), commands=len(getattr(self, 'command',[])), evrs=len(getattr(self, 'evr',[])), instrument_commands=len(getattr(self, 'instrument_commands',[])), monitor_responses=len(getattr(self, 'monitor_responses',[])), parameters=len(getattr(self, 'param',[]))))
    
    def _read_xml(self, xml_fname, backup_xml_fname=None):
        # sandboxes sometimes have these "global_ac" names. try both.
        p = os.path.join(self.dictionary_path, xml_fname)
        if not os.path.exists(p) and backup_xml_fname is None:
            self.log.warning(f'"{p}" does not exist and no backup_xml_fname was provided!')
            return None
        elif not os.path.exists(p) and backup_xml_fname is not None:
            p = os.path.join(self.dictionary_path, backup_xml_fname)
            if not os.path.exists(p):
                self.log.warning(f'Expected XML file does not exist and backup_xml_fname="{p}" does not exist!')
                return None
        with open(p, 'r') as _xml:
            _xml_read = _xml.read()
        return _xml_read

    def _ingest_all(self):
        self.ingest_apid()
        self.ingest_channel()
        self.ingest_command()
        self.ingest_evr()
        self.ingest_instrument_commands()
        self.ingest_monitor_responses()
        self.ingest_param()
        if self.cache:
            self.cache_dictionary()

    def cache_dictionary(self):
        
        self.log.warning('cache_dictionary is STUBBED, see issue #37.')
        return

        self.log.debug('Caching the dictionary...')
        f = __CACHE_FILENAME_TEMPLATE__.format(self.version)
        if not os.path.exists(self.cache_to):
            self.log.warning(f'Default cache location "{self.cache_to}" does not exist. Using "/tmp".')
            _dest = os.path.join('/tmp/', f)
        else:
            _dest = os.path.join(self.cache_to, f)
        self.log.debug(f'Cached dictionary destination: "{_dest}"')
        if os.path.exists(_dest):
            self.log.warning(f'Destination pickle "{_dest}" already exists. Updating...')
        with open(_dest, 'wb') as rick_and_morty_joke:
            pickle.dump(self, rick_and_morty_joke)

    def ingest_apid(self):
        self.log.debug('Running ingest_apid...')
        apid_read = self._read_xml('apid.xml', backup_xml_fname='global_ac_apid.xml')
        if apid_read is None:
            self.apid = None
            return
        apids = [ dict(_) for _ in xmltodict.parse(apid_read)['apid_dictionary']['apids']['apid_definition'] ]
        for d in apids:
            d['@apid'] = int(d['@apid'])
        self.apid = { int(d['@apid']): d for d in apids }
    
    def ingest_channel(self):
        self.log.debug('Running ingest_channel...')
        channel_read = self._read_xml('channel.xml', backup_xml_fname='global_ac_eha.xml')
        if channel_read is None:
            self.channel = None
            return
        channels = xmltodict.parse(channel_read)
        cd = channels['telemetry_dictionary']['telemetry_definitions']['telemetry']
        self.channel = { c['@abbreviation']:c for c in cd }
        # now do enums
        self.channel_enum_from_numeric = {}
        self.channel_enum_to_numeric = {}
        for enum in channels['telemetry_dictionary']['enum_definitions']['enum_table']:
            self.channel_enum_from_numeric.setdefault(enum['@name'], {})
            self.channel_enum_to_numeric.setdefault(enum['@name'], {})
            _type = type(enum['values']['enum'])
            # xmltodict parses single-element things into dicts, not lists. ugh.
            if _type is list:
                for e in enum['values']['enum']:
                    self.channel_enum_from_numeric[enum['@name']].setdefault(int(e['@numeric']), e['@symbol'])
                    self.channel_enum_to_numeric[enum['@name']].setdefault(e['@symbol'], int(e['@numeric']))
            else:
                self.channel_enum_from_numeric[enum['@name']].setdefault(int(enum['values']['enum']['@numeric']), enum['values']['enum']['@symbol'])
                self.channel_enum_to_numeric[enum['@name']].setdefault(enum['values']['enum']['@symbol'], int(enum['values']['enum']['@numeric']))
    
    def ingest_command(self):
        
        self.log.debug('Running ingest_command...')
        
        # we cannot use xmltodict here because it destroys command argument ordering. 
        # use the elegent, if misunderstood, BeautifulSoup methods.
        command_read = self._read_xml('command.xml', backup_xml_fname='global_ac_cmd.xml')
        if command_read is None:
            self.command = None
            return
        soup = BeautifulSoup(command_read, features='xml')

        # extract the enumerations first
        command_enum = {}
        for enum_definition in soup.findAll('enum_definitions'):
            for enum_table in enum_definition.findAll('enum_table'):
                _name = enum_table['name']
                command_enum.setdefault(_name, {})
                for values in enum_table.findAll('values'):
                    command_enum[_name] = { int(enum['numeric']): enum['symbol'] for enum in values.findAll('enum') }
        self.command_enum = command_enum
        
        # initialize command and opcode mappings
        self.command = {}
        self.opcodes = {}

        # let's go...
        for command_definition in soup.findAll('command_definitions'):

            # get hardware commands first. nothing crazy going on here, as they have no arguments.
            for hw_command in command_definition.findAll('hw_command'):
                _info = {
                    'opcode': hw_command['opcode'],
                    'stem': hw_command['stem'],
                    'ops_category': hw_command.find_next('ops_category').string,
                    'description': hw_command.find_next('description').string,
                }
                self.command[hw_command['stem']] = _info
                self.opcodes[hw_command['opcode']] = _info

            # FSW commands get more interesting...
            for fsw_command in command_definition.findAll('fsw_command'):
                
                # initialize
                _opcode = fsw_command['opcode']
                _stem = fsw_command['stem']
                _info = {
                    'opcode': _opcode,
                    'stem': _stem,
                    'arguments': [],
                    'module': fsw_command.find_next('module').string,
                    'ops_category': fsw_command.find_next('ops_category').string,
                    'description': fsw_command.find_next('description').string,
                }
                
                # loop on the arguments...
                for _ in fsw_command.findAll('arguments'):
                                
                    # recursive=False isn't behaving as advertised -- it's finding the args within the repeat tags. clean up later.
                    for arg in _.findAll(['unsigned_arg', 'float_arg', 'enum_arg', 'var_string_arg', 'repeat_arg', 'integer_arg'], recursive=False):
                        
                        # if not a repeat, extract and set idiosyncratic fields based on type
                        argument = {}
                        if arg.name != 'repeat_arg':
                                                
                            argument = { 
                                'argument_name': arg['name'], 
                                'argument_type': arg.name, 
                                'argument_description': arg.find_next('description').string 
                            }
                            _lf = 'bit_length' 
                            if arg.name == 'var_string_arg':
                                _lf = 'prefix_bit_length'
                                argument['argument_string_length'] = arg['max_bit_length']
                            argument['argument_length'] = int(arg[_lf])
                            if arg.name == 'enum_arg':
                                argument['argument_enum'] = arg['enum_name']
                                                    
                        # if repeat_arg, just loop on each and set them as sub-fields to keep the intended structure in place.
                        elif arg.name == 'repeat_arg':
                            
                            argument = { 
                                'argument_name': arg['name'], 
                                'argument_type': arg.name, 
                                'argument_length': int(arg['prefix_bit_length']), 
                                'argument_description': arg.find_next('description').string,
                                'repeat_arguments': [],
                                'max_repeat_arguments': int(arg.find_next('repeat')['max'])
                            }

                            # recursive=False not necessary as there should only be one level of repeats
                            for rarg in arg.findAll(['unsigned_arg', 'float_arg', 'enum_arg', 'var_string_arg', 'integer_arg']):
                                rargument = { 
                                    'argument_name': rarg['name'], 
                                    'argument_type': rarg.name, 
                                    'argument_description': rarg.find_next('description').string 
                                }
                                _lf = 'bit_length' 
                                if rarg.name == 'var_string_arg':
                                    _lf = 'prefix_bit_length'
                                    rargument['argument_string_length'] = rarg['max_bit_length']
                                rargument['argument_length'] = int(rarg[_lf])
                                if rarg.name == 'enum_arg':
                                    rargument['argument_enum'] = rarg['enum_name']
                                argument['repeat_arguments'].append(rargument)
                                
                        _info['arguments'].append(argument)
                        
                # because of the issue with recursive=False above, the repeat args get appended as 
                # regular args to the args list -- crucially, reliably at the end of the list.
                # let's count up the number of repeat arguments in this command and then remove
                # that number of elements from the arg list.
                n_repeats = 0
                for arg in _info['arguments']:
                    if arg['argument_type'] == 'repeat_arg':
                        n_repeats += len(arg['repeat_arguments'])
                _info['arguments'] = _info['arguments'][0:len(_info['arguments']) - n_repeats]

                # update the mappings
                self.command[fsw_command['stem']] = _info
                self.opcodes[fsw_command['opcode']] = _info
    
    def ingest_evr(self):
        self.log.debug('Running ingest_evr...')
        evr_read = self._read_xml('evr.xml', backup_xml_fname='global_ac_evr.xml')
        if evr_read is None:
            self.evr = None
            return
        evrs = xmltodict.parse(evr_read)['evr_dictionary']
        self.evr = { e['@name']: e for e in evrs['evrs']['evr'] }
    
    def ingest_instrument_commands(self):
        self.log.debug('Running ingest_instrument_commands...')
        ic_read = self._read_xml('instrument_commands.xml', backup_xml_fname='global_ac_icmd.xml')
        if ic_read is None:
            self.ic = None
            return
        ic = xmltodict.parse(ic_read)
        self.instrument_commands = ic['instrument_command_dictionary']['instrument_command_headers']['instrument_command_header']
    
    def ingest_monitor_responses(self):
        self.log.debug('Running ingest_monitor_responses...')
        mr_read = self._read_xml('monitor_responses.xml', backup_xml_fname='global_ac_fp.xml')
        if mr_read is None:
            self.mr = None
            return
        mr = xmltodict.parse(mr_read)
        self.monitor_responses = { m['@monitor_name']:m for m in mr['monitor_response_dictionary']['monitors']['monitor'] }
    
    def ingest_param(self):
        self.log.debug('Running ingest_param...')
        param_read = self._read_xml('param.xml', backup_xml_fname='global_ac_param.xml')
        if param_read is None:
            self.param = None
            return
        param = xmltodict.parse(param_read)
        self.param = { p['@param_id']:p for p in param['param-def']['param'] }
        self.param_by_name = { p['@param_name']:p for p in param['param-def']['param'] }
        self.param_enums = { p['@name']:p for p in param['param-def']['enum_definitions']['enum_table'] }
        self.param_groups = { p['@param_group_name']:p for p in param['param-def']['parameter_groups']['parameter_group'] }
        self.reverse_param_groups = {}
        for k,v in self.param_groups.items():
            for pn in v['group_params']['group_param']:
                self.reverse_param_groups.setdefault(pn, k)
    
    def __getstate__(self):
        d = self.__dict__.copy()
        if 'log' in d:
            d['log'] = d['log'].level
        return d

    def __setstate__(self, d):
        if 'log' in d:
            d['log'] = rich_logger(level=d['log'], logger_name='Dictionary')
        self.__dict__.update(d)

class DictionaryRepr:
    '''Base class for Dictionary repr objects.'''
    def __init__(self, entry):
        self.entry = entry
    def __repr__(self):
        return json.dumps(self.entry, indent=4)

dict_command_table = '''
<table style="table-layout:fixed;text-align:left;"">
    <thead>
        <tr style="border-bottom: solid white 1px;">
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">OPCODE</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">STEM</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">OPSCAT</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">MODULE</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">ARGUMENTS</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">DESCRIPTION</th>
        </tr>
    </thead>
    <tbody>
        {body}
    </tbody>
</table>
'''
def dict_command_row(command):
    arguments = ''
    if 'arguments' in command:
        for i,a in enumerate(command['arguments']):
            if a['argument_type'] == 'repeat_arg':
                print(a["argument_name"], a["max_repeat_arguments"])
                arguments += f'{i}. "{a["argument_name"]}" ("{a["argument_type"]}"), repeats={a["max_repeat_arguments"]}<br>'
                for j,r in enumerate(a['repeat_arguments']):
                    print('\t',r)
                    arguments += f'<span style="color:steelblue">&nbsp;&nbsp;&nbsp;&nbsp;[{j}] "{r["argument_name"]}" ("{r["argument_type"]}")</span><br>'
            else:
                arguments += f'{i}. "{a["argument_name"]}" ("{a["argument_type"]}")<br>'
    return f'''
    <tr style="border-bottom: solid white 1px;">
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{command["opcode"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{command["stem"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{command["ops_category"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{command["module"] if "module" in command else ''}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{arguments}</td>
        <td style="text-align:left;border:1pt solid #ccc;">{command["description"]}</td>
    </tr>
    '''    
class DictionaryCommand(DictionaryRepr):
    '''Special class for displaying Dictionary command entries. ``__repr__`` is JSON-pretty and ``_repr_html_`` is a single-row HTML table.

    :param entry: A single entry from ``Dictionary.command``.

    :Example: Display a command!

    >>> d = Dictionary(...)
    >>> d.ingest_command()
    >>> DictionaryCommand(d.command['AVS_MOUNT_EMEM_NAND'])
    '''
    def _repr_html_(self):
        _body = dict_command_row(self.entry)
        return dict_command_table.format(body=_body)

dict_param_table = '''
<table style="table-layout:fixed;text-align:left;"">
    <thead>
        <tr style="border-bottom: solid white 1px;">
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">ID</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">NAME</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">VERSION</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">UNITS</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">TYPE</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">DEFAULT</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">RATIONALE</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">DESCRIPTION</th>
        </tr>
    </thead>
    <tbody>
        {body}
    </tbody>
</table>
'''
def dict_param_row(param):
    _types = list(param['parameter_type'])
    if _types:
        _param_type = _types[0]
        _param_size = param['parameter_type'][_param_type]['@bit_length']
        _type_info = f'{_param_type}<br>({_param_size} bits)'
    return f'''
    <tr style="border-bottom: solid white 1px;">
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{param["@param_id"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{param["@param_name"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{param["@parameter_version"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{param.get("@units")}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{_type_info}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{param["default_value"]}</td>
        <td style="text-align:left;border:1pt solid #ccc;">{param["rationale"]}</td>
        <td style="text-align:left;border:1pt solid #ccc;">{param["sysdesc"]}</td>
    </tr>
    '''  
class DictionaryParameter(DictionaryRepr):
    '''Special class for displaying Dictionary parameter entries. ``__repr__`` is JSON-pretty and ``_repr_html_`` is a single-row HTML table.

    :param entry: A single entry from ``Dictionary.param_by_name`` or ``Dictionary.param``.

    :Example: Display a parameter!

    >>> d = Dictionary(...)
    >>> d.ingest_param()
    >>> DictionaryParameter(d.param_by_name['SEQ_EPOCH_TIME_77']) # by name...
    >>> DictionaryParameter(d.param['0x02100004']       )         # ... or by ID
    '''
    def _repr_html_(self):
        _body = dict_param_row(self.entry)
        return dict_param_table.format(body=_body)
    
dict_apid_table = '''
<table style="table-layout:fixed;text-align:left;"">
    <thead>
        <tr style="border-bottom: solid white 1px;">
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">APID</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">NAME</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">MODULE/OPSCAT</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">AUTO DELETE</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">COMPRESS</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">DEFAULT PRIORITY</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">DESCRIPTION</th>
        </tr>
    </thead>
    <tbody>
        {body}
    </tbody>
</table>
'''
def dict_apid_row(apid):
    _moc = f'module={apid["categories"]["module"]}<br>ops_category={apid["categories"]["ops_category"]}'
    return f'''
    <tr style="border-bottom: solid white 1px;">
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{apid["@apid"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{apid["name"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{_moc}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{apid["downlink_info"]["@auto_delete"] if "downlink_info" in apid else "--"}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{apid["downlink_info"]["@compress"] if "downlink_info" in apid else "--"}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{apid["downlink_info"]["@default_priority"] if "downlink_info" in apid else "--"}</td>
        <td style="text-align:left;border:1pt solid #ccc;">{apid["description"]}</td>
    </tr>
    '''  
class DictionaryApid(DictionaryRepr):
    '''Special class for displaying Dictionary APID entries. ``__repr__`` is JSON-pretty and ``_repr_html_`` is a single-row HTML table.

    :param entry: A single entry from ``Dictionary.apid``.

    :Example: Display a parameter!

    >>> d = Dictionary(...)
    >>> d.ingest_apid()
    >>> DictionaryApid(dictionary.apid[100])
    '''
    def _repr_html_(self):
        _body = dict_apid_row(self.entry)
        return dict_apid_table.format(body=_body)
    
dict_channel_table = '''
<table style="table-layout:fixed;text-align:left;"">
    <thead>
        <tr style="border-bottom: solid white 1px;">
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">ID</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">NAME</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">TYPE</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">MODULE/OPSCAT</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">DESCRIPTION</th>
        </tr>
    </thead>
    <tbody>
        {body}
    </tbody>
</table>
'''
def dict_channel_row(channel):
    _id = f'{channel["@abbreviation"]}<br>(mid={channel["measurement_id"]})'
    _type = f'{channel["@type"]}<br>({channel["@byte_length"]} bytes)'
    _moc = f'module={channel["categories"]["module"]}<br>ops_category={channel["categories"]["ops_category"]}'
    return f'''
    <tr style="border-bottom: solid white 1px;">
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{_id}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{channel["@name"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{_type}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{_moc}</td>
        <td style="text-align:left;border:1pt solid #ccc;">{channel["description"]}</td>
    </tr>
    '''  
class DictionaryChannel(DictionaryRepr):
    '''Special class for displaying Dictionary channel entries. ``__repr__`` is JSON-pretty and ``_repr_html_`` is a single-row HTML table.

    :param entry: A single entry from ``Dictionary.channel``.

    :Example: Display a parameter!

    >>> d = Dictionary(...)
    >>> d.ingest_channel()
    >>> DictionaryChannel(d.channel['DDM-0012'])
    '''
    def _repr_html_(self):
        _body = dict_channel_row(self.entry)
        return dict_channel_table.format(body=_body)
    
dict_evr_table = '''
<table style="table-layout:fixed;text-align:left;"">
    <thead>
        <tr style="border-bottom: solid white 1px;">
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">ID</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">NAME</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">MODULE/OPSCAT</th>
            <th style="text-align:left;border-bottom:1pt solid black;font-size:8px;">MESSAGE FORMAT</th>
        </tr>
    </thead>
    <tbody>
        {body}
    </tbody>
</table>
'''
def dict_evr_row(evr):
    _moc = f'module={evr["categories"]["module"]}<br>ops_category={evr["categories"]["ops_category"]}'
    return f'''
    <tr style="border-bottom: solid white 1px;">
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{evr["@id"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{evr["@name"]}</td>
        <td style="text-align:left;white-space:nowrap;border:1pt solid #ccc;">{_moc}</td>
        <td style="text-align:left;border:1pt solid #ccc;"><pre>"{evr["format_message"]}"</pre><br>({evr["number_of_arguments"]} args)</td>
    </tr>
    '''  
class DictionaryEvr(DictionaryRepr):
    '''Special class for displaying Dictionary EVR entries. ``__repr__`` is JSON-pretty and ``_repr_html_`` is a single-row HTML table.

    :param entry: A single entry from ``Dictionary.evr``.

    :Example: Display an EVR!

    >>> d = Dictionary(...)
    >>> d.ingest_evr()
    >>> DictionaryEvr(d.evr['BC_MGR_EVR_BCRAM_TEST_FAILED'])
    '''
    def _repr_html_(self):
        _body = dict_evr_row(self.entry)
        return dict_evr_table.format(body=_body)


__SSE_DICTIONARY_LOCATION__ = '/dict/eurcsse/current/'

class SseDictionary:

    '''Manages the ingestion of SSE dictionaries.

    :param dictionary_path: The directory containing the XML dictionaries. Defaults to latest release in ``__DICTIONARY_LOCATION__`` "current".
    :type dictionary_path: ``str``
    :param ingest_all: Indicates that all dictionaries should be ingested. Defaults to ``False``.
    :type ingest_all: ``bool``
    :param log_level: Logging level per the ``logging`` module. Defaults to ``logging.WARNING``.
    :type log_level: ``logging`` level

    :Example: Use the latest:

    >>> D = SseDictionary()

    :Example: Give it your own path:

    >>> D = SseDictionary(dictionary_path='/dict/eurcsse/WSTS-9.3.2')
    
    :Example: Get all the dictionaries for the default release:

    >>> D = SseDictionary(ingest_all=True)
    >>> D.apid    # APID dictionary
    >>> D.channel # Channel dictionary
    >>> # ... etc.

    :Example: Only ingest, say, the APID dictionary:

    >>> D = SseDictionary()  # ingest_all defaults to False
    >>> d.ingest_apid()
    >>> d.apid               # the APID dictionary
    '''
    
    def __init__(self, dictionary_path=__SSE_DICTIONARY_LOCATION__, ingest_all=False, log_level=logging.WARNING):
        
        self.log = rich_logger(level=log_level, logger_name='Dictionary')
        
        dictionary_path = os.path.abspath(dictionary_path)
        if not os.path.exists(dictionary_path):
            raise DictionaryError(f'"{dictionary_path}" does not exist!')
        if not os.path.isdir(dictionary_path):
            raise DictionaryError(f'"{dictionary_path}" is not a directory!')
        self.dictionary_path = dictionary_path
        
        if ingest_all is True:
            self._ingest_all()
            
    def __repr__(self):
        return f'SseDictionary(dictionary_path="{self.dictionary_path}", apids={len(getattr(self, "apid",[]))}, channels={len(getattr(self, "channel",[]))}, commands={len(getattr(self, "command",[]))}, evrs={len(getattr(self, "evr",[]))})'

    def _repr_html_(self):
        return fancy_repr_html('SseDictionary', dict(dictionary_path=f'"{self.dictionary_path}"', apids=len(getattr(self, 'apid',[])), channels=len(getattr(self, 'channel',[])), commands=len(getattr(self, 'command',[])), evrs=len(getattr(self, 'evr',[])), ))
    
    def _read_xml(self, xml_fname):
        # sandboxes sometimes have these "global_ac" names. try both.
        p = os.path.join(self.dictionary_path, xml_fname)
        if not os.path.exists(p):
            self.log.warning(f'"{p}" does not exist and no backup_xml_fname was provided!')
            return None
        with open(p, 'r') as _xml:
            _xml_read = _xml.read()
        return _xml_read
    
    def _ingest_all(self):
        self.ingest_apid()
        self.ingest_channel()
        self.ingest_command()
        self.ingest_evr()
        
    def ingest_apid(self):
        self.log.debug('Running ingest_apid...')
        apid_read = self._read_xml('apid.xml')
        if apid_read is None:
            self.apid = None
            return
        self.apid = { int(_['@number']):_ for _ in xmltodict.parse(apid_read)['ApidDictionary']['apid'] }
        
    def ingest_channel(self):
        self.log.debug('Running ingest_channel...')
        channel_read = self._read_xml('channel.xml')
        if channel_read is None:
            self.channel = None
            return
        self.channel = { _['@id']:_ for _ in xmltodict.parse(channel_read)['Channel-Dictionary']['channels']['channel'] }

    def ingest_command(self):
        self.log.debug('Running ingest_command...')
        command_read = self._read_xml('command.xml')
        if command_read is None:
            self.command = None
            return
        self.command = xmltodict.parse(command_read)['dictionary']['stem']
        
    def ingest_evr(self):
        self.log.debug('Running ingest_evr...')
        evr_read = self._read_xml('evr.xml')
        if evr_read is None:
            self.evr = None
            return
        self.evr = { _['evr']['@name']:_['evr'] for _ in xmltodict.parse(evr_read)['evrs']['packet'] }

def load_dictionary(version):
    '''Loads a cached pickle ``Dictionary`` object from ``__DICTIONARY_CACHE_LOCATION__``. If the specified version's cache/pickle does not exist, warns and returns ``None``. Spare me your Rick and Morty jokes.

    :param version: "Dot"-formatted FSW version, e.g. ``"EURC_R10_1_0_2"`` would be specified as ``"8.0.1.2"``.
    :type version: ``str``
    :return: ``Dictionary`` object, unpickled. 

    :Example: Use a previously cached ``Dictionary``:
    
    >>> D = load_dictionary('8.0.1.2')
    >>> D.version # hopefully "8.0.1.2"
    >>> D.apid    # the APID dictionary
    >>> ...
    '''
    
    _log = rich_logger(logger_name='load_dictionary')
    _log.warning('Stubbed, see issue #37.')
    return None

    f = os.path.join(__DICTIONARY_CACHE_LOCATION__, __CACHE_FILENAME_TEMPLATE__.format(version))
    if not os.path.exists(f):
        _log.warning(f'Dictionary pickle "{f}" for version "{version}" does not exist.')
        return None
    with open(f, 'rb') as rick_and_morty_joke:
        dictionary = pickle.load(rick_and_morty_joke)
    return dictionary

__DICTIONARY_RELEASE_ROOT__ = '/dict/eurc/'
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--output-dir', '-o', metavar='<directory>', default=__DICTIONARY_CACHE_LOCATION__,help=f'Specify where to place the cached dictionaries. Defaults to "{__DICTIONARY_CACHE_LOCATION__}".')
@click.option('--dict-dir', '-d', metavar='<directory>', default=__DICTIONARY_RELEASE_ROOT__,help=f'Specify where to find the dictionaries (the folder containing the XMLs). Defaults to "{__DICTIONARY_RELEASE_ROOT__}".')
def cache_dictionary(output_dir, dict_dir):
    
    """
    Caches dictionaries as pickles, per eurc_vnv.dictionary.Dictionary.
    """

    log = rich_logger(level=logging.INFO, logger_name='cache_dictionary')

    log.critical('cache_dictionary is stubbed, see issue #37.')
    sys.exit(0)

    log.info(f'Searching for dictionaries in "{dict_dir}"...')
    releases = glob.glob(os.path.join(dict_dir,'*'))
    if not releases:
        log.warning(f'--dict-dir="{dict_dir}" contains nothing.')

    # sort because cool
    releases.sort()

    # process each release
    log.info(f'Searching "{dict_dir}"...')
    for r in releases:
        # must be a directory that matches the pattern. "CFDP" is for <=R7.x; 
        # no material differences to non-CFDP dictionaries for our purposes here.
        m = re.search('^EURC(.*)$', os.path.basename(r))
        if os.path.isdir(r) and m and not r.endswith('CFDP'):
            path = m.group()
            log.info(f'Unpacking and caching "{path}"...')
            try:
                d = Dictionary(dictionary_path=r, ingest_all=True, cache=True, cache_to=output_dir)
            except Exception as e:
                log.critical(f'Could not unpack "{r}" due to error "{repr(e)}".')
        else:
            log.info(f'"{r}" is not a valid dictionary path. Skipping.')
