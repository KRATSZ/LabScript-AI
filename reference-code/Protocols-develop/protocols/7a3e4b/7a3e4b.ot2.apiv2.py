metadata = {
    'protocolName': 'Cherrypicking with Source and Destination',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
    }


def run(protocol):
    [volumes_csv, pip_model, pip_mount, sp_type,
     dp_type, tip_reuse] = get_values(  # noqa: F821
     'volumes_csv', 'pip_model', 'pip_mount', 'sp_type', 'dp_type',
     'tip_reuse')

    # create pipette and tip rack
    pip_max = pip_model.split('_')[0][1:]

    pip_max = '300' if pip_max == '50' else pip_max
    tip_name = 'opentrons_96_tiprack_'+pip_max+'ul'

    tiprack_slots = ['1', '4', '7', '10']
    tips = [protocol.load_labware(tip_name, slot)
            for slot in tiprack_slots]

    pipette = protocol.load_instrument(
        pip_model, pip_mount, tip_racks=tips)

    source_plate = protocol.load_labware(sp_type, '2', 'Source Labware')

    dest_plate = protocol.load_labware(dp_type, '3', 'Destination Labware')

    data = [row.split(',') for row in volumes_csv.strip().splitlines() if row]

    if tip_reuse == 'never':
        pipette.pick_up_tip()
    for src_well, vol, dest_well in data[1:]:
        vol = float(vol)
        dest_well = dest_well.strip()
        pipette.transfer(
            vol,
            source_plate[src_well],
            dest_plate[dest_well],
            new_tip=tip_reuse
        )
    if tip_reuse == 'never':
        pipette.drop_tip()
