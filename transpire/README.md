# transpire_process_dps.py
Python script for querying out Data Products, run vnv tools to convert command history and then push to OCS

# Installation Instructions
Need to be on a flight machine where chill tools(chill_get_products), chronos, and fsw dictionaries exist

Inside the `transpire` folder:
# Script Usage Instructions

#### Load Data Products into OCS

Query out data products for session and push to OCS
```shell
If not already autenticated with SSO, run `credss` and then:

$ python transpire_process_dps.py -K 620 

This should query out the data products using chill_get_products
Then it should parse the data product out using the eurc_vnv libraries
Then it should push the parsed data product into OCS

Sample url to view data prodcuts in browser:
https://dd.eurc-dev.jpl.nasa.gov/eurc-dev-general/transpire
```

Parse a dat file + emd file and write the json to disk
```
python transpire_process_dps.py -d 0100_0498009603-0073007-1.dat -e 0100_0498009603-0073007-1.emd -o ./output_files
```

---
#### Script Help Options
```
  -h, --help            show this help message and exit
  -p APID, --apid APID  apid to query(only supports apid 100 atm)
  -K SESSION, --session SESSION
                        session number to query on
  -t OCS_PATH, --ocs_path OCS_PATH
                        The ocs directory to publish to
  -g OCS_PACKAGE, --ocs_package OCS_PACKAGE
                        The ocs package to publish as
  -d DAT_FILE, --dat_file DAT_FILE
                        file path to dat file to parse
  -e EMD_FILE, --emd_file EMD_FILE
                        file path to emd file to parse
  -o OUTPUT, --output OUTPUT
                        Location to write json files OR 'ocs'(default) to push to ocs


```

