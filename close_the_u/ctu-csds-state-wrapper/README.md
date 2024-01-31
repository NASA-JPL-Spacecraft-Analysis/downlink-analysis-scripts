# ctu-csds-state-wrapper
Python script for publishing CSV or JSON state data to Clipper State Data Store (CSDS)


# Installation Instructions
Inside the `ctu-csds-state-wrapper/` folder:
```shell
$ python -m venv .venv --upgrade-deps && source ./.venv/bin/activate
$ pip install -r requirements.txt
```

# Script Usage Instructions

#### Load States into Clipper State Data Store

CSV Example
```shell
$ python ctu_csds_states.py --action LOAD_STATES  --collection 'fsw-params' --input ./filename.csv
```

JSON Example
```shell
$ python ctu_csds_states.py --action LOAD_STATES --collection 'fsw-params' --input ./filename.json
```

---

#### Query States from Clipper State Data Store

CSV Example
```shell
$ python ctu_csds_states.py --action QUERY_STATES --collection 'fsw-params' --output CSV
```

JSON Example
```shell
$ python ctu_csds_states.py --action QUERY_STATES --collection 'fsw-params' --output JSON
```

---
#### Script Help Options
```
Arguments:
  -a ACTION, --action ACTION (required)
        the action to either query or load state for the CSDS
        (ex: LOAD_STATES or QUERY_STATES)

  -c COLLECTION, --collection COLLECTION (required)
        name of the collection in CSDS (ex: mast-fsw-params)

  -i INPUT, --input INPUT (required for LOAD_STATES action)
        relative path to the csv or json input file (ex: ./sample.csv)

  -o OUTPUT, --output OUTPUT (default: JSON)
        file format to write output response (ex: CSV or JSON)
```


