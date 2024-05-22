from io import StringIO

import argparse
import socket
import ocs
import ocs.exceptions
import json
import xmltodict
#import os
import sys
import subprocess

# todo, allow these to be passed in via commnad line, ENV, and a transpire_dps.config file
ocs_env = "dev" #default to dev if nothing passed in
ocs_configs = {
    "ccgds": {
        "ocs_endpoint_host": "ocs.ccgds.eurc.jpl.nasa.gov",
        "ocs_api": "/prod"
    },
    "dev": {
        "ocs_endpoint_host": "ocs.eurc-dev.jpl.nasa.gov",
        "ocs_api": "/dev"
    },
    "gdsit": {
        "ocs_endpoint_host": "ocs.gdsit.eurc.jpl.nasa.gov",
        "ocs_api": "/test"
    },
    "test": {
        "ocs_endpoint_host": "ocs.test.eurc.jpl.nasa.gov",
        "ocs_api": "/test"
    },
    "ops": {
        "ocs_endpoint_host": "ocs.ops.eurc.jpl.nasa.gov",
        "ocs_api": "/prod"
    },
}

class DpOcsPusherException(Exception):
    pass

#just an os system call to chill_get_products
def find_data_products(session=None, apid=None, cmd_path=None):
    print("Attempting to find data products")

    cmd = []
    if cmd_path:
        cmd.append(cmd_path)
    else:
        cmd.append("chill_get_products")

    if session:
        cmd.append("-K")
        cmd.append(session)

    if apid:
        cmd.append("-p")
        cmd.append(str(apid))
    print("running chill command {}".format(cmd))

    output = None
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()

        if err:
            output = err.decode()
            print('--Error--\n', err.decode())
            raise DpOcsPusherException("Error running chill_get_products: {}".format(output))
        else:
            output = out.decode()
            # print('--No errors--\n', out.decode())
    except FileNotFoundError as e:
        #if a hard command path was provided and we got nothing we should exit
        if cmd_path:
            raise DpOcsPusherException("Unable to execute chill_get_products command");
        else:
            # try this known location of chill_get_products in case the path got messed up
            default_cmd = "/ammos/ampcs/mpcs/eurc/current/bin/chill_get_products"
            print("Unable to find chill_get_products, attempting to use: {}".format(default_cmd))

            return find_data_products(session, apid, default_cmd)

    print("Parsing output for dat files")
    dps = []
    for line in output.splitlines():
        dps.append(parse_chill_csv_line(line))

    return dps

def parse_chill_csv_line(line):
    # sample csv line from chill_get_products(broken up on multiple lines for readability)
    # "Product","620","eurcits001","1","100",
    # "DP_CMD_COMMAND_HISTORY","2023-164T22:06:44.327","2025-286T00:00:00.06961","2023-164T22:06:42.762","0498009603.0696249",
    # "/really/long/path/to/dat/file/0100_0498009603-0073007-1.dat",
    # "0","498009603","73007","0","0",
    # "0","2138934958277980360","2320","3930033554","COMPLETE_CHECKSUM_PASS","1.000"

    csv = line.split(",")
    for i in range(0, len(csv)):
        csv[i] = csv[i].replace("\"", "")

    chill_record = {
        "session": csv[1],
        "host": csv[2],
        "apid": csv[4],
        "dat_file": csv[10]
    }

    return chill_record

def build_ocs_client(venue):
    # SETUP OCS
    global ocs_configs
    config = ocs_configs

    if venue not in config:
        raise DpOcsPusherException("Unknown OCS venue {}".format(venue))

    # Instantiate ocs client
    client = ocs.client(ocs_endpoint_host=config[venue]['ocs_endpoint_host'],
                        ocs_api_stage=config[venue]['ocs_api'])

    return client


def push_to_ocs(filepath, ocs_package_name, ocs_path, ocs_filename, ocs_metadata):
    print("Pushing file with file {} to OCS at {}{}/{}".format(
        filepath, ocs_package_name, ocs_path, ocs_filename))

    local_object = filepath # this should be complete filepath to dat/emd file

    global ocs_env
    client = build_ocs_client(ocs_env)
    session_token = client.get_csso_session_token()  # Retrieve csso session token after logging into credss

    # describe_all_packages to find the package_id
    response = client.describe_all_packages(SessionToken=session_token)
    #print(json.dumps(response, indent=4))
    package_id = [item['package_id'] for item in response['data'] if item['name'] == ocs_package_name][0]

    object_type = 'eurc-idms-ampcs-dp'

    # response = client.index_local_object(
    #     PackageId=package_id,
    #     ObjectTypeName=object_type,
    #     OcsPath=ocs_path,
    #     OcsName=ocs_filename,
    #     Metadata=ocs_metadata,
    #     LocalObject=local_object,
    #     MimeType='application/json',
    #     SessionToken=session_token,
    #     Overwrite=True
    # )
    #
    # print('Successfully uploaded to OCS.  OCS dataset_id is: {}'.format(response['data']['dataset_id']))

def build_ocs_metadata_from_emd(emd_file):
    print("Building metadata from emd file {}".format(emd_file))

    with open(emd_file, 'r') as the_emd_file:
        read_emd = the_emd_file.read()

    # turn it into a Dict
    emd_dict = xmltodict.parse(read_emd)
    print("emd dict {}".format(json.dumps(emd_dict, indent=4)))

    session_info = emd_dict["mm-emd:EarthProductMetadata"]["mm-emd:SessionInformation"]
    session_id =    session_info["mpcs:SessionId"]["mpcs:Number"]
    session_name =  session_info["mpcs:SessionId"]["mpcs:Name"]
    fsw_dict_ver =  session_info["mpcs:SessionId"]["mpcs:FswDictionaryVersion"]
    fsw_dict_dir =  session_info["mpcs:SessionId"]["mpcs:FswDictionaryDir"]

    venue_type =    session_info["mpcs:Venue"]["mpcs:VenueType"]
    host =          session_info["mpcs:Venue"]["mpcs:Host"]
    user =          session_info["mpcs:Venue"]["mpcs:User"]

    output_dir =    session_info["mpcs:OutputDirectory"]

    product_metadata = emd_dict["mm-emd:EarthProductMetadata"]["mm-emd:ProductMetadata"]
    scid =          int(product_metadata["mm-emd:Scid"])
    vcid =          int(product_metadata["mm-emd:Vcid"])
    apid =          int(product_metadata["mm-emd:Apid"])
    product_type =  product_metadata["mm-emd:ProductType"]
    ground_status = product_metadata["mm-emd:GroundStatus"]
    seq_id =        product_metadata["mm-emd:SequenceId"]
    seq_ver =       product_metadata["mm-emd:SequenceVersion"]
    cmd_num =       int(product_metadata["mm-emd:CommandNumber"])
    dvt_coarse =    int(product_metadata["mm-emd:DvtCoarse"])
    dvt_fine =      int(product_metadata["mm-emd:DvtFine"])
    sclk_str =      product_metadata["mm-emd:FirstPartSclk"]
    chksum_expect = product_metadata["mm-emd:ExpectedProductChecksum"]
    chksum_actual = product_metadata["mm-emd:ActualProductChecksum"]
    size_expect =   product_metadata["mm-emd:ExpectedProductFileSize"]
    size_actual =   product_metadata["mm-emd:ActualProductFileSize"]
    cfdp_id =       product_metadata["mm-emd:CfdpTransactionSequenceNumber"]
    dat_filepath =  product_metadata["mm-emd:DataFilePath"]
    emd_filepath =  dat_filepath.replace(".dat", ".emd")

    # sclk_str_split = sclk_str.split(".")
    # sclk_coarse = int(sclk_str_split[0])
    # sclk_fine = 0
    #
    # if len(sclk_str_split) == 2:
    #     sclk_fine = int(sclk_str_split[1])

    #ocs is picky and wants us to have 5 decimal precision in our milliseconds
    scet_str_split = product_metadata["mm-emd:FirstPartScet"].split(".")
    scet_millis = "00000"
    if len(scet_str_split) == 2:
        scet_millis = scet_str_split[1]
        scet_millis = scet_millis.ljust(5, '0') # zero pad in case it is shorter than 5 millis
        scet_millis = scet_millis[:5] #grab first 5 incase it is longer than 5 millis

    scet = "{}.{}".format(scet_str_split[0], scet_millis)

    ert_str_split = product_metadata["mm-emd:FirstPartErt"].split(".")
    ert_millis = "00000"
    if len(ert_str_split) == 2:
        ert_millis = ert_str_split[1]
        ert_millis = ert_millis.ljust(5, '0') # zero pad in case it is shorter than 5 millis
        ert_millis = ert_millis[:5] #grab first 5 incase it is longer than 5 millis

    ert = "{}.{}".format(ert_str_split[0], ert_millis)



    meta = {
        "session_id": session_id,
        "session_name": session_name,
        "session_fsw_dictionary_dir": fsw_dict_dir,
        "session_fsw_dictionary_version": fsw_dict_ver,
        "session_venue_type": venue_type,
        # "session_test_bed_name": None,
        "session_user": user,
        "session_host": host,
        "session_output_directory": output_dir,
        "creation_time": None,
        "scid": scid,
        "apid": apid,
        "product_type": product_type,
        "vcid": vcid,
        "ground_status": ground_status,
        "fsw_version": None,
        "product_tag": None,
        "data_file_name": None,
        "onboard_creation_time": None,
        "onboard_Creation_time_str": None,
        "sequence_id": seq_id,
        "sequence_version": seq_ver,
        "command_number": cmd_num,
        "dvt_coarse": dvt_coarse,
        "dvt_fine": dvt_fine,
        "sclk": None,
        "sclk_str": sclk_str,
        "scet": None,
        "ert": None,
        "expected_product_checksum": chksum_expect,
        "actual_product_checksum": chksum_actual,
        "expected_product_filesize": size_expect,
        "actual_product_filesize": size_actual,
        "cfdp_transaction_sequence_id": cfdp_id,
        "absolute_path": dat_filepath,
        "absolute_path_emd": emd_filepath,
        "source": dat_filepath,
        "file_type": None,
        "sha256": None, #are these sha and md5 manually calculated on upload?
        "sha256_dat": None,
        "sha256_emd": None,
        "md5": None,
        "md5_dat": None,
        "md5_emd": None,
        "dvt": None,
        "dat_filename": dat_filepath.split("/")[-1],
        "emd_filename": emd_file.split("/")[-1],
        "dat_extension": "dat",
        "emd_extension": "emd"
    }

    print("metadata is {}".format(json.dumps(meta, indent=4)))
    return meta

def query_ocs(expression, sort="sclk_str:desc", max_results=1):
    print("Querying OCS with search expression: {}".format(expression))
    global ocs_env
    client = build_ocs_client(ocs_env)

    session_token = client.get_csso_session_token()  # Retrieve csso session token after logging into credss

    # try:
    if True:
        found_records = client.search_by_expression(expression, session_token,
                                                             Sort=[sort], MaxResults=max_results)
        print(json.dumps(found_records, indent=4))
        return found_records
    # except ocs.exceptions.HTTPError as e:
    #     print(e)
    #
    #     if 'HTTP Error: 403' in e.args[0]:
    #         raise Exception('User is forbidden from accessing OCS resources.')
    #     elif 'HTTP Error: 401' in e.args[0]:
    #         raise Exception('User is not authorized to access OCS resources.')
    # except ocs.exceptions.RequestError as r:
    #     print(r)

def query_from_ocs(session_host, session_id, ocs_package):
    # expression = "ocs_type_name:{} AND ocs_name:{} AND scet:[{} TO {}]".format(
    #     ocs_type, pcfg_name, start_scet, end_scet)
    #expression = "ocs_name: {}".format(filename)
    ocs_type = "eurc-idms-ampcs-dp"

    #searching with type name by itself works...
    #expression = "ocs_type_name: {}".format(ocs_type)

    #queries below with session host and id do not work...blah
    #expression = "ocs_type_name: {} AND session_host={}".format(ocs_type, session_host)
    expression = "ocs_type_name: {} AND session_host: {} AND session_id: {} AND ocs_package_name: {}".format(
        ocs_type, session_host, session_id, ocs_package)

    query_ocs(expression)

def main():
    hostname = socket.gethostname()
    print("Start of transpire_process_dps script, running on host {}".format(hostname))

    parser = argparse.ArgumentParser(description='Query Data Products from a session and publish json format to OCS')
    parser.add_argument('-p', '--apid', default=301, help='apid to query(only supports apid 301 atm)')
    parser.add_argument('-K', '--session', help='session number to query on')
    parser.add_argument('-t', '--ocs_path', default='/parasol', help='The ocs directory to publish to')
    parser.add_argument('-g', '--ocs_package', default='eurc-dev-fspa', help='The ocs package to publish as')
    parser.add_argument('-c', '--ocs_env', default='dev', help='the ocs environment to use(e.g. dev, test, prod, etc')
    #todo add ocs_endpoint_host as a command line arg as well
    parser.add_argument('-d', '--dat_file', default=None, help='file path to dat file to parse')
    parser.add_argument('-e', '--emd_file', default=None, help='file path to emd file to parse')

    args = parser.parse_args()

    session = args.session
    apid = args.apid
    ocs_path = args.ocs_path
    ocs_package_name = args.ocs_package
    dat_file = args.dat_file
    emd_file = args.emd_file

    #todo: read these out of cli, env, and a config file, see comment at top near these global variables
    global ocs_env
    global ocs_configs

    if args.ocs_env not in ocs_configs:
        print("Unknown OCS env {}, defaulting to {}".format(args.ocs_env, ocs_env))
    else:
        ocs_env = args.ocs_env
        print("Using ocs env: {}".format(ocs_env))

    if not session and (not dat_file or not emd_file):
        print("You must pass in [ session(-K) ] OR a [ dat_file(-d) and emd_file(-e) ]")
        sys.exit()

    # we need to find the dat and emd files using chill and the session + apid
    if session and apid:
        data_products = find_data_products(session=session, apid=apid)
    # we were given a dat file and emd file, just shove it in the data_products list for the loop below to handle
    else:
        # data_products from find_data_products() also has extra things like session, host, and apid, but we do not
        # really need those anymore as those are actually provided in the EMD file
        # we just need to shove the 'dat_file' key in there
        data_products = [
            {
                'dat_file': dat_file
            }
        ]

    if not data_products:
        print("No data products found")
        sys.exit()

    for dp in data_products:
        dat_file = dp['dat_file']

        emd_file = dat_file.replace(".dat", ".emd")
        metadata = build_ocs_metadata_from_emd(emd_file)

        filename = dp['dat_file'].split("/")[-1]
        #filename = "{}-{}-{}".format(metadata['session_host'], metadata['session_id'], filename)

        # write files to ocs

        push_to_ocs(filepath=dat_file,
                    ocs_package_name=ocs_package_name,
                    ocs_path=ocs_path,
                    ocs_filename=filename,
                    ocs_metadata=metadata)

        push_to_ocs(filepath=emd_file,
                    ocs_package_name=ocs_package_name,
                    ocs_path=ocs_path,
                    ocs_filename=filename,
                    ocs_metadata=metadata)

        # try to query out the data we just pushed to make sure it got in
        # print("Verifying data made it to OCS")
        # query_from_ocs(metadata['session_host'], metadata['session_id'], ocs_package)
        #

if __name__ == "__main__":
    main()
