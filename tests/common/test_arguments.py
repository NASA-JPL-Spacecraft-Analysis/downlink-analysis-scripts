import sys
from unittest.mock import patch
from fspa_scripts.common.arguments import process_simple_io_arguments
from tests.test_helpers.path_utils import get_path_to_test_file


class TestArguments:
    def test_process_simple_io_arguments(self):
        with patch.object(
            sys,
            "argv",
            [
                "conversions/radmon_to_ctu.py",
                "--infile",
                get_path_to_test_file("test_radmon.csv"),
            ],
        ):
            args = process_simple_io_arguments()
            assert args.infile.name == get_path_to_test_file("test_radmon.csv")
            assert args.outdir == "./"

        with patch.object(
            sys,
            "argv",
            [
                "conversions/radmon_to_ctu.py",
                "--infile",
                get_path_to_test_file("test_radmon.csv"),
                "--outdir",
                "test/special/dir",
            ],
        ):
            args = process_simple_io_arguments()
            assert args.infile.name == get_path_to_test_file("test_radmon.csv")
            assert args.outdir == "test/special/dir"
