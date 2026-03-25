import json
import sys
from pathlib import Path

STANDARD_LABWARE_DIRECTORY = 'ot2monorepoClone/\
shared-data/labware/definitions/2'


def parse_title(data):

    metadata = data['metadata']
    title = None
    for key in ['protocolName', 'title']:
        if key in metadata.keys():
            title = data['metadata'][key]
    if title:
        title_lines = [f'# {title}']
    else:
        title_lines = None
    return title_lines


def parse_labware(data):

    def parse_custom_labware(data):
        if 'custom_labware_defs' in data.keys():
            custom_labware_list = []
            for custom_labware in data['custom_labware_defs']:
                display_text = custom_labware['metadata']['displayName']
                if 'brandId' in custom_labware['brand'] and \
                        custom_labware['brand']['brandId']:
                    brand_id = custom_labware['brand']['brandId']
                else:
                    brand_id = None
                lw = {
                    'display-text': display_text,
                    'brand-id': brand_id,
                    'link': None
                }
                custom_labware_list.append(lw)
            return custom_labware_list
        return []

    def parse_standard_labware(data):
        if 'custom_labware_defs' in data.keys():
            custom_labware_loadnames = [
                lw['parameters']['loadName']
                for lw in data['custom_labware_defs']]
        else:
            custom_labware_loadnames = []
        standard_loadnames = [
            lw['type'] for lw in data['labware']
            if lw['type'] not in custom_labware_loadnames
            and int(lw['slot']) != 12]  # don't include trash
        standard_labware_list = []
        for loadname in standard_loadnames:
            lw_definition_path = f'\
{STANDARD_LABWARE_DIRECTORY}/{loadname}/1.json'
            with open(lw_definition_path) as lw_definition_file:
                lw_data = json.load(lw_definition_file)
            display_name = lw_data['metadata']['displayName']
            if display_name not in [
                    lw['display-text'] for lw in standard_labware_list]:
                if 'links' in lw_data['brand'].keys():
                    if lw_data['brand']['links']:
                        link = lw_data['brand']['links'][0]
                    else:
                        link = None
                else:
                    link = None
                if 'brandId' in lw_data['brand'].keys():
                    if lw_data['brand']['brandId']:
                        brand_id = lw_data['brand']['brandId']
                    else:
                        brand_id = None
                else:
                    brand_id = None
                lw = {
                    'display-text': display_name,
                    'brand-id': brand_id,
                    'link': link
                }
                standard_labware_list.append(lw)
        return standard_labware_list

    def labware_data_to_lines(labware_data):
        if labware_data:
            labware_lines = ['### Labware']
            for labware in labware_data:
                display = f'{labware["display-text"]}'
                if labware['brand-id']:
                    display += f' #{labware["brand-id"][0]}'
                if labware['link']:
                    line = f'* [{display}]({labware["link"]})'
                else:
                    line = f'* {display}'
                labware_lines.append(line)
            return labware_lines
        return None

    custom_labware_data = parse_custom_labware(data)
    standard_labware_data = parse_standard_labware(data)
    all_labware_data = custom_labware_data + standard_labware_data

    return labware_data_to_lines(all_labware_data)


def parse_pipettes(data, readme_map):

    def pipettes_data_to_lines(pipette_data):
        if pipette_data:
            pipette_lines = ['### Pipettes']
            for pipette in pipette_data.values():
                line = f'* [{pipette["displayText"]}]({pipette["link"]})'
                pipette_lines.append(line)
            return pipette_lines
        return None

    pipette_list = list(set([pip['name'] for pip in data['instruments']]))
    pipette_data = {
        pip: readme_map['pipettes'][pip]
        for pip in pipette_list
    }
    return pipettes_data_to_lines(pipette_data)


def parse_modules(data, readme_map):

    def module_data_to_lines(module_data):
        if module_data:
            module_lines = ['### Modules']
            for module in module_data.values():
                line = f'* [{module["displayText"]}]({module["link"]})'
                module_lines.append(line)
            return module_lines
        return None

    module_list = list(set([module['type'] for module in data['modules']]))
    module_data = {
        module: readme_map['modules'][module]
        for module in module_list
    }
    return module_data_to_lines(module_data)


def parse(data, readme_map, folder_id):

    title_lines = parse_title(data)
    author_lines = ['### Author', '[Opentrons](https://opentrons.com/)']
    description_lines = ['## Description', 'This protocol does stuff!']
    category_lines = [
        '## Categories', '* Broad Category', '	* Specific Category']
    module_lines = parse_modules(data, readme_map)
    labware_lines = parse_labware(data,)
    pipette_lines = parse_pipettes(data, readme_map)
    deck_setup_lines = [
        '### Deck Setup',
        f'![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/\
custom-README-images/{folder_id}/deck.png)']
    reagent_setup_lines = [
        '### Reagent Setup',
        f'![reagents](https://opentrons-protocol-library-website.s3.amazonaws.\
com/custom-README-images/{folder_id}/reagents.png)']
    protocol_step_lines = ['### Protocol Steps', '1. Step 1...']
    process_lines = [
        '### Process',
        '1. Input your protocol parameters above.',
        '2. Download your protocol and unzip if needed.',
        '3. Upload your custom labware to the [OT App](https://opentrons.com/\
ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and \
selecting your labware files (.json extensions) if needed.',
        '4. Upload your protocol file (.py extension) to the [OT App](https://\
opentrons.com/ot-app) in the `Protocol` tab.',
        '5. Set up your deck according to the deck map.',
        '6. Calibrate your labware, tiprack and pipette using the OT App. \
For calibration tips, check out our \
[support articles](https://support.opentrons.com/en/collections/\
1559720-guide-for-getting-started-with-the-ot-2).',
        '7. Hit "Run".']
    additional_notes_lines = [
        '### Additional Notes',
        'If you have any questions about this protocol, please contact the \
Protocol Development Team by filling out the [Troubleshooting Survey]\
(https://protocol-troubleshooting.paperform.co/).']
    internal_lines = ['###### Internal', f'{folder_id}']

    readme_data = {
        'title': title_lines,
        'author': author_lines,
        'catgories': category_lines,
        'description': description_lines,  # add links
        'modules': module_lines,  # --- before
        'labware': labware_lines,
        'pipettes': pipette_lines,
        'deck-setup': deck_setup_lines,  # --- before
        'reagent-setup': reagent_setup_lines,
        'protocol-steps': protocol_step_lines,
        'process': process_lines,
        'additional-notes': additional_notes_lines,  # --- before
        'internal': internal_lines
    }
    return readme_data


def write_readme_text(readme_data):
    readme_lines = []
    for i, content in enumerate(readme_data.values()):
        if content:
            for line in content:
                readme_lines.append(line)
            if i < len(readme_data.values()) - 1:
                readme_lines.append('\n')
    return readme_lines


if __name__ == '__main__':
    protocol_path = sys.argv[1]
    protobuildPath = sys.argv[2]
    folder_id = str(Path(protocol_path).parent).split('/')[-1]

    with open(protobuildPath) as protobuild_file:
        protobuilds_data = json.load(protobuild_file)

    mapPath = 'protolib/parse/readme_map.json'
    with open(mapPath) as map_file:
        readme_map = json.load(map_file)
    # print('OT2 APIv2: parsing {} to {}'.format(sourceFilePath, destFilePath))

    readme_path = f'{Path(protocol_path).parent}/README.md'
    readme_content = parse(protobuilds_data, readme_map, folder_id)
    readme_text = write_readme_text(readme_content)

    if not Path(readme_path).exists():  # do not overwrite README
        with open(readme_path, 'w') as f:
            for line in readme_text:
                f.writelines(f'{line}\n')
