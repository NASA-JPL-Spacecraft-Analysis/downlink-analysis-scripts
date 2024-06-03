# fspa-scripts

Repo for scripts to be delivered through the GDS.

## Modules

### ctu_merlin

#### merlin_to_sm.py

Connect state definitions and resource timelines from Merlin to the State Manager and State Data Store

#### merlin_to_ctu_tools.py

Connect state definitions and resource timelines from Merlin to the State Manager and State Data Store

### close_the_u

#### ctu_csds_states.py

Publish CSV or JSON state data to Clipper State Data Store (CSDS)

```shell
python ctu_csds_states.py --action LOAD_STATES  --collection 'fsw-params' --input ./filename.csv
```

### conversions

#### chill_to_ctu.py

Converts a chill .csv output to CTU .csv input

#### radmon_to_ctu.py

Converts a RadMon .csv output to CTU .csv input

#### param_ioncons_to_ctu.py

Converts and uploads a SEQGEN fincon .json file's output parameters to CTU.

```
Arguments:

-t          Type of file input (default: seqgen_fincon)
-i          Input file path
-c          CDSS collection to insert parameters
--scet      A SCET formatted time to insert parameters (ex: 2023-136T22:08:51.038)
--env       Venue for retrieving parameter values (ex: dev)
--vol       CSDS volatile values (options: 'VOLATILE' or 'NON-VOLATILE') (default: VOLATILE)
```

##### Examples

```shell
$ python3 param_incons_to_ctu.py -t seqgen_fincon -i /path/to/seqgen_fincon/vm_10.3.0.0.json -c param_incon_1 --scet 2025-001T00:00:00 --env dev --vol VOLATILE
```

### parasol

#### publish_fsw_params.py

Query Parasol fsw parameters and publish them to states in the Clipper State Data Store

```shell
$ python publish_fsw_params.py --host eurcits001 --session 578 --collection 'eurcits001-collection' --scet 2026-109T07:44:10 --vcid 0
```

### param_compare

Compare parasol, param.json, seqgen_fincon.json, or CSDS parameters and return results in human-readable output (Excel report or JSON).

NOTE: Requires CSSO or cam-login. Run `credss` for CSSO, or `cam-login` in your terminal before trying the param_history script.

#### Input Schemas

```
input types: {parasol, param_json, seqgen_fincon, csds}

required arguments:

parasol:
    host        Session host on parasol (ex: eurcits001)
    session     Session id on parasol (ex: 830)
    scet        A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)
    vcid        VCID 0 or 32 (ex: 0)
    volatility  Use parasol volatile values (options: 'vol' or 'nvm')
    env         Venue for retrieving parameter values (ex: dev)

param_json:
    path        Path to json file.

seqgen_fincon:
    path        Path to json file.

csds:
    collection  Collection Name for state data store (ex: 'eurcits001-collection-690')
    env         Venue for retrieving parameter values (ex: dev)
```

#### CLI

Enter `param_compare -h` for help details.

##### Examples

After building the fspa-scripts libraries in the root directory with `pip install .` and running `make setup`, you should be able to run the script without prefixing `python` or adding the `.py` extension.

```shell
# parasol to parasol
$ param_compare --input1 parasol eurcits001 830 2026-082T17:19:46 0 nvm dev --input2 parasol eurcits001 830 2026-082T17:19:46 0 nvm dev

# parasol to param.json
$ param_compare --input1 parasol eurcits001 830 2026-082T17:19:46 0 nvm dev --input2 param_json "./data/parm_json/017_success_active_only_260_nvm.parm.json"

# param.json to seqgen_fincon.json
$ param_compare --input1 param_json "./data/parm_json/017_success_active_only_260_nvm.parm.json" --input2 seqgen_fincon "./data/seqgen_fincon/Active_Falseactive_params.json"

# csds to parasol
$ param_compare --input1 csds "eurcits001-collection-690" dev --input2 parasol eurcits001 830 2026-082T17:19:46 0 nvm dev
```

Additional flags:

- `--output` Path to desired output location.
- `--verbose` Includes all data from compared files in output.
- `--intersect-only` Only output parameters that exist in both inputs.
- `--diff-only` Only output parameters that do not match.
- `--to-json` Output results in JSON at desired output path.
- `--debug` Log param_compare processing information to console.
- `--auth-type` Authenticate with 'csso' (Parasol with Chillax) or 'cam' (Parasol with MCWS) (default: csso)

#### param_compare library

See below for examples.

1. Make sure library is built and installed with `pip install .` from the fspa-scripts root directory.
2. Import the `compare` function from `from fspa_scripts.param_compare.param_compare import compare`.
3. Call `compare` with codes similar to the below example.

`compare` returns a JSON list of results by default, with option to write results to xlsx or json file like the CLI script.

##### Examples

```python
from fspa_scripts.param_compare.param_compare import compare

# input types: 'parasol', 'csds', 'param_json', or 'seqgen_fincon'
# should be written as objects with their respective arguments

response = compare(
    input1={
        'type': 'parasol', # input example for parasol
        'host': 'eurcits001',
        'session': 830,
        'scet': '2026-082T17:19:46',
        'vcid': 0,
        'volatility': 'nvm',
        'env': 'dev'
    },
    input2={
        'type'='param_json',  # input example for param_json
        'path'='/path/to/param_json.json',
    },
    verbose = True,
    diff_only = True,
    intersect_only = True,
    return_type = 'xlsx', # optional file to write results
    output = '/my/output/folder', # optional file path to write results
    debug = True,
    auth_type = 'csso'
)

# parasol-parasol basic example
response = compare(input1={'type': 'parasol','host': 'eurcits001','session': 830,'scet': '2026-082T17:19:46','vcid': 0,'volatility': 'nvm','env': 'dev'}, input2={'type': 'parasol','host': 'eurcits001','session': 830,'scet': '2026-082T17:19:46','vcid': 0,'volatility': 'nvm','env': 'dev'})
```

### param_history

Compare parameter history from CSDS or Parasol and view a human-readable output (XLSX or JSON).

NOTE: Requires CSSO or cam-login. Run `credss` for CSSO, or `cam-login` in your terminal before trying the param_history script.

#### Input Schemas

```
input types: {parasol, csds}

required arguments:

parasol:
    host        Session host on parasol (ex: eurcits001)
    session     Session id on parasol (ex: 830)
    start_time  A SCET formatted start time for parasol history (ex: 2023-136T22:08:51.038)
    end_time    A SCET formatted end time for parasol history (ex: 2023-136T22:08:51.038)
    vcid        VCID 0 or 32 (ex: 0)
    volatility  Use parasol volatile values (options: 'vol' or 'nvm')
    env         Venue for retrieving parameter values (ex: dev)

csds:
    collection  Collection Name for state data store (ex: 'eurcits001-collection-690')
    env         Venue for retrieving parameter values (ex: dev)
```

#### CLI

Enter `param_history -h` for help details.

##### Examples

After building the fspa-scripts libraries in the root directory with `pip install .` and running `make setup`, you should be able to run the script without prefixing `python` or adding the `.py` extension.

```shell
# parasol to parasol
$ param_history --input parasol eurcits001 831 2024-001T00:00:00 2026-001T00:00:00 0 vol dev

# parasol to param.json
$ param_history --input csds fsw-params-eurcits001-844 dev
```

Additional flags:

- `--output` Path to desired output location.
- `--verbose` Include all data from query in output. NOTE: Only applies to 'list' format.
- `--format` Format parameter output as 'matrix' or 'list' (default: 'matrix')
- `--intersect-only` Only output parameters that exist in every timestamp in parameter history.
- `--change-only` Only output parameters that changed in given history.
- `--end-value` Only output parameters that are the 'same' or 'different' (default: 'all').
- `--to-json` Output history as JSON.
- `--debug` Log param_history processing information to console.
- `--auth-type` Authenticate with 'csso' (Parasol with Chillax) or 'cam' (Parasol with MCWS) (default: csso)

### transpire

#### transpire_process_dps.py

Query Data Products, run vnv tools to convert command history and then push to OCS

##### Installation Instructions

Need to be on a flight machine where chill tools and vnv librarires are setup (e.g. eurcits001)

Inside the `transpire` folder:

```shell
$ source /proj/europa/fs/tools/europa-fs-vnv/environment/.cshrc
$ activate-ec-ve
$ pip install -r requirements.txt
```

In case the vnv .cshrc file is not available there is a copy of it named ec_ve_cshrc

##### Load Data Products into OCS

Query out data products for session and push to OCS
If not already autenticated with SSO, run `credss` and then:

```shell
$ python transpire_process_dps.py -K 620
```

This should query out the data products using chill_get_products
Then it should parse the data product out using the eurc_vnv libraries
Then it should push the parsed data product into OCS

Sample url to view data prodcuts in browser:
https://dd.eurc-dev.jpl.nasa.gov/eurc-dev-general/transpire

## Prerequisites

- Python 3.8+
- pip

## Setup

- `make setup`

## Lint

- `make format`

## Test

- `make test`

## Build

- `make build`

## Install

- `pip install dist/eurc-gds-fspa-scripts-<version>.tar.gz`
