"""Protocol."""
from opentrons.types import Point


metadata = {
    'protocolName': 'Ilumina DNA Prep Part 2 - Post Tagmentation Cleanup',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):
    """Protocol."""
    [num_samp, index_start_col, tip_park_start_col,
        asp_height, length_from_side,
        m20_mount, m300_mount] = get_values(  # noqa: F821
      "num_samp", "index_start_col",
      "tip_park_start_col", "asp_height",
      "length_from_side", "m20_mount", "m300_mount")

    if not 1 <= index_start_col <= 12:
        raise Exception("Enter an index start column 1-12")
    if not 1 <= index_start_col <= 12:
        raise Exception("Enter an index start column 1-12")

    num_samp = int(num_samp)
    num_col = int(num_samp/8)
    if num_col - tip_park_start_col < 0:
        raise Exception("Not enough tips on slot 11. Refill tip rack on 11.")

    index_start_col = int(index_start_col)-1
    tip_park_start_col = int(tip_park_start_col)-1

    # load labware
    mag_module = ctx.load_module('magnetic module gen2', '1')
    sample_plate = mag_module.load_labware('biorad_96_wellplate_200ul_pcr')
    reagent_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '2')
    index_plate = ctx.load_labware('illumina_96_wellplate_200ul', '3')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4')
    tiprack = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
               for slot in ['5', '6']]
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['7', '8', '9', '10']]
    park_tips_300 = ctx.load_labware(
                                'opentrons_96_filtertiprack_200ul', '11')

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tiprack)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack300)
    switch = True
    drop_count = 0
    drop_threshold = 120

    def _drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        if pip.type == 'multi':
            drop_count += 8
        else:
            drop_count += 1
        if drop_count >= drop_threshold:
            m300.home()
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()  # home before continuing with protocol
            drop_count = 0

    def change_speeds(pip, speed):
        pip.flow_rate.aspirate = speed
        pip.flow_rate.dispense = speed

    def remove_supernatant(vol, index, loc):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        m300.aspirate(vol, aspirate_loc)
        m300.dispense(vol, waste)
        m300.blow_out(waste.top())

    def mix_at_beads(vol, index, loc):
        side = 1 if index % 2 == 0 else -1
        aspirate_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        dispense_loc = loc.bottom(z=asp_height+4).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        for _ in range(15):
            m300.aspirate(vol, aspirate_loc)
            m300.dispense(vol, dispense_loc)

    # reagents
    twb = reservoir.wells()[1]
    tsb = reagent_plate.rows()[0][1]
    epm = reagent_plate.rows()[0][2:4]
    waste = reservoir.wells()[11]

    # transfer tsb from mastermix plate to sample plate
    airgap = 5
    for col in sample_plate.rows()[0][:num_col]:
        m20.pick_up_tip()
        m20.aspirate(5, tsb)
        m20.air_gap(airgap)
        m20.dispense(5+airgap, col)
        m20.mix(10, 17, col, rate=0.5)
        m20.blow_out(col.top())
        m20.touch_tip()
        _drop(m20)

    ctx.pause(
        '''
            Seal the plate with Microseal 'B', place on the preprogrammed
            thermal cycler, and run the PTC program. Afterwards, place plate
            back on magnetic module and select "Resume" on the Opentrons App.
            Empty trash if needed.

        '''
    )

    for wash in range(3):
        mag_module.engage()
        ctx.delay(minutes=5)

        # remove supernatant
        ctx.comment('\n Removing Supernatant \n')
        for i, col in enumerate(sample_plate.rows()[0][:num_col]):
            m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
            remove_supernatant(30 if wash == 0 else 50, i, col)
            m300.blow_out(col.top())
            m300.return_tip()
        mag_module.disengage()

        # add 50ul of twb over beads and mix at bead location
        ctx.comment('\n Adding TWB \n')
        change_speeds(m300, 35)
        for i, col in enumerate(sample_plate.rows()[0][:num_col]):
            m300.pick_up_tip()
            m300.aspirate(50, twb)
            m300.dispense(50, col)
            mix_at_beads(40, i, col)
            _drop(m300)
        change_speeds(m300, 94)

    ctx.pause(
        '''
        Put EPM Mastermix onto columns 3 and 4 of the reagent plate,
        then select "Resume" on the Opentrons App. Empty trash if needed.
        '''
    )

    # engage magnet, remove supernatant
    mag_module.engage()
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
        remove_supernatant(50, i, col)
        _drop(m300)  # drop parked tips
    mag_module.disengage()

    # add epm, mix at bead location
    ctx.comment('\n Adding EPM \n')
    for i, (epm_reagent, dest_col) in enumerate(
                                    zip(epm*num_col,
                                        sample_plate.rows()[0][:num_col])):
        m300.pick_up_tip()
        m300.aspirate(20, epm_reagent)
        m300.dispense(20, dest_col)
        mix_at_beads(20, i, dest_col)
        m300.blow_out(dest_col.top())
        _drop(m300)
    ctx.pause('''
    Prepare plate for index addition.
    Select "Resume" on the Opentrons App. Empty trash if needed.
    ''')

    for source_col, dest_col in zip(index_plate.rows()[0][index_start_col:
                                                          index_start_col
                                                          + num_col],
                                    sample_plate.rows()[0]):
        m20.pick_up_tip()
        m20.aspirate(5, source_col, rate=0.75)
        m20.dispense(5, dest_col, rate=0.75)
        m20.mix(10, 18, dest_col)
        m20.blow_out(dest_col.top())
        _drop(m20)
