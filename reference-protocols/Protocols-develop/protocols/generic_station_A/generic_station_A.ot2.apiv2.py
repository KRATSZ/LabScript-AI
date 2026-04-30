metadata = {
    'protocolName': 'Generic Sample Plating Protocol (Station A)',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.5'
}


def run(protocol):
    [num_samples, samp_vol, plate_type,
     tube_type, pip_type] = get_values(  # noqa: F821
        'num_samples', 'samp_vol', 'plate_type',
        'tube_type', 'pip_type')

    # load labware and pipettes
    pip_name, tip_name = pip_type.split()
    tips = [protocol.load_labware(tip_name, '3')]
    pipette = protocol.load_instrument(pip_name, 'right', tip_racks=tips)

    dest_plate = protocol.load_labware(plate_type, '2')

    t_slots = ['1', '4', '7', '10', '5', '8', '11']
    src_tubes = [protocol.load_labware(tube_type, s) for s in t_slots]

    # define source/dest wells
    if num_samples > 96:
        raise Exception('The number of samples should be 1-96.')

    dest_wells = dest_plate.wells()[:num_samples]
    src_wells = [t for tube in src_tubes for t in tube.wells()][:num_samples]
    air_vol = round(samp_vol*0.1)

    for src, dest in zip(src_wells, dest_wells):
        pipette.pick_up_tip()
        pipette.transfer(samp_vol, src, dest, new_tip='never', air_gap=air_vol)
        pipette.drop_tip()
