# dp100ocs
Python script for querying out Data Products, run vnv tools to convert command history and then push to OCS

# Installation Instructions
Need to be on a flight machine where chill tools and vnv librarires are setup

Inside the `transpire-dps` folder:
```shell
$ source /proj/europa/fs/tools/europa-fs-vnv/environment/.cshrc
$ activate-ec-ve
$ pip install -r requirements.

In case the vnv .cshrc file is not available there is a copy of it named ec_ve_cshrc
```

# Script Usage Instructions

#### Load States into Clipper State Data Store

Query out data products for session and push to OCS
```shell
If not already autenticated with SSO, run `credss` and then:

$ python dp100ocs.py -K 620 -p 100

Sample url to view data prodcuts in browser:
https://dd.eurc-dev.jpl.nasa.gov/eurc-dev-general/playground/fhy-sandbox
```


---
#### Script Help Options
```
  -p APID, --apid APID  apid to query(only supports apid 100 atm)
  -K SESSION, --session SESSION
                        session number to query on
  -t OCS_PATH, --ocs_path OCS_PATH
                        The ocs directory to publish to
  -g OCS_PACKAGE, --ocs_package OCS_PACKAGE
                        The ocs package to publish as

```

