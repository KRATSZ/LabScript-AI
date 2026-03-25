import glob
# import logging
import os
import shutil
import json
from pathlib import Path
from traversals import PROTOCOLS_BUILD_DIR, PROTOCOL_DIR
# file handler keys
OT_1_PROTOCOL = 'OT 1 protocol'
OT_2_PROTOCOL = 'OT 2 protocol'
DESCRIPTION = 'description'

file_handlers = {
    DESCRIPTION: '*.md',
    OT_1_PROTOCOL: '*ot1.py',
    OT_2_PROTOCOL: '*ot2*.py'
}


def get_file_content(protocol_root, filename):
    with open(os.path.join(protocol_root, filename), 'r') as appfile:
        return appfile.read().strip()


def generate_metadata(root, _path, file_names):
    """
    root: the single protocol dir we're parsing now
    _path: the path to the root protocols dir (probably is 'protocols')
    file_names: array of strings representing all file names
    in the single protocol dir
    """
    path = Path(_path)

    return {
        'slug': root,
        'path': str(path / root),
        'flags': {
            'feature': '.feature' in file_names,
            'skip-tests': '.notests' in file_names,
            'hide-from-search': '.hide-from-search' in file_names,
            'embedded-app':
                get_file_content(path / root, '.embedded-app')
                if '.embedded-app' in file_names else False
        },
        'files': {
            file_type: [
                Path(f).name
                for f in glob.glob(os.path.join(path, root, file_glob))]
            for file_type, file_glob in file_handlers.items()
        }
    }


def get_errors(file_data):
    msg = []
    protocol_keys = [
        OT_1_PROTOCOL,
        OT_2_PROTOCOL
    ]

    protocol_file_counts = [
        len(file_data.get(key, []))
        for key in protocol_keys
    ]
    print(file_data.get(OT_1_PROTOCOL))
    print(file_data.get(OT_2_PROTOCOL))
    if sum(protocol_file_counts) == 0:
        raise ValueError('Found 0 protocol files required at least 1')

    else:
        for key, num_files in zip(protocol_keys, protocol_file_counts):
            if num_files > 1:
                raise ValueError('Found {} {} files required \
                                  no more than 1'.format(num_files, key))

    description_files = len(file_data.get(DESCRIPTION, []))
    if description_files != 1:
        raise ValueError('Found {} description files required 1'.format(
            description_files))

    return msg


def get_status(file_data):
    errors = None
    if not file_data['flags']['embedded-app']:
        errors = get_errors(file_data['files'])
    if not sum(file_data['files'].values(), []):
        return 'empty'
    return 'error' if errors else 'ok'


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


def delete_empty_folder(folder):
    protocols_folder = f'{PROTOCOL_DIR}/{folder}'
    protobuilds_folder = f'{PROTOCOLS_BUILD_DIR}/{folder}'
    if check_empty(protocols_folder):
        shutil.rmtree(protocols_folder)
        if os.path.isdir(protobuilds_folder):
            shutil.rmtree(protobuilds_folder)
        print(f'Deleting {protocols_folder}, {protobuilds_folder} \
(no relevant files)')
        return True
    return False


def write_metadata_to_file(protocol_path):
    """
    Function to write metadata to the relative path
    'protocol_dir/metadata.json'.
    """
    for proto_dir in Path(protocol_path).iterdir():
        if not proto_dir.is_dir():
            # maybe it's a .DS_Store or something
            print(f'DEBUG: Not a directory: "{proto_dir}"')
        else:
            root = proto_dir.name
            file_names = [f.name for f in proto_dir.iterdir()]
            build_path = Path(PROTOCOLS_BUILD_DIR) / root
            empty = delete_empty_folder(root)
            if not empty:
                metadata_output_path = build_path / 'metadata.json'

                if not build_path.is_dir():
                    os.mkdir(build_path)

                metadata = generate_metadata(root, protocol_path, file_names)

                with open(metadata_output_path, 'w') as metadata_file:
                    json.dump(
                        {**metadata,
                         'status': get_status(metadata)},
                        metadata_file, indent=4, sort_keys=True)


if __name__ == '__main__':
    write_metadata_to_file(PROTOCOL_DIR)
