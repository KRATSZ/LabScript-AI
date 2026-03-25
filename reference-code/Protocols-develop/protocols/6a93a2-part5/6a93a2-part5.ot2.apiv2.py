import math
from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'Swift Rapid NGS Part 5 - Indexing and SPRI Clean',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_samp, tip_type, index_start_column, tc_num_reps,
        overage_percent, bead_dry_time,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_type", "index_start_column", "tc_num_reps",
        "overage_percent", "bead_dry_time", "p20_mount", "p300_mount")

    # keep user in range
    if not 1 <= index_start_column <= 12:
        raise Exception("Enter a column number between 1-12")
    if not 0.0 <= overage_percent <= 10.0:
        raise Exception("Enter a an overage percent between 5-10%")
    overage_percent = 1+overage_percent/100
    num_samp = int(num_samp)
    num_cols = math.ceil(int(num_samp/8))

    # load labware
    thermocycler = ctx.load_module('thermocycler')
    tc_plate = thermocycler.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
    index_plate = ctx.load_labware('thermofisherarmadillo_96_wellplate_200ul',
                                   '3')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2')
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_mod.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')
    tiprack20 = [ctx.load_labware(tip_type, slot) for slot in ['6', '9']]
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['4', '5']]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=tiprack300)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all tip racks")
            pip.reset_tipracks()
            pip.pick_up_tip()

    if thermocycler.lid_position != 'open':
        thermocycler.open_lid()
    thermocycler.set_lid_temperature(108)

    # add indexing primers to each sample
    well_from_start_column = (index_start_column-1)*8
    airgap = 5
    for index_primer_well, samp_well in zip(
                                index_plate.wells()[well_from_start_column:],
                                tc_plate.wells()[32:32+num_samp]):
        p20.pick_up_tip()
        p20.aspirate(5, index_primer_well)
        p20.air_gap(airgap)
        p20.touch_tip()
        p20.dispense(5+airgap, samp_well)
        p20.blow_out()
        p20.drop_tip()

    # add mastermix to sample + index primer
    mastermix = reservoir.wells()[2]
    for col in tc_plate.rows()[0][4:4+num_cols]:
        m300.pick_up_tip()
        m300.aspirate(25*overage_percent, mastermix)
        m300.dispense(25*overage_percent, col)
        m300.mix(15, 45)
        m300.touch_tip()
        m300.drop_tip()

    # run thermocycler profile based on quantity of purified RNA
    profile = [
        {'temperature': 98, 'hold_time_minutes': 2},
        {'temperature': 98, 'hold_time_seconds': 20},
        {'temperature': 60, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_minutes': 1},
    ]
    thermocycler.close_lid()
    thermocycler.execute_profile(steps=profile[:1],
                                 repetitions=1,
                                 block_max_volume=50)
    thermocycler.execute_profile(steps=profile[1:4],
                                 repetitions=tc_num_reps,
                                 block_max_volume=50)
    thermocycler.execute_profile(steps=profile[4:],
                                 repetitions=1,
                                 block_max_volume=50)
    thermocycler.set_block_temperature(4, block_max_volume=20.5)
    thermocycler.open_lid()

    # SPRI cleanup
    num_cols = math.ceil(int(num_samp/8))
    sample_cols = mag_plate.rows()[0][8:8+num_cols]
    beads = reservoir.wells()[1]
    ethanol = reservoir.wells()[11]
    trash = reservoir.wells()[4]
    te = reservoir.wells()[0]

    # adding magbeads
    ctx.comment('\nAdding magbeads\n')
    m300.pick_up_tip()
    m300.distribute(42.5, beads,
                    [col.top() for col in sample_cols],
                    mix_before=(5, 200),
                    new_tip='never')
    m300.drop_tip()

    # mix solution, cut flow rate to avoid bubbles
    m300.flow_rate.aspirate = 7.56  # same flow rate as p20
    m300.flow_rate.dispense = 7.56
    for col in sample_cols:
        m300.pick_up_tip()
        m300.mix(10, 80, col)
        m300.touch_tip()
        m300.drop_tip()
    m300.flow_rate.aspirate = 150  # set flow rate back to default
    m300.flow_rate.dispense = 300

    ctx.delay(minutes=7.5)
    ctx.pause('''Remove magnetic plate from deck, seal and spin down -
                 place back on the magnetic module
                 If needed, please empty trash.''')

    # magnetic Engage, extraction
    ctx.comment('\nEngaging magnetic module in extraction step\n')
    mag_mod.engage()
    ctx.delay(minutes=5)

    # remove supernatant before ethanol wash
    for i, col in enumerate(sample_cols):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip()
        m300.move_to(col.center())
        m300.aspirate(85, col.bottom().move(
                Point(x=(col.diameter/2-1)*side)))
        m300.dispense(85, trash.top())
        m300.drop_tip()

    # 2x ethanol washes
    for i in range(2):
        # add ethanol to beads and incubate
        m300.pick_up_tip()
        for col in sample_cols:
            m300.aspirate(200, ethanol)
            m300.dispense(200, col.top())
        m300.drop_tip()
        ctx.delay(seconds=30)

        # trash ethanol
        for col in sample_cols:
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip()
            m300.move_to(col.center())
            m300.aspirate(50, col.top(z=-(col.depth-col.depth/4)).move(
                    Point(x=(col.diameter/2-1)*side)))
            m300.aspirate(50, col.top(z=-(col.depth-2*col.depth/4)).move(
                    Point(x=(col.diameter/2-1)*side)))
            m300.aspirate(50, col.top(z=-(col.depth-3*col.depth/4)).move(
                    Point(x=(col.diameter/2-1)*side)))
            m300.aspirate(50, col.bottom().move(
                    Point(x=(col.diameter/2-1)*side)))
            m300.dispense(200, trash.top())
            m300.drop_tip()
            ctx.comment('\n\n')
    mag_mod.disengage()
    ctx.pause('''Seal and spin down sample plate -
                if needed, please empty trash.''')
    ctx.delay(minutes=bead_dry_time)

    # add te and mix
    m300.pick_up_tip()
    for col in sample_cols:
        m300.aspirate(27, te)
        m300.dispense(27, col.top())
    m300.drop_tip()

    m300.flow_rate.aspirate = 7.56  # same flow rate as p20
    m300.flow_rate.dispense = 7.56
    for col in sample_cols:
        m300.pick_up_tip()
        m300.mix(5, 10, col)
        m300.blow_out()
        m300.drop_tip()
    m300.flow_rate.aspirate = 150  # set flow rate back to default
    m300.flow_rate.dispense = 300

    # incubate for 4 minutes at RT
    ctx.delay(minutes=4)
    ctx.pause('''Seal and spin down sample plate -
             remove seal, then place back on magnet.
             If needed, please empty trash.''')
    mag_mod.engage()
    ctx.delay(minutes=3)

    for i, (well, dest) in enumerate(zip(mag_plate.rows()[0][4:4+num_cols],
                                     mag_plate.rows()[0][8:])):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip()
        m300.aspirate(25, well.bottom().move(
                Point(x=(well.diameter/2-1)*side)))
        m300.dispense(25, dest)
        m300.drop_tip()
        ctx.comment('\n\n')
    ctx.comment('''Protocol complete. Samples are in column 9, 10, and 11''')
