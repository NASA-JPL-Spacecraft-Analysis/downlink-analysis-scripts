import argparse


def process_simple_io_arguments():
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument(
        "--infile", type=argparse.FileType("r", encoding="UTF-8"), required=True
    )
    parser.add_argument("--outdir", default="./")
    return parser.parse_args()
