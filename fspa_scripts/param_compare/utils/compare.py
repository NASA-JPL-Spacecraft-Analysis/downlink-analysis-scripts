"""
File for converting parameter input formats into a pandas DataFrame. The 
DataFrames are used for processing data sets efficiently.
"""

import pandas as pd
from .constants import GROUP, COPY

###############################################################################
# COMPARE & MERGE PARAMETER SETS WITH USER INPUT
###############################################################################

def compare_parameters(df1, df2, verbose, intersect_only, diff_only):
    """Merge parameter sets based on arguments."""
    # Only return 'name' and 'value' from JSON input for non-verbose comparison
    if not verbose:
        df1 = df1[['name','value']]
        df2 = df2[['name','value']]

    # Merge parameter sets based on intersection
    merge_method = "inner" if intersect_only else "outer"
    df = pd.merge(df1, df2, how=merge_method, on=["name"], suffixes=("_1", "_2"))
    df['match'] = df['value_1'] == df['value_2']

    # Only return set of parameters that do not match
    if diff_only:
        df = df[df['match'] == False]
    
    return df

###############################################################################
# CREATE DATAFRAME FUNCTIONS
###############################################################################

def create_df_from_parasol(response):
    """Return pandas DataFrame from parasol query JSON data."""
    rows_list = []
    for module_name, module in response.items():
        for parameter_name, parameter in module[GROUP][COPY].items():
            rows_list.append({
                "name": parameter_name, 
                "value": parameter['non-volatile']['value'],
                "module": module_name,
                "group": GROUP,
                "copy": COPY,
                "evidence":parameter['non-volatile']['evidence'],
                "evidence_status": parameter['non-volatile']['evidence_status']
            })
    return pd.DataFrame(rows_list)

def create_df_from_param_json(data):
    """Return pandas DataFrame from param.json data."""
    return pd.json_normalize(data['parameter_file']['parameter_list'])