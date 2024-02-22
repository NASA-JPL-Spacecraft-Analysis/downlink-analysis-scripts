from eurc_vnv.command import Command
from io import StringIO

import argparse
import socket
import ocs
import ocs.exceptions
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
        cmd.pop(
            "opcode", None
        )  # need to get rid of all the opcodes before pushing anything

    return commands


# just an os system call to chill_get_products
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

    # do some checks to see if we got valid output
    if "command not found" in output:
        # if a hard command path was provided and we got nothing we should exit
        if cmd_path:
            raise DpOcsPusherException("Unable to execute chill_get_products command")
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
        csv[i] = csv[i].replace('"', "")

    chill_record = {
        "session": csv[1],
        "host": csv[2],
        "apid": csv[4],
        "dat_file": csv[10],
    }

    return chill_record


def build_ocs_client(venue):
    # SETUP OCS
    config = {
        "ccgds": {
            "ocs_endpoint_host": "ocs.ccgds.eurc.jpl.nasa.gov",
            "ocs_api": "/prod",
        },
        "dev": {"ocs_endpoint_host": "ocs.eurc-dev.jpl.nasa.gov", "ocs_api": "/dev"},
    }

    if venue not in config:
        raise DpOcsPusherException("Unknown OCS venue {}".format(venue))

    # Instantiate ocs client
    client = ocs.client(
        ocs_endpoint_host=config[venue]["ocs_endpoint_host"],
        ocs_api_stage=config[venue]["ocs_api"],
    )

    return client


def push_to_ocs(data, ocs_package_name, ocs_path, ocs_filename, ocs_metadata):
    print(
        "Pushing file with data size {} to OCS at {}{}/{}".format(
            len(data), ocs_package_name, ocs_path, ocs_filename
        )
    )

    # todo: add in logic to check if a file exists and if not cast into StringIO
    local_object = StringIO(data)

    client = build_ocs_client("dev")
    session_token = (
        client.get_csso_session_token()
    )  # Retrieve csso session token after logging into credss

    # describe_all_packages to find the package_id
    response = client.describe_all_packages(SessionToken=session_token)
    # print(json.dumps(response, indent=4))
    package_id = [
        item["package_id"]
        for item in response["data"]
        if item["name"] == ocs_package_name
    ][0]

    # todo: create new object type
    object_type = "eurc-fspa-dp-parsed"
    # object_type = 'eurc-idms-ampcs-dp'

    response = client.index_local_object(
        PackageId=package_id,
        ObjectTypeName=object_type,
        OcsPath=ocs_path,
        OcsName=ocs_filename,
        Metadata=ocs_metadata,
        LocalObject=local_object,
        MimeType="application/json",
        SessionToken=session_token,
        Overwrite=True,
    )

    print(
        "Successfully uploaded to OCS.  OCS dataset_id is: {}".format(
            response["data"]["dataset_id"]
        )
    )


def build_ocs_metadata_from_emd(emd_file):
    print("Building ocs metadata from emd file {}".format(emd_file))

    with open(emd_file, "r") as the_emd_file:
        read_emd = the_emd_file.read()

    # turn it into a Dict
    emd_dict = xmltodict.parse(read_emd)
    # print("emd dict {}".format(json.dumps(emd_dict, indent=4)))

    session_info = emd_dict["mm-emd:EarthProductMetadata"]["mm-emd:SessionInformation"]
    product_metadata = emd_dict["mm-emd:EarthProductMetadata"]["mm-emd:ProductMetadata"]
    session_id = session_info["mpcs:SessionId"]["mpcs:Number"]
    # venue = session_info["mpcs:Venue"]["mpcs:VenueType"]
    host = session_info["mpcs:Venue"]["mpcs:Host"]
    # user = session_info["mpcs:Venue"]["mpcs:User"]
    session_name = session_info["mpcs:SessionId"]["mpcs:Name"]
    fsw_ver = session_info["mpcs:SessionId"]["mpcs:FswDictionaryVersion"]

    sclk_str_split = product_metadata["mm-emd:FirstPartSclk"].split(".")
    sclk_coarse = int(sclk_str_split[0])
    sclk_fine = 0

    if len(sclk_str_split) == 2:
        sclk_fine = int(sclk_str_split[1])

    # ocs is picky and wants us to have 5 decimal precision in our milliseconds
    scet_str_split = product_metadata["mm-emd:FirstPartScet"].split(".")
    scet_millis = "00000"
    if len(scet_str_split) == 2:
        scet_millis = scet_str_split[1]
        scet_millis = scet_millis.ljust(
            5, "0"
        )  # zero pad in case it is shorter than 5 millis
        scet_millis = scet_millis[:5]  # grab first 5 incase it is longer than 5 millis

    scet = "{}.{}".format(scet_str_split[0], scet_millis)

    ert_str_split = product_metadata["mm-emd:FirstPartErt"].split(".")
    ert_millis = "00000"
    if len(ert_str_split) == 2:
        ert_millis = ert_str_split[1]
        ert_millis = ert_millis.ljust(
            5, "0"
        )  # zero pad in case it is shorter than 5 millis
        ert_millis = ert_millis[:5]  # grab first 5 incase it is longer than 5 millis

    ert = "{}.{}".format(ert_str_split[0], ert_millis)

    vcid = int(product_metadata["mm-emd:Vcid"])
    apid = int(product_metadata["mm-emd:Apid"])
    dat_file_name = product_metadata["mm-emd:DataFilePath"]

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
        "dat_file_name": dat_file_name,
    }

    print("ocs metadata is {}".format(json.dumps(meta, indent=4)))
    return meta


def query_ocs(expression, sort="scet:desc", max_results=1):
    print("Querying OCS with search expression: {}".format(expression))
    client = build_ocs_client("dev")

    session_token = (
        client.get_csso_session_token()
    )  # Retrieve csso session token after logging into credss

    try:
        found_records = client.search_by_expression(
            expression, session_token, Sort=[sort], MaxResults=max_results
        )
        print(json.dumps(found_records, indent=4))
        return found_records
    except ocs.exceptions.HTTPError as e:
        print(e)

        if "HTTP Error: 403" in e.args[0]:
            raise Exception("User is forbidden from accessing OCS resources.")
        elif "HTTP Error: 401" in e.args[0]:
            raise Exception("User is not authorized to access OCS resources.")
    except ocs.exceptions.RequestError as r:
        print(r)


def query_from_ocs(session_host, session_id):
    # expression = "ocs_type_name:{} AND ocs_name:{} AND scet:[{} TO {}]".format(
    #     ocs_type, pcfg_name, start_scet, end_scet)
    # expression = "ocs_name: {}".format(filename)
    ocs_type = "eurc-fspa-dp-parsed"

    # searching with type name by itself works...
    # expression = "ocs_type_name: {}".format(ocs_type)

    # queries below with session host and id do not work...blah
    # expression = "ocs_type_name: {} AND session_host={}".format(ocs_type, session_host)
    expression = "ocs_type_name: {} AND session_host: {} AND session_id: {}".format(
        ocs_type, session_host, session_id
    )

    query_ocs(expression)


def main():
    hostname = socket.gethostname()
    print("Start of transpire_process_dps script, running on host {}".format(hostname))

    parser = argparse.ArgumentParser(
        description="Query Data Products from a session and publish json format to OCS"
    )
    parser.add_argument(
        "-p", "--apid", default=100, help="apid to query(only supports apid 100 atm)"
    )
    parser.add_argument(
        "-K", "--session", required=True, help="session number to query on"
    )
    parser.add_argument(
        "-t", "--ocs_path", default="/transpire", help="The ocs directory to publish to"
    )
    parser.add_argument(
        "-g",
        "--ocs_package",
        default="eurc-dev-fspa",
        help="The ocs package to publish as",
    )
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
        # cmd_data = parse_command_dat("/home/fhy/0100_0498009603-0073007-1.dat")
        dat_file = dp["dat_file"]
        print("Parsing data product for commands: {}".format(dat_file))
        cmd_data = parse_command_dat(dat_file)
        data = json.dumps(cmd_data, indent=4)

        emd_file = dat_file.replace(".dat", ".emd")
        metadata = build_ocs_metadata_from_emd(emd_file)

        filename = dp["dat_file"].split("/")[-1]
        filename = filename.replace(".dat", ".json")
        filename = "{}-{}-{}".format(
            metadata["session_host"], metadata["session_id"], filename
        )

        push_to_ocs(
            data=data,
            ocs_package_name=ocs_package_name,
            ocs_path=ocs_path,
            ocs_filename=filename,
            ocs_metadata=metadata,
        )

        # try to query out the data we just pushed to make sure it got in
        query_from_ocs(metadata["session_host"], metadata["session_id"])


if __name__ == "__main__":
    main()
