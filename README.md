# fspa-scripts
Repo for scripts to be delivered through the GDS.

## Modules
### aerie
TODO
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
* Python 3.8+
* pip

## Setup
* `make setup`

## Lint
* `make format`

## Test
* `make test`

## Build
* `make build`

## Install
* `pip install dist/eurc-gds-fspa-scripts-<version>.tar.gz`
