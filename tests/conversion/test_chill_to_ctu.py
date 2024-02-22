import os
import sys
from unittest.mock import patch
from fspa_scripts.conversions import chill_to_ctu
from tests.test_helpers.path_utils import get_path_to_test_file


class TestRadmonToCTU:
    def test_radmon_to_ctu(self, tmpdir):
        with patch.object(
            sys,
            "argv",
            [
                "conversions/chill_to_ctu.py",
                "--infile",
                get_path_to_test_file("test_chill.csv"),
                "--outdir",
                str(tmpdir),
            ],
        ):
            chill_to_ctu.main()

            assert os.path.isfile(os.path.join(tmpdir, "output.csv"))
            with open(os.path.join(tmpdir, "output.csv"), "r") as infile:
                csv_string = infile.read()
                assert csv_string == (
                    "name,scet,value,type\n"
                    "UPL-0009,2020-001T12:01:00,1,predicted\n"
                    "UPL-0009,2020-001T12:02:00,2,predicted\n"
                    "UPL-0009,2020-001T12:03:00,3,predicted\n"
                    "UPL-0009,2020-001T12:04:00,4,predicted\n"
                    "UPL-0009,2020-001T12:05:00,5,predicted\n"
                )
