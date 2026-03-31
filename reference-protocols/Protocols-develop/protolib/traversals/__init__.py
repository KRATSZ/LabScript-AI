import os
import sys

PROTOCOL_DIR = 'protocols'
RELEASES_DIR = 'releases'
PROTOCOLS_BUILD_DIR = 'protoBuilds'
ARGS = sys.argv[2::]


def prepare_dirs(
    protocols_build_dir, protocols_release_dir, library_input_path
):

    try:
        os.mkdir(protocols_release_dir)
    except FileExistsError:
        pass

    try:
        os.mkdir(protocols_build_dir)
    except FileExistsError:
        pass

    if not os.path.exists(library_input_path):
        raise SystemExit('Protocol Library path does not exist')


def search_directory(protocol_dir, file_type):
    # Generalized search function to recursively move through a directory tree.
    # This function will only return a generator object with the specified
    # file type.
    for root, dirs, files in os.walk(protocol_dir):
        ignore = False
        file_list = []
        for f in files:
            if '.ignore' in f:
                ignore = True
            if not f.startswith('test_'):
                if file_type and file_type in f:
                    file_list.append(f)
                if not file_type:
                    file_list.append(f)

        if root != protocol_dir:
            if not ignore:
                yield {'root': root, 'dirs': dirs, 'files': file_list}
        else:
            continue


prepare_dirs(PROTOCOLS_BUILD_DIR, RELEASES_DIR, PROTOCOL_DIR)
