import json
import os
import csv

protocols_path = 'protocols/'
all_fields = {}


def mine_fields():
    for folder in os.listdir(protocols_path):
        prtcl_path = f'{protocols_path}/{folder}'
        if os.path.isdir(prtcl_path):
            if 'fields.json' in os.listdir(prtcl_path):
                with open(f'{prtcl_path}/fields.json') as fields_file:
                    fields = json.load(fields_file)
                    for field in fields:
                        name = field['name'].lower()
                        if name not in all_fields:
                            all_fields[name] = 1
                        else:
                            all_fields[name] += 1

    out_path = 'data/data/fields.csv'
    with open(out_path, 'w') as out_file:
        field_writer = csv.writer(out_file)
        field_writer.writerows(
            [[key, val] for key, val in sorted(all_fields.items())])


if __name__ == '__main__':
    mine_fields()
