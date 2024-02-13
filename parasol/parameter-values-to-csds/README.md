# parameter-values-to-csds
Python command line script for querying Parasol fsw parameters and publishing them to states in the Clipper State Data Store

# Setup Instructions
This script makes use of both the `parasol-py` library and the `close-the-u-.py` library.  These libraires are currently in active development to support Clipper.

# Installation Instructions
Inside the `parameter-values-to-csds` folder:
```shell
$ python -m venv .venv --upgrade-deps && source ./.venv/bin/activate
$ pip install -r requirements.txt
```

# Usage Instructions

1. Login using `cam-login` (https://github.jpl.nasa.gov/397/cam-login)
2. If needed add eurc-dev venue: `cam-login config --add eurc-dev eurcdevcam2 --port 8443`


```shell
$ python publish_fsw_params.py --host eurcits001 --session 578 --collection 'eurcits001-collection' --scet 2026-109T07:44:10 --vcid 0
```

```
Arguments:
  --host HOST           session host on parasol
                        (ex: eurcits001)

  --session SESSION     session id on parasol
                        (ex: 578)

  --scet SCET           scet formatted date
                        (ex: 2023-136T22:08:51.038)

  --collection COLLECTION
                        name of the state data store collection to publish data
                        (ex: eurcits001-578-collection)

  --vcid VCID           vcid 0 or 1
                        (ex: 0) (defult: 0)

  --env ENV             environment for retrieving parameter values and publishing data
                        (ex: dev) (defult: dev)
```


