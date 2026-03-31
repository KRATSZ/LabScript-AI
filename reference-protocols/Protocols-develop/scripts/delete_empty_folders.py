import os
import sys
from pathlib import Path


def check_py(files):
    for file in files:
        if 'ot2.apiv2.py' in file:
            return True
    return False


def check_README(files):
    for file in files:
        if file == 'README.md':
            return True
    return False


def check_fields(files):
    for file in files:
        if file == 'fields.json':
            return True
    return False


def check_empty(folder):
    files = os.listdir(folder)
    return not (check_py(files) or check_README(files) or check_fields(files))


def delete_empty_folders(folder):
    if check_empty(folder):
        os.rmdir(folder)


if __name__ == '__main__':
    source_file_path = sys.argv[1]
    source_folder_path = str(Path(source_file_path).parent)
    delete_empty_folders(source_folder_path)
