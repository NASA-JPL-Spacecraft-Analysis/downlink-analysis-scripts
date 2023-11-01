from eurc_vnv.command import Command
from io import StringIO

import argparse
import socket
import ocs
import json
import xmltodict
import os
import sys

class DpOcsPusherException(Exception):
    pass


def parse_command_dat(dat_file, dict_loc="/dict/eurc/current/"):
    cmd_util = Command(dict_loc)
    commands = cmd_util.extract_command_history(dat_file)

    for cmd in commands:
        cmd.pop('opcode', None)  # need to get rid of all the opcodes before pushing anything

    return commands

#just an os system call to chill_get_products
def find_data_products(session=None, apid=None, cmd_path=None):
    print("Attempting to find data products")

    if cmd_path:
        cmd = cmd_path
    else:
        cmd = "chill_get_products"

    if session:
        cmd += " -K {}".format(session)

    if apid:
        cmd += " -p {}".format(apid)

    # chill_get_products -K 620 -p 100
    print("Running command: {}".format(cmd))
    process = os.popen(cmd)
    output = process.read()
    process.close()

    #do some checks to see if we got valid output
    if "command not found" in output:
        #if a hard command path was provided and we got nothing we should exit
        if cmd_path:
            raise DpOcsPusherException("Unable to execute chill_get_products command");
        else:
            # try this known location of chill_get_products in case the path got messed up
            default_cmd = "/ammos/ampcs/mpcs/eurc/current/bin/chill_get_products"
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
    config = {
        "ccgds": {
            "ocs_endpoint_host": "ocs.ccgds.eurc.jpl.nasa.gov",
            "ocs_api": "/prod"
        },
        "dev": {
            "ocs_endpoint_host": "ocs.eurc-dev.jpl.nasa.gov",
            "ocs_api": "/dev"
        }
    }

    if venue not in config:
        raise DpOcsPusherException("Unknown OCS venue {}".format(venue))

    # Instantiate ocs client
    client = ocs.client(ocs_endpoint_host=config[venue]['ocs_endpoint_host'],
                        ocs_api_stage=config[venue]['ocs_api'])

    return client


def push_to_ocs(data, ocs_package_name, ocs_path, ocs_filename, ocs_metadata):
    print("Pushing file with data size {} to OCS at {}{}/{}".format(
        len(data), ocs_package_name, ocs_path, ocs_filename))

    #todo: add in logic to check if a file exists and if not cast into StringIO
    local_object = StringIO(data)

    client = build_ocs_client("dev")
    session_token = client.get_csso_session_token()  # Retrieve csso session token after logging into credss

    # describe_all_packages to find the package_id
    response = client.describe_all_packages(SessionToken=session_token)
    #print(json.dumps(response, indent=4))
    package_id = [item['package_id'] for item in response['data'] if item['name'] == ocs_package_name][0]

    #todo: create new object type
    object_type = 'eurc-fspa-dp-parsed'
    #object_type = 'eurc-idms-ampcs-dp'

    response = client.index_local_object(
        PackageId=package_id,
        ObjectTypeName=object_type,
        OcsPath=ocs_path,
        OcsName=ocs_filename,
        Metadata=ocs_metadata,
        LocalObject=local_object,
        MimeType='application/json',
        SessionToken=session_token,
        Overwrite=True
    )

    print('Successfully uploaded to OCS.  OCS dataset_id is: {}'.format(response['data']['dataset_id']))

def build_ocs_metadata_from_emd(emd_file):
    print("Building ocs metadata from emd file {}".format(emd_file))
    """
    Sample EMD converted json
    {
        "mm-emd:EarthProductMetadata": {
            "@xmlns:mpcs": "http://dsms.jpl.nasa.gov/mpcs",
            "@xmlns:mm-emd": "http://dsms.jpl.nasa.gov/mpcs_mm-core_emd",
            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "@xsi:schemaLocation": "http://dsms.jpl.nasa.gov/mpcs_mm-core_emd http://dsms.jpl.nasa.gov/mpcs/MM_Core_Session.xsd",
            "@EmdSchemaVersion": "CFDP-1",
            "mm-emd:SessionInformation": {
                "mpcs:SessionId": {
                    "mpcs:Number": "620",
                    "mpcs:Name": "ST1_AR13705_reproc",
                    "mpcs:FswDictionaryDir": "/dict",
                    "mpcs:FswDictionaryVersion": "EURC_R10_2_0_0"
                },
                "mpcs:Venue": {
                    "mpcs:VenueType": "TESTSET",
                    "mpcs:TestbedName": null,
                    "mpcs:User": "dan",
                    "mpcs:Host": "eurcits001"
                },
                "mpcs:OutputDirectory": "/ammos/ampcs/mpcs/eurc/current/test/2023/164/ampcs/eurcits001/dan_ST1_AR13705_reproc_2023_164T21_10_59_967"
            },
            "mm-emd:ProductMetadata": {
                "mm-emd:GroundCreationTime": "2023-164T22:06:44.327",
                "mm-emd:Scid": "159",
                "mm-emd:Apid": "100",
                "mm-emd:ProductType": "DP_CMD_COMMAND_HISTORY",
                "mm-emd:Vcid": "1",
                "mm-emd:GroundStatus": "COMPLETE_CHECKSUM_PASS",
                "mm-emd:DataFilePath": "/ammos/ampcs/mpcs/eurc/current/test/2023/164/ampcs/eurcits001/dan_ST1_AR13705_reproc_2023_164T21_10_59_967/products/0100/0100_0498009603-0073007-1.dat",
                "mm-emd:SequenceId": "0",
                "mm-emd:SequenceVersion": "0",
                "mm-emd:CommandNumber": "0",
                "mm-emd:DvtCoarse": "498009603",
                "mm-emd:DvtFine": "73007",
                "mm-emd:FirstPartSclk": "0498009603.06961",
                "mm-emd:FirstPartScet": "2025-286T00:00:00.06961",
                "mm-emd:FirstPartErt": "2023-164T22:06:42.753",
                "mm-emd:ExpectedProductChecksum": "-364933742",
                "mm-emd:ActualProductChecksum": "-364933742",
                "mm-emd:ExpectedProductFileSize": "2320",
                "mm-emd:ActualProductFileSize": "2320",
                "mm-emd:CfdpTransactionSequenceNumber": "2138934958277980360",
                "mm-emd:PartList": {
                    "@TotalReceived": "1",
                    "mm-emd:Part": {
                        "@Offset": "0",
                        "@Length": "2320",
                        "mm-emd:Sclk": "0498009603.06961",
                        "mm-emd:Scet": "2025-286T00:00:00.06961",
                        "mm-emd:Ert": "2023-164T22:06:42.753",
                        "mm-emd:SourcePacketSeqCount": "25"
                    }
                }
            }
        }
    }
    """
    with open(emd_file, 'r') as the_emd_file:
        read_emd = the_emd_file.read()

    # turn it into a Dict
    emd_dict = xmltodict.parse(read_emd)
    print("emd dict {}".format(json.dumps(emd_dict, indent=4)))
    session_info = emd_dict["mm-emd:EarthProductMetadata"]["mm-emd:SessionInformation"]

    session_id = session_info["mpcs:SessionId"]["mpcs:Number"]
    #venue = session_info["mpcs:Venue"]["mpcs:VenueType"]
    host = session_info["mpcs:Venue"]["mpcs:Host"]
    #user = session_info["mpcs:Venue"]["mpcs:User"]
    session_name = session_info["mpcs:SessionId"]["mpcs:Name"]
    fsw_ver = session_info["mpcs:SessionId"]["mpcs:FswDictionaryVersion"]

    sclk_str_split = session_info["mm-emd:ProductMetadata"]["mm-emd:FirstPartSclk"].split(".")
    sclk_coarse = int(sclk_str_split[0])
    sclk_fine = 0

    if len(sclk_str_split) == 2:
        sclk_fine = int(sclk_str_split[1])

    scet = session_info["mm-emd:ProductMetadata"]["mm-emd:FirstPartScet"]
    ert = session_info["mm-emd:ProductMetadata"]["mm-emd:FirstPartErt"]
    vcid = int(session_info["mm-emd:ProductMetadata"]["mm-emd:Vcid"])
    apid = int(session_info["mm-emd:ProductMetadata"]["mm-emd:Apid"])
    dat_file_name = session_info["mm-emd:ProductMetadata"]["mm-emd:DataFilePath"]

    # meta = {
    #     "session_id": session_id,
    #     "session_venue_type": venue,
    #     "session_testbed_name": host,
    #     "session_user": user
    # }

    meta = {
        "session_id": session_id,
        "session_host": host,
        "session_name": session_name,
        "session_fsw_dictionary_version": fsw_ver,
        "sclk_coarse": sclk_coarse,
        "sclk_fine": sclk_fine,
        "scet": scet,
        "ert": ert,
        "vcid": vcid,
        "apid": apid,
        "dat_file_name": dat_file_name
    }

    print("ocs metadata is {}".format(meta))
    return meta

def main():
    hostname = socket.gethostname()
    print("Start of dp100ocs script, running on host {}".format(hostname))

    parser = argparse.ArgumentParser(description='Query Data Products from a session and publish json format to OCS')
    parser.add_argument('-p', '--apid', default=100, help='apid to query(only supports apid 100 atm)')
    parser.add_argument('-K', '--session', required=True, help='session number to query on')
    parser.add_argument('-t', '--ocs_path', default='/playground/fhy-sandbox', help='The ocs directory to publish to')
    parser.add_argument('-g', '--ocs_package', default='eurc-dev-general', help='The ocs package to publish as')
    args = parser.parse_args()

    session = args.session
    apid = args.apid
    ocs_path = args.ocs_path
    ocs_package_name = args.ocs_package

    data_products = find_data_products(session=session, apid=apid)

    if not data_products:
        print("No data products found")
        sys.exit()

    for dp in data_products:
        #cmd_data = parse_command_dat("/home/fhy/0100_0498009603-0073007-1.dat")
        dat_file = dp['dat_file']
        print("Parsing data product for commands: {}".format(dat_file))
        cmd_data = parse_command_dat(dat_file)
        data = json.dumps(cmd_data, indent=4)

        emd_file = dat_file.replace(".dat", ".emd")
        metadata = build_ocs_metadata_from_emd(emd_file)

        filename = dp['dat_file'].split("/")[-1]
        filename = filename.replace(".dat", ".json")

        push_to_ocs(data=data,
                    ocs_package_name=ocs_package_name,
                    ocs_path=ocs_path,
                    ocs_filename=filename,
                    ocs_metadata=metadata)

if __name__ == "__main__":
    main()