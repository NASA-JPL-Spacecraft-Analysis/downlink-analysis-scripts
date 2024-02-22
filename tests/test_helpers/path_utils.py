import os

TEST_FILES_PATH = f"{os.getcwd()}/tests/test_helpers/test_files"


def get_path_to_test_file(filename):
    return f"{TEST_FILES_PATH}/{filename}"
