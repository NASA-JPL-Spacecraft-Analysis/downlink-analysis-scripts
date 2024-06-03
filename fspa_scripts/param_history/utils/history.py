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


def get_status(row):
    """Determine the status of a parameter."""
    return 'CHANGE'

###############################################################################
# COMPARE & MERGE PARAMETER SETS WITH USER INPUT
###############################################################################
def generate_history_matrix(df, intersect_only, end_value, change_only):
    """Create parameter history matrix with query."""
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


def generate_history_list(df, intersect_only, end_value, change_only, verbose):
    """Create parameter history list with query."""
    logging.info(f"Parameter history entries to process: {len(df.index)}")
    
    # apply verbose
    if not verbose:
        df = df[['name', 'scet', 'value']]

    # order by parameter name and scet
    df = df.sort_values(by=['name', 'scet'], ascending=[True, True])

    # set all returned values as 'CHANGE' by default
    # df['status'] = 'CHANGE'
    
    # print(df.loc[df.groupby(('name')).scet.idxmax()])

    # logging.info(f"Calculating status for parameters...")
    # param_tracker = set()
    # for index, row in df.iterrows():
    #     name = row['name']
    #     if name not in param_tracker:
    #         param_tracker.add(name)
    #         df.at[name, 'status'] = 'INITIAL'

    # for name, group in param_groups:
    #     first_scet = group['scet'].min()
    #     last_scet = group['scet'].max()
    #     print(name, first_scet, last_scet)
        # df.loc[df.loc[(df['name'] == name) & (df['scet'] == first_scet)], 'status'] = 'INITIAL'
        # df.loc[df.loc[(df['name'] == name) & (df['scet'] == last_scet)], 'status'] = 'FINAL'
    
    # print(df)

    # df['status'] = df.apply(get_status, axis=1)
    # replace first scet time as 'INITIAL'
    # param_mins = df.groupby(by=('name'))['scet'].min()
    
    # df.loc['scet' == pg_min, 'status'] = "INITIAL"
    # df.loc[df['scet'].str.contains('us'), 'status'] = "FINAL"
    # df['status'] = 

    # replace last scet time as 'FINAL'
    # param_maxs = df.groupby(by=('name'))['scet'].max()

    # replace microseconds with nanoseconds value
    # df.loc[df[pg_max], 'status'] = "FINAL"


    # print('SCET MIN\n', pg_min, 'SCET MAX\n', pg_max)

    # define how to merge parameters between scet times with argument
    # logging.info(f"Merging {param_groups.ngroups} 'scet' groups on parameter name...")
    # for param, group in param_groups:
    #     # print(scet, group.value_counts())
    
    # # # Filter for parameters that changed
    # if change_only:
    #     df = df[df['change'] == True]
    #     logging.info(f"Parameter count (after applying 'change_only' flag): {len(df.index)}")

    # # # Filter for 'same' or 'different' end values
    # if end_value == 'same':
    #     df = df[df['end value'] == 'SAME']
    #     logging.info(f"Parameter count (after applying 'end_value' flag): {len(df.index)}")

    # if end_value == 'different':
    #     df = df[df['end value'] == 'DIFFERENT']
    #     logging.info(f"Parameter count (after applying 'end_value' flag): {len(df.index)}")

    # logging.info(f"Parameter count (after processing): {len(df.index)}")
    return df