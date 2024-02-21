# dp100ocs
Python script for querying out Data Products, run vnv tools to convert command history and then push to OCS

# Installation Instructions
Need to be on a flight machine where chill tools and vnv librarires are setup(e.g. eurcits001)

Inside the `transpire` folder:
```shell
$ source /proj/europa/fs/tools/europa-fs-vnv/environment/.cshrc
$ activate-ec-ve
$ pip install -r requirements.txt

In case the vnv .cshrc file is not available there is a copy of it named ec_ve_cshrc
```

# Script Usage Instructions

#### Load Data Products into OCS

Query out data products for session and push to OCS
```shell
If not already autenticated with SSO, run `credss` and then:

$ python dp100ocs.py -K 620 -p 100

This should query out the data products using chill_get_products
Then it should parse the data product out using the eurc_vnv libraries
Then it should push the parsed data product into OCS

Sample url to view data prodcuts in browser:
https://dd.eurc-dev.jpl.nasa.gov/eurc-dev-general/transpire
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

