import os
import sys
import json
from ocs.exceptions import HTTPError
from io import StringIO
import pytest
from unittest.mock import patch, call, MagicMock, Mock
from fspa_scripts.transpire import transpire_process_dps
from tests.test_helpers.path_utils import get_path_to_test_file, TEST_FILES_PATH
from tests.test_helpers.test_data.parsed_commands import EXPECTED_PARSED_COMMANDS

TEST_CHILL_LINE = '"Product","620","eurcits001","1","100","DP_CMD_COMMAND_HISTORY","2023-164T22:06:44.327","2025-286T00:00:00.06961","2023-164T22:06:42.762","0498009603.0696249","/really/long/path/to/dat/file/0100_0498009603-0073007-1.dat","0","498009603","73007","0","0","0","2138934958277980360","2320","3930033554","COMPLETE_CHECKSUM_PASS","1.000"'


class TestTranspireProcessDps:
    def test_parse_command_dat(self):
        commands = transpire_process_dps.parse_command_dat(
            get_path_to_test_file("test_dat.dat"),
            f"{TEST_FILES_PATH}/current",
        )
        assert commands == EXPECTED_PARSED_COMMANDS

    @patch("fspa_scripts.transpire.transpire_process_dps.os.popen", autospec=True)
    def test_find_data_products_cmd(self, mock_popen):
        transpire_process_dps.find_data_products()
        mock_popen.assert_called_with("chill_get_products")
        transpire_process_dps.find_data_products(cmd_path="/fake/path")
        mock_popen.assert_called_with("/fake/path")
        transpire_process_dps.find_data_products(session="711")
        mock_popen.assert_called_with("chill_get_products -K 711")
        transpire_process_dps.find_data_products(apid="100")
        mock_popen.assert_called_with("chill_get_products -p 100")
        transpire_process_dps.find_data_products(
            cmd_path="/fake/path", session="711", apid="100"
        )
        mock_popen.assert_called_with("/fake/path -K 711 -p 100")

    @patch("fspa_scripts.transpire.transpire_process_dps.os.popen", autospec=True)
    def test_find_data_products_default_cmd(self, mock_popen):
        with pytest.raises(transpire_process_dps.DpOcsPusherException) as e_info:
            mock_popen.return_value.read.return_value = "command not found"
            transpire_process_dps.find_data_products(cmd_path="/fake/path")
            assert (
                e_info.value.args[0] == "Unable to execute chill_get_products command"
            )

        mock_popen.return_value.read.side_effect = [
            "command not found",
            "",
        ]

        # test fallback to known location of chill_get_products
        with patch.object(
            transpire_process_dps,
            "find_data_products",
            wraps=transpire_process_dps.find_data_products,
        ) as wrapped_find_data_products:
            transpire_process_dps.find_data_products()
            assert wrapped_find_data_products.call_count == 2
            # first call, our call, was called with no arguments
            assert wrapped_find_data_products.call_args_list[0] == call()
            # recursive call should have been called with default cmd
            assert wrapped_find_data_products.call_args_list[1] == call(
                None, None, transpire_process_dps.DEFAULT_CMD
            )

    @patch("fspa_scripts.transpire.transpire_process_dps.os.popen", autospec=True)
    def test_find_data_products_parse_csv_lines(self, mock_popen):
        with patch.object(
            transpire_process_dps,
            "parse_chill_csv_line",
            wraps=transpire_process_dps.parse_chill_csv_line,
        ) as wrapped_parse_chill_csv_line:
            dps = transpire_process_dps.find_data_products()
            assert wrapped_parse_chill_csv_line.call_count == 0
            assert dps == []

            mock_popen.return_value.read.return_value = TEST_CHILL_LINE
            dps = transpire_process_dps.find_data_products()
            assert wrapped_parse_chill_csv_line.call_count == 1
            assert dps == [
                {
                    "apid": "100",
                    "dat_file": "/really/long/path/to/dat/file/0100_0498009603-0073007-1.dat",
                    "host": "eurcits001",
                    "session": "620",
                }
            ]

    @patch("fspa_scripts.transpire.transpire_process_dps.ocs.client", autospec=True)
    def test_build_ocs_client(self, mock_client):
        with pytest.raises(transpire_process_dps.DpOcsPusherException) as e_info:
            transpire_process_dps.build_ocs_client("blahblahblah")
            assert e_info.value.args[0] == "Unknown OCS venue blahblahblah"

        transpire_process_dps.build_ocs_client("ccgds")
        mock_client.assert_called_with(
            ocs_endpoint_host="ocs.ccgds.eurc.jpl.nasa.gov", ocs_api_stage="/prod"
        )

        transpire_process_dps.build_ocs_client("dev")
        mock_client.assert_called_with(
            ocs_endpoint_host="ocs.eurc-dev.jpl.nasa.gov", ocs_api_stage="/dev"
        )

    @patch("fspa_scripts.transpire.transpire_process_dps.StringIO", autospec=True)
    @patch("fspa_scripts.transpire.transpire_process_dps.ocs.client", autospec=True)
    def test_push_to_ocs(self, mock_client, mock_stringio):
        fake_client = MagicMock()
        mock_client.return_value = fake_client
        fake_client.describe_all_packages.return_value = {
            "data": [
                {"package_id": 1, "name": "test_package"},
                {"package_id": 2, "name": "other_package"},
                {"package_id": 3, "name": "test_package"},
            ]
        }
        fake_client.index_local_object.return_value = {"data": {"dataset_id": 4}}
        fake_client.get_csso_session_token.return_value = "mytoken"
        mock_stringio.return_value = StringIO("data")

        transpire_process_dps.push_to_ocs(
            "data",
            "test_package",
            "/test/path",
            "test_file.txt",
            {"key": "value"},
        )

        fake_client.index_local_object.assert_called_with(
            PackageId=1,
            ObjectTypeName="eurc-fspa-dp-parsed",
            OcsPath="/test/path",
            OcsName="test_file.txt",
            Metadata={"key": "value"},
            LocalObject=mock_stringio.return_value,
            MimeType="application/json",
            SessionToken="mytoken",
            Overwrite=True,
        )

    def test_build_ocs_metadata_from_emd(self):
        assert transpire_process_dps.build_ocs_metadata_from_emd(
            f"{os.getcwd()}/tests/test_helpers/test_files/test_dat.emd"
        ) == {
            "session_id": "620",
            "session_host": "eurcits001",
            "session_name": "ST1_AR13705_reproc",
            "session_fsw_dictionary_version": "EURC_R10_2_0_0",
            "sclk_coarse": 498009603,
            "sclk_fine": 6961,
            "scet": "2025-286T00:00:00.06961",
            "ert": "2023-164T22:06:42.75300",
            "vcid": 1,
            "apid": 100,
            "dat_file_name": "/ammos/ampcs/mpcs/eurc/current/test/2023/164/ampcs/eurcits001/dan_ST1_AR13705_reproc_2023_164T21_10_59_967/products/0100/0100_0498009603-0073007-1.dat",
        }

    @patch("fspa_scripts.transpire.transpire_process_dps.ocs.client", autospec=True)
    def test_query_ocs(self, mock_client):
        fake_client = MagicMock()
        mock_client.return_value = fake_client
        fake_client.get_csso_session_token.return_value = "mytoken"
        fake_client.search_by_expression.return_value = [
            "record 1",
            "record 2",
            "record 3",
        ]

        assert transpire_process_dps.query_ocs("test expression") == [
            "record 1",
            "record 2",
            "record 3",
        ]
        fake_client.search_by_expression.assert_called_with(
            "test expression", "mytoken", Sort=["scet:desc"], MaxResults=1
        )

        fake_client.search_by_expression.side_effect = Mock(
            side_effect=HTTPError("HTTP Error: 403")
        )
        with pytest.raises(Exception) as e_info:
            transpire_process_dps.query_ocs("test expression")
            assert (
                e_info.value.args[0]
                == "User is forbidden from accessing OCS resources."
            )

        fake_client.search_by_expression.side_effect = Mock(
            side_effect=HTTPError("HTTP Error: 401")
        )
        with pytest.raises(Exception) as e_info:
            transpire_process_dps.query_ocs("test expression")
            assert (
                e_info.value.args[0]
                == "User is not authorized to access OCS resources."
            )

    @patch("fspa_scripts.transpire.transpire_process_dps.query_ocs", autospec=True)
    def test_query_from_ocs(self, mock_query_ocs):
        transpire_process_dps.query_from_ocs("eurcits001", "690")
        mock_query_ocs.assert_called_with(
            "ocs_type_name: eurc-fspa-dp-parsed AND session_host: eurcits001 AND session_id: 690"
        )

    @patch(
        "fspa_scripts.transpire.transpire_process_dps.find_data_products", autospec=True
    )
    @patch(
        "fspa_scripts.transpire.transpire_process_dps.parse_command_dat", autospec=True
    )
    @patch(
        "fspa_scripts.transpire.transpire_process_dps.build_ocs_metadata_from_emd",
        autospec=True,
    )
    @patch("fspa_scripts.transpire.transpire_process_dps.push_to_ocs", autospec=True)
    @patch("fspa_scripts.transpire.transpire_process_dps.query_from_ocs", autospec=True)
    def test_main(
        self,
        mock_query_from_ocs,
        mock_push_to_ocs,
        mock_build_ocs_metadata_from_emd,
        mock_parse_command_dat,
        mock_find_data_products,
    ):
        mock_find_data_products.return_value = [
            {"dat_file": "path/to/dat/1.dat"},
            {"dat_file": "path/to/dat/2.dat"},
        ]
        mock_parse_command_dat.side_effect = [{"key": "val"}, []]
        mock_build_ocs_metadata_from_emd.side_effect = [
            {"session_host": "eurcits001", "session_id": "690"},
            {"session_host": "eurcits001", "session_id": "700"},
        ]

        with patch.object(
            sys,
            "argv",
            [
                "transpire/transpire_process_dps.py",
                "--apid",
                "60",
                "--session",
                "800",
                "--ocs_path",
                "test/ocs/path",
                "--ocs_package",
                "eurc-unit-test-fspa",
            ],
        ):
            transpire_process_dps.main()

            mock_find_data_products.assert_called_with(session="800", apid="60")

            assert mock_parse_command_dat.call_count == 2
            assert mock_parse_command_dat.call_args_list[0] == call("path/to/dat/1.dat")
            assert mock_parse_command_dat.call_args_list[1] == call("path/to/dat/2.dat")

            assert mock_build_ocs_metadata_from_emd.call_count == 2
            assert mock_build_ocs_metadata_from_emd.call_args_list[0] == call(
                "path/to/dat/1.emd"
            )
            assert mock_build_ocs_metadata_from_emd.call_args_list[1] == call(
                "path/to/dat/2.emd"
            )

            assert mock_push_to_ocs.call_count == 2
            assert mock_push_to_ocs.call_args_list[0] == call(
                data=json.dumps({"key": "val"}, indent=4),
                ocs_package_name="eurc-unit-test-fspa",
                ocs_path="test/ocs/path",
                ocs_filename="eurcits001-690-1.json",
                ocs_metadata={"session_host": "eurcits001", "session_id": "690"},
            )
            assert mock_push_to_ocs.call_args_list[1] == call(
                data=json.dumps([], indent=4),
                ocs_package_name="eurc-unit-test-fspa",
                ocs_path="test/ocs/path",
                ocs_filename="eurcits001-700-2.json",
                ocs_metadata={"session_host": "eurcits001", "session_id": "700"},
            )

            assert mock_query_from_ocs.call_count == 2
            assert mock_query_from_ocs.call_args_list[0] == call("eurcits001", "690")
            assert mock_query_from_ocs.call_args_list[1] == call("eurcits001", "700")
