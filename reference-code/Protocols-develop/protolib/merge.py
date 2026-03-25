import os
import json
import zipfile
from protolib.traversals import RELEASES_DIR, search_directory
from collections import defaultdict
from datetime import datetime


def zip_file(input_file):
    deploy_path = os.path.join(RELEASES_DIR, 'deploy')
    if not os.path.exists(deploy_path):
        os.mkdir(deploy_path)
    output_file = os.path.join(
        deploy_path, 'PL-data-{}.zip'.format(
            datetime.now().strftime("%Y-%m-%d_%H.%M")))
    with zipfile.ZipFile(output_file, 'w') as zf:
        zf.write(input_file, 'output.json')


def append_to_output(categories, protocols):
    release_path = os.path.join(RELEASES_DIR, 'output.json')
    with open(release_path, 'w') as final_file:
        data = {'categories': categories, 'protocols': protocols}
        json.dump(data, final_file)
    zip_file(release_path)


def serialize_set(categories):
    return {key: list(value) for key, value in categories.items()}


def add_categories(data, metadata, categories, root):
    new_cat = data['categories']
    is_hidden = metadata.get('flags', {}).get('hide-from-search', False)
    if is_hidden:
        return
    for key, value in new_cat.items():
        if value:
            categories[key].add(value[-1])
        else:
            categories[key].add(root.split('/')[-1])


def merge_protocols(path):
    # Create generator object of protocol object(s) found
    # in the /protocols directory
    protocols = []
    categories = defaultdict(set)
    for build_dir in search_directory(path, None):
        root = build_dir['root']
        # Inside a given protocol directory from the releases/builds dir
        # Metadata blob
        with open(os.path.join(root, 'metadata.json'), 'r') as meta:
            metadata = json.load(meta)
            status = metadata['status']
            file_order = metadata['files']

        # README Blob
        with open(os.path.join(root, 'README.json'), 'r') as md:
            md_data = json.load(md)
            add_categories(md_data, metadata, categories, root)

        # Protocol blob
        metadata['protocols'] = {'OT 1 protocol': [], 'OT 2 protocol': []}

        for ot1 in file_order['OT 1 protocol']:
            with open(os.path.join(root, '{}.json'.format(ot1)), 'r') as proto:
                proto_data = json.load(proto)
            metadata['protocols']['OT 1 protocol'].append(proto_data)
        for ot2 in file_order['OT 2 protocol']:
            with open(os.path.join(root, '{}.json'.format(ot2)), 'r') as proto:
                proto_data = json.load(proto)
            metadata['protocols']['OT 2 protocol'].append(proto_data)

        if status != 'empty':
            for key, value in md_data.items():
                metadata[key] = value
            protocols.append(metadata)
        else:
            pass

    updated_categories = serialize_set(categories)
    append_to_output(updated_categories, protocols)
