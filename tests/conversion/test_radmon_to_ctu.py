import os
import sys
from unittest.mock import patch
from fspa_scripts.conversions import radmon_to_ctu
from tests.test_helpers.path_utils import get_path_to_test_file


class TestRadmonToCTU:
    def test_radmon_to_ctu(self, tmpdir):
        with patch.object(
            sys,
            "argv",
            [
                "conversions/radmon_to_ctu.py",
                "--infile",
                get_path_to_test_file("test_radmon.csv"),
                "--outdir",
                str(tmpdir),
            ],
        ):
            radmon_to_ctu.main()

            assert os.path.isfile(os.path.join(tmpdir, "output.csv"))
            with open(os.path.join(tmpdir, "output.csv"), "r") as infile:
                csv_string = infile.read()
                assert csv_string == (
                    "name,scet,value,ert,sclk,vcid\n"
                    "STATE_1,2025-286T00:00:51.682434,11,2023-164T21:58:56.468,498009654.68243,1\n"
                    "STATE_2,2025-286T00:00:51.682434,12,2023-164T21:58:56.468,498009654.68243,1\n"
                    "STATE_3,2025-286T00:00:51.682434,13,2023-164T21:58:56.468,498009654.68243,1\n"
                    "STATE_1,2025-286T00:01:50.150955,15,2023-164T21:58:56.468,498009713.15096,1\n"
                    "STATE_2,2025-286T00:01:50.150955,16,2023-164T21:58:56.468,498009713.15096,1\n"
                    "STATE_3,2025-286T00:01:50.150955,17,2023-164T21:58:56.468,498009713.15096,1\n"
                    "STATE_1,2025-286T00:02:48.526351,18,2023-164T21:58:56.468,498009771.52635,1\n"
                    "STATE_2,2025-286T00:02:48.526351,19,2023-164T21:58:56.468,498009771.52635,1\n"
                    "STATE_3,2025-286T00:02:48.526351,20,2023-164T21:58:56.468,498009771.52635,1\n"
                    "STATE_1,2025-286T00:03:51.806915,21,2023-164T21:58:56.468,498009834.80692,1\n"
                    "STATE_2,2025-286T00:03:51.806915,22,2023-164T21:58:56.468,498009834.80692,1\n"
                    "STATE_3,2025-286T00:03:51.806915,23,2023-164T21:58:56.468,498009834.80692,1\n"
                    "STATE_1,2025-286T00:04:50.182785,24,2023-164T21:58:56.468,498009893.18279,1\n"
                    "STATE_2,2025-286T00:04:50.182785,25,2023-164T21:58:56.468,498009893.18279,1\n"
                    "STATE_3,2025-286T00:04:50.182785,26,2023-164T21:58:56.468,498009893.18279,1\n"
                )
