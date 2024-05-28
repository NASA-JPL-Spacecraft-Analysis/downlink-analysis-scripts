"""
File for converting parameter inputs into a pandas DataFrame and comparing
parameters. Pandas DataFrames are used to process data efficiently.
"""

import re
import pandas as pd
import logging

###############################################################################
# HELPERS
###############################################################################
def detect_changes(row):
    """Detect if changes occurred in a parameter's history."""
    values = set(row.dropna().values.flatten().tolist()[1:]) # filter NaN values and remove parameter name from beginning
    return len(values) > 1 # true/false if more than one value exists

def detect_end_value(row):
    """Detect if last value matches first value in a parameter's history."""
    values = row.dropna().values.flatten().tolist()[1:-1] # filter NaN values, remove parameter name from beginning and 'changes' column from end
    return 'SAME' if values[0] == values[-1] else 'DIFFERENT' # true/false if first and last values match

###############################################################################
# COMPARE & MERGE PARAMETER SETS WITH USER INPUT
###############################################################################
def generate_history(df, verbose, format, intersect_only, end_value, change_only):
    """Merge parameter sets based on arguments."""
    logging.info(f"Parameter history entries to process: {len(df.index)}")
    
    # NOTE: verbose flag only applies for diff_option_3 (column format) not diff_option_1 (row format)
    # if not verbose:
    df = df[['name', 'scet', 'value']]

    # group by scet times
    scet_groups = df.groupby(('scet'))
    logging.info(f"""\n{scet_groups.size()}""")

    # define how to merge parameters between scet times with argument
    merge_method = "inner" if intersect_only else "outer"
    logging.info(f"Merging {scet_groups.ngroups} 'scet' groups on parameter name...")
    df = None
    last_scet = None
    for scet, group in scet_groups:
        # print(scet, group.value_counts())
        if df is None:
            df = group
            last_scet = scet
        else:
            df = pd.merge(df, group, how=merge_method, on=["name"], suffixes=(f'_{last_scet}', f'_{scet}'))
            last_scet = scet
    
    # drop unnecessary scet columns
    df = df[df.columns.drop(list(df.filter(regex='scet')))]

    # remove column name 'value' prefix for scet labels
    df = df.rename(columns=lambda x: re.sub('value_', '', x))
    logging.info(f"Detecting if changes occurred in history for each parameter...")

    # create 'change' column if not all columns in row are the same
    df['change'] = df.apply(detect_changes, axis=1)
    logging.info(f"Detecting if start and end values in history are the same for each parameter...")

    # create 'end value' column
    df['end value'] = df.apply(detect_end_value, axis=1)
    logging.info(f"Finished creating history dataframe.")

    # # Filter for parameters that changed
    if change_only:
        df = df[df['change'] == True]
        logging.info(f"Parameter count (after applying 'change_only' flag): {len(df.index)}")

    # # Filter for 'same' or 'different' end values
    if end_value == 'same':
        df = df[df['end value'] == 'SAME']
        logging.info(f"Parameter count (after applying 'end_value' flag): {len(df.index)}")

    if end_value == 'different':
        df = df[df['end value'] == 'DIFFERENT']
        logging.info(f"Parameter count (after applying 'end_value' flag): {len(df.index)}")

    logging.info(f"Parameter count (after processing): {len(df.index)}")
    return df