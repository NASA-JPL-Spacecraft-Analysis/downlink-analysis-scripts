"""
Constants used in the parameter comparison script that shouldn't change based 
on any inputs. These are all currently related to parasol-py queries.
"""

# queries
PARASOL_PHASE = "cruise"
PARASOL_COPY = "COPY_0"

# CLI
INPUT_TYPES = ['parasol', 'param_json', 'seqgen_fincon', 'csds']
INPUT_TYPE_ARG_COUNTS = {
    'parasol': 6,
    'param_json': 1,
    'seqgen_fincon': 1,
    'csds': 2
}
