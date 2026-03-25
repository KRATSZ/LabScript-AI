import sys
import os
import uuid
import json
import time
from pathlib import Path

# be sure to cd to Protocols repo top level

pd_json = {}


def generate_uuid():
    return str(uuid.uuid1())


def get_now_ms():
    return round(time.time()*1000)


# def get_category(folder):
    # readme_data_path = 'protoBuilds' + '/' + folder + '/README.json'
    # with open(readme_data_path) as readme_data_file:
    #     readme_data = json.load(readme_data_file)
    #     return(readme_data['categories'])


def get_initial_setup():
    pass


def map_pipette_to_tiprack(pipette_type):
    map = {
        '10': '10',
        '20': '20',
        '50': '300',
        '300': '300',
        '1000': '1000'
    }
    pipette_capacity = pipette_type.split('_')[0][1:]
    rack_name = f'opentrons/opentrons_96_tiprack_{map[pipette_capacity]}ul/1'
    return(rack_name)


def create_designer_application(pipettes, labware):
    labware_location_update = {
        id: labware[id]['slot']
        for id in [key for key in labware.keys()]
    }
    pipette_location_update = {
        id: pipettes[id]['mount']
        for id in [key for key in pipettes.keys()]
    }
    pipette_tiprack_assignments = {
        id: map_pipette_to_tiprack(pipettes[id]['name'])
        for id in [key for key in pipettes.keys()]
    }

    designer_app = {
        'name': 'opentrons/protocol-designer',
        'version': '5.2.6',
        'data': {
            '_internalAppBuildDate': 'Mon, 26 Apr 2021 18:42:28 GMT',
            'defaultValues': {
                'aspirate_mmFromBottom': 1,
                'dispense_mmFromBottom': 0.5,
                'touchTip_mmFromTop': -1,
                'blowout_mmFromTop': 0
            },
            'pipetteTiprackAssignments': pipette_tiprack_assignments,
            'dismissedWarnings': {
                'form': {},
                'timeline': {}
            },
            'ingredients': {},
            'ingredLocations': {},
            'savedStepForms': {
                '__INITIAL_DECK_SETUP_STEP__': {
                    "stepType": "manualIntervention",
                    "id": "__INITIAL_DECK_SETUP_STEP__",
                    'labwareLocationUpdate': labware_location_update,
                    'pipetteLocationUpdate': pipette_location_update,
                    'moduleLocationUpdate': {}
                }
            },
            'orderedStepIds': []
        }
    }
    return designer_app


def get_pipettes(protobuilds_data):
    pipettes = {
        generate_uuid(): pipette
        for pipette in protobuilds_data['instruments']
    }
    return pipettes


def get_labware(labware):
    pass


def create_pd_json(folder):
    protobuilds_folder = 'protobuilds/' + folder
    for file in os.listdir(protobuilds_folder):
        if '.py.json' in file:
            protobuilds_file = protobuilds_folder + '/' + file
            with open(protobuilds_file) as pb_file:
                protobuilds_data = json.load(pb_file)

    # labware
    custom_labware = protobuilds_data['custom_labware_defs']
    custom_loadnames = [lw['parameters']['loadName'] for lw in custom_labware]
    standard_labware = []
    opentrons_lw_path = 'ot2monorepoClone/shared-data/labware/definitions/2/'
    for lw in protobuilds_data['labware']:
        lw_loadname = lw['type']
        if lw_loadname not in custom_loadnames:
            standard_lw_path = opentrons_lw_path + lw_loadname + '/1.json'
            with open(standard_lw_path) as lw_file:
                lw_json = json.load(lw_file)
                standard_labware.append(lw_json)

    all_labware_defs = custom_labware + standard_labware
    all_labware_dict = {}
    for lw in all_labware_defs:
        load_name = lw['parameters']['loadName']
        full_labware_name = '/'.join([lw['namespace'], load_name, '1'])
        if load_name == 'opentrons_1_trash_1100ml_fixed':
            id = 'trashId'
        else:
            id = None
        all_labware_dict[load_name] = {
                'fullname': full_labware_name,
                'definition': lw,
                'id': id,
        }

    labware = {}
    for lw in protobuilds_data['labware']:
        load_name = lw['type']
        slot = lw['slot']
        display_name = lw['name']

        corr_id_lw = all_labware_dict[load_name]
        if not corr_id_lw['id']:
            id = f'{generate_uuid()}:{corr_id_lw["fullname"]}'
        else:
            id = corr_id_lw['id']
        labware[id] = {
            'slot': slot,
            'displayName': display_name,
            'definitionId': corr_id_lw['fullname']
        }

    labware_definitions = {}
    for lw in all_labware_dict.values():
        labware_definitions[lw['fullname']] = lw['definition']

    protobuilds_metadata = protobuilds_data['metadata']
    now = get_now_ms()
    # categories = get_category(folder)
    # category = [key for key in categories.keys()][0]
    # subcategory = categories[category][0]

    if 'protocolName' in protobuilds_metadata.keys():
        name = protobuilds_metadata['protocolName']
    elif 'title' in protobuilds_metadata.keys():
        name = protobuilds_metadata['title']
    else:
        name = ' '

    if 'author' in protobuilds_metadata.keys():
        author = protobuilds_metadata['author']
    else:
        author = ' '
    metadata = {
        'protocolName': name,
        'author': author,
        'description': '',
        'created': now,
        'lastModified': now,
        'category': None,
        'subcategory': None,
        'tags': []
    }

    pipettes = get_pipettes(protobuilds_data)

    designer_application = create_designer_application(pipettes, labware)
    robot = {"model": "OT-2 Standard"}

    pd_data = {
        'metadata': metadata,
        'designerApplication': designer_application,
        'robot': robot,
        'pipettes': pipettes,
        'labware': labware,
        'labwareDefinitions': labware_definitions,
        'schemaVersion': 3,
        'commands': []
    }
    return pd_data


def write_file_to_protocol_folder(folder):
    protocol_folder = 'protocols/' + folder
    if 'supplements' not in os.listdir(protocol_folder):
        os.mkdir(protocol_folder + '/supplements')
    out_path = protocol_folder + '/supplements/pd.json'
    data = create_pd_json(folder)
    with open(out_path, 'w') as out_file:
        json.dump(data, out_file, indent=4)


if __name__ == '__main__':
    source_file_path = sys.argv[1]
    source_folder_path = str(Path(source_file_path).parent).split('/')[-1]
    write_file_to_protocol_folder(source_folder_path)
