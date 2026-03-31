import os
import pathlib

PROTOCOL_URIS_FOR_BANNER = [
    'https://protocols.opentrons.com/protocol/customizable_serial_dilution_ot2',
    'https://protocols.opentrons.com/protocol/nucleic_acid_purification_with_magnetic_beads',
    'https://protocols.opentrons.com/protocol/cherrypicking',
    'https://protocols.opentrons.com/protocol/omega_biotek_magbind_totalpure_NGS',
    'https://protocols.opentrons.com/protocol/normalization',
    'https://protocols.opentrons.com/protocol/Opentrons_Logo',
    'https://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1',
    'https://protocols.opentrons.com/protocol/pcr_prep_part_1',
    'https://protocols.opentrons.com/protocol/274d2a',
    'https://protocols.opentrons.com/protocol/pcr_prep_part_2',
    'https://protocols.opentrons.com/protocol/swift-2s-turbo-pt1',
    'https://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2',
    'https://protocols.opentrons.com/protocol/dinosaur',
    'https://protocols.opentrons.com/protocol/3359a5',
    'https://protocols.opentrons.com/protocol/sci-macherey-nagel-nucleomag',
    'https://protocols.opentrons.com/protocol/sci-mag-bind-blood-tissue-kit',
    'https://protocols.opentrons.com/protocol/sci-omegabiotek-extraction-fa',
    'https://protocols.opentrons.com/protocol/sci-omegabiotek-magbind',
    'https://protocols.opentrons.com/protocol/sci-omegabiotek-magbind-total-rna-96',
    'https://protocols.opentrons.com/protocol/sci-promega-magazorb-dna-mini-prep-kit',
    'https://protocols.opentrons.com/protocol/sci-zymo-directzol-magbead',
    'https://protocols.opentrons.com/protocol/swift-fully-automated',
    'https://protocols.opentrons.com/protocol/macherey-nagel-nucleomag-clean-up',
    'https://protocols.opentrons.com/protocol/macherey-nagel-nucleomag-tissue',
    'https://protocols.opentrons.com/protocol/macherey-nagel-nucleomag-DNA-microbiome',
    'https://protocols.opentrons.com/protocol/macherey-nagel-nucleomag-dna-food',
    'https://protocols.opentrons.com/protocol/macherey-nagel-nucleomag-virus']


PROTOCOL_SLUGS = [
    uri.split('/')[-1] for uri in PROTOCOL_URIS_FOR_BANNER]

for slug in PROTOCOL_SLUGS:
    readme_path = f'protocols/{slug}/README.md'
    with open(readme_path) as rm_file:
        content = rm_file.readlines()
    injection_index = None
    for i, line in enumerate(content):
        if '# categories' in line.lower():
            injection_index = i
            print(injection_index, line)
            break

    if not injection_index:
        print(f"ERROR parsing {slug}")
        break

    content.insert(
        injection_index,
        f"***Opentrons has launched a new Protocol Library. You should use the [new page for this protocol](library.opentrons.com/p/{slug.lower()}). This page won’t be available after January 31st, 2024.***\n\n")

    with open(readme_path, 'w') as rm_file:
        rm_file.writelines(content)
