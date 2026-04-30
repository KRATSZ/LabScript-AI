metadata = {
    'protocolName': 'Nextera DNA Flex NGS Library Prep: Cherrypick Samples',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}

example_csv = """source plate, source well, destination well
1, A1, A1
2, H2, B1
3, B3, C3
4, C7, D2
5, A3, C1
6, G1, D1
7, H1, D8
8, A12, C12
9, B11, E11
"""


def run(ctx):

    [cherrypicking_CSV, volume_to_cherrypick_in_ul, starting_tip_position,
        pipette_type, pipette_mount] = get_values(  # noqa: F821
            'cherrypicking_CSV', 'volume_to_cherrypick_in_ul',
            'starting_tip_position', 'pipette_type', 'pipette_mount')

    # load labware
    source_plates = {}
    for i in range(9):
        slot = str(i+1)
        source_plates[slot] = ctx.load_labware(
            'olympus_96_wellplate_200ul_pcr', slot, 'source plate ' + slot)
    destination_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr', '10', 'destination_plate')

    # pipette
    if pipette_type.split()[0] == 'P50' and volume_to_cherrypick_in_ul < 5:
        raise Exception('Cannot accommodate volumes < 5ul with P50')
        tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', '11')
    elif pipette_type.split()[0] == 'P300' and volume_to_cherrypick_in_ul < 30:
        raise Exception('Cannot accommodate volumes < 30ul with P300')
        tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', '11')
    else:
        tiprack = ctx.load_labware('opentrons_96_tiprack_10ul', '11')
    pip = ctx.load_instrument(
        pipette_type, mount=pipette_mount, tip_racks=[tiprack])
    all_wells = [tip for tip in tiprack.wells_by_name()]
    starting_tip_position = starting_tip_position.upper()
    if starting_tip_position not in all_wells:
        raise Exception('Invalid starting tip (must be in A1-H12)')
    tip_count = all_wells.index(starting_tip_position)
    pip.starting_tip = tiprack.wells_by_name()[starting_tip_position]

    def pick_up():
        nonlocal tip_count
        if tip_count == 96:
            ctx.pause('Refill 300ul tiprack in slot 11 before resuming.')
            pip.reset_tipracks()
            tip_count = 0
            pip.starting_tip = tiprack.wells()[0]
        tip_count += 1
        pip.pick_up_tip()

    # parse CSV
    data = [
        [val.strip() for val in line.split(',')]
        for line in cherrypicking_CSV.splitlines() if line][1:]

    for trans in data:
        [s_plate, s_well, d_well] = [val for val in trans]
        if s_plate not in [key for key in source_plates]:
            raise Exception('Invalid source plate: ' + s_plate)
        if s_well not in all_wells:
            raise Exception('Invalid source well: ' + s_well)
        if d_well not in all_wells:
            raise Exception('Invlaid destination well: ' + d_well)

        pick_up()
        dest = destination_plate.wells_by_name()[d_well]
        pip.transfer(
            volume_to_cherrypick_in_ul,
            source_plates[s_plate].wells_by_name()[s_well],
            dest,
            new_tip='never'
        )
        pip.blow_out(dest.top(-2))
        pip.drop_tip()
