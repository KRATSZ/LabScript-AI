import os
import json
from pathlib import Path
from parse import markdown as parser
from traversals import PROTOCOLS_BUILD_DIR, PROTOCOL_DIR


def write_README_to_json(protocol_path):
    """
    Shallow scan through root returning the list of protocol
    dictionary items.
    """
    for proto_dir in Path(protocol_path).iterdir():
        if not proto_dir.is_dir():
            # maybe it's a .DS_Store or something
            print(f'DEBUG: Not a directory: "{proto_dir}"')
        else:
            root = proto_dir.name
            files = list(proto_dir.iterdir())
            readme_files = [f for f in files if f.name == 'README.md']
            if len(readme_files) >= 2:
                raise RuntimeError(
                    'Expected exactly 1 README.md, got ' +
                    f'{len(readme_files)} in {proto_dir}')

            build_path = Path(PROTOCOLS_BUILD_DIR) / root
            if not build_path.is_dir():
                os.mkdir(build_path)

            output_path = build_path / 'README.json'
            with open(output_path, 'w') as output_file:
                json.dump(
                    {**parser.parse(readme_files[0])}, output_file,
                    indent=4, sort_keys=True)


if __name__ == '__main__':
    write_README_to_json(PROTOCOL_DIR)
