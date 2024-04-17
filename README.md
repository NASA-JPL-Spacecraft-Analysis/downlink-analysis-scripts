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

### parasol

#### publish_fsw_params.py

Query Parasol fsw parameters and publish them to states in the Clipper State Data Store

```shell
$ python publish_fsw_params.py --host eurcits001 --session 578 --collection 'eurcits001-collection' --scet 2026-109T07:44:10 --vcid 0
```

### param_compare

#### param_compare.py

Compare parasol, param.json, seqgen_fincon.json, or CSDS parameters and return results in human-readable output (Excel report or JSON).

NOTE: Requires cam-login. Run `cam-login` in your terminal before trying the param_compare script.

##### CLI Schema

```
input types: {parasol, param_json, seqgen_fincon, csds}

required arguments:

parasol:
    host        Session host on parasol (ex: eurcits001)
    session     Session id on parasol (ex: 830)
    scet        A SCET formatted time for parasol query 1 (ex: 2023-136T22:08:51.038)
    vcid        VCID 0 or 32 (ex: 0)
    env         Venue for retrieving parameter values (ex: dev)

param_json:
    path        Path to json file.

seqgen_fincon:
    path        Path to json file.

csds:
    collection  Collection Name for state data store (ex: 'eurcits001-collection-690')
    env         Venue for retrieving parameter values (ex: dev)
```

##### Examples

```shell
# parasol to parasol
$ python param_compare.py --input1 parasol eurcits001 830 2026-082T17:19:46 0 dev --input2 parasol eurcits001 830 2026-082T17:19:46 0 dev

# parasol to param.json
$ python param_compare.py --input1 parasol eurcits001 830 2026-082T17:19:46 0 dev --input2 param_json "./data/parm_json/017_success_active_only_260_nvm.parm.json"

# param.json to seqgen_fincon.json
$ python param_compare.py --input1 param_json "./data/parm_json/017_success_active_only_260_nvm.parm.json" --input2 seqgen_fincon "./data/seqgen_fincon/Active_Falseactive_params.json"

# csds to parasol
$ python param_compare.py --input1 csds "eurcits001-collection-690" dev --input2 parasol eurcits001 830 2026-082T17:19:46 0 dev
```

Additional flags:

- `--output` Path to desired output location.
- `--verbose` Includes all data from compared files in output.
- `--intersect-only` Only output parameters that exist in both inputs.
- `--diff-only` Only output parameters that do not match.
- `--to-json` Output results in JSON at desired output path.

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
