import os
import sys

from fspa_scripts.param_compare import param_compare



def test_param_compare_library_parasol(self):
    """Test parasol query returns data."""
    result = param_compare.compare(
        input1={
            'type': 'parasol',
            'host': 'eurcitis001',
            'session': 830,
            'scet': '2026-082T17:19:46',
            'vcid': 0,
            'env': 'dev'
        },
        input2={
            'type': 'parasol',
            'host': 'eurcitis001',
            'session': 830,
            'scet': '2026-082T17:19:46',
            'vcid': 0,
            'env': 'dev'
        },
    )
    # print(result)
    # 'type': 'param_json',
    # 'path': "/fspa_scripts/tests/data/260_param.json" 
    assert True

def test_param_compare_library(self):
    """Test parasol query returns data."""
    result = param_compare.compare(
        input1={
            'type': 'param_json',
            'path': '/Users/huffman/code/clipper/fspa-scripts/tests/param_compare/data/parm_json/012_success_active_only_30p_nvm.parm.json'
        },
        input2={
            'type': 'param_json',
            'path': '/Users/huffman/code/clipper/fspa-scripts/tests/param_compare/data/parm_json/017_success_active_only_260_nvm.parm.json'
        }
    )
    # print(result)
    assert True


def test_param_compare_library(self):
    """Test parasol query returns data."""
    result = param_compare.compare(
        input1={
            'type': 'csds',
            'collection_name': 'eurcits001-collection-690',
            'env': 'dev'
        },
        input2={
            'type': 'csds',
            'collection_name': 'eurcits001-collection-690',
            'env': 'dev'
        }
    )
    # print(result)
    assert True


