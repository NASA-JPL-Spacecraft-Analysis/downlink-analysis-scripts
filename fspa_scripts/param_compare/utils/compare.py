"""
File for converting parameter inputs into a pandas DataFrame and comparing
parameters. Pandas DataFrames are used to process data efficiently.
"""

import pandas as pd
import logging

###############################################################################
# COMPARE & MERGE PARAMETER SETS WITH USER INPUT
###############################################################################

def compare_parameters(df1, df2, verbose, intersect_only, diff_only):
    """Merge parameter sets based on arguments."""
    logging.info(f"Parameters in input1: {len(df1.index)}")
    logging.info(f"Parameters in input2: {len(df2.index)}")
    # Only return 'name' and 'value' from JSON input for non-verbose comparison
    if not verbose:
        df1 = df1[['name','value']]
        df2 = df2[['name','value']]

    # Merge parameter sets based on intersection
    merge_method = "inner" if intersect_only else "outer"
    df = pd.merge(df1, df2, how=merge_method, on=["name"], suffixes=("_1", "_2"))
    df['match'] = df['value_1'] == df['value_2']

    logging.info(f"Parameters (after optional merging with 'intersect_only' flag): {len(df.index)}")

    # Only return set of parameters that do not match
    if diff_only:
        df = df[df['match'] == False]

    logging.info(f"Parameters (after optional filtering with 'diff_only' flag): {len(df.index)}")
    
    return df