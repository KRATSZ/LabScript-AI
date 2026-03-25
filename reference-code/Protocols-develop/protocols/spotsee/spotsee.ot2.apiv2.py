metadata = {
    'protocolName': 'Spotsee Well Distribution Protocol',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_cycles, vol, labware, start_tip,
        p20_mount, use_p20, p300_mount, use_p300] = get_values(  # noqa: F821
        "num_cycles", "vol", "labware", "start_tip", "p20_mount", "use_p20",
            "p300_mount", "use_p300")

    # p20_mount = 'left'
    # vol = 25
    # p300_mount = 'right'
    # labware = '40_well_plate'
    # start_tip = 4

    # labware
    reservoir = ctx.load_labware('nest_1_reservoir_195ml', 10)
    plate = ctx.load_labware(labware, 1)
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul' if vol < 10 else 'opentrons_96_tiprack_300ul', slot)  # noqa: E501
            for slot in [11]]

    red_wells = [
                'J1', 'I1', 'H1', 'G1', 'F1', 'E1', 'D1', 'C1', 'B1', 'A1',
                'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'J2',
                'J3', 'I3', 'H3', 'G3', 'F3', 'E3', 'D3', 'C3', 'B3', 'A3',
                'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'I4', 'J4',
                'J5', 'I5', 'H5', 'G5', 'F5', 'E5', 'D5', 'C5', 'B5', 'A5',
                'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'I6', 'J6',
                'J7', 'I7', 'H7', 'G7', 'F7', 'E7', 'D7', 'C7', 'B7', 'A7',
                'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8', 'I8', 'J8'
    ]

    # pipettes
    if use_p20:
        p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                                  tip_racks=tips)
    if use_p300:
        p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                                   tip_racks=tips)

    pip = p20 if vol < 10 else p300

    # mapping
    buffer = reservoir.wells()[0]

    # protocol
    pip.pick_up_tip(tips[0].wells()[start_tip-1])

    for cycle in range(num_cycles):
        ctx.comment('\n-------------ADDING BUFFER TO PLATE-------------\n\n')
        if labware == '80_well_plate':
            num_asp = pip.max_volume // vol

            chunks = [red_wells[i:i+num_asp] for i in range(0, len(red_wells),
                      num_asp)]

            for chunk in chunks:
                pip.aspirate(num_asp*vol, buffer)
                for well in chunk:
                    pip.dispense(vol, plate.wells_by_name()[well])
                    pip.move_to(plate.wells_by_name()[well].top(z=5))
                    ctx.comment(f'This is sheet number {cycle+1} out of total {num_cycles} sheets')  # noqa: E501

        else:
            num_asp = pip.max_volume // vol
            chunks = [plate.wells()[i:i+num_asp] for i in range(0,
                      len(plate.wells()),
                      num_asp)]

            for chunk in chunks:
                pip.aspirate(num_asp*vol, buffer)
                for well in chunk:
                    pip.dispense(vol, well)
                    pip.move_to(well.top(z=5))
                    ctx.comment(f'This is sheet number {cycle+1} out of total {num_cycles} sheets')  # noqa: E501

        pip.dispense(pip.current_volume, buffer.top())
        ctx.pause('Change Sheet on Deck')
    pip.drop_tip()
