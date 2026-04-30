import math
from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'Swift Rapid NGS Part 1 - Reverse Transcription',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, tip_type, overage_percent, bead_dry_time,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_type", "overage_percent", "bead_dry_time",
        "p20_mount", "p300_mount")

    # keep user in range
    num_samp = int(num_samp)
    if not 0.0 <= overage_percent <= 10.0:
        raise Exception("Enter an overage percent between 5-10%")
    overage_percent = 1+overage_percent/100
    num_cols = math.ceil(int(num_samp/8))

    # load labware
    thermocycler = ctx.load_module('thermocycler')
    samp_plate = thermocycler.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
    temperature_mod = ctx.load_module('temperature module gen2', '3')
    alum_tuberack = temperature_mod.load_labware(
                        'opentrons_24_aluminumblock_generic_2ml_screwcap')
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_mod.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2')
    tiprack20 = [ctx.load_labware(tip_type, slot) for slot in ['6', '9']]
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['4', '5']]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=tiprack300)

    def pick_up():
        try:
            p20.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            p20.reset_tipracks()
            p20.pick_up_tip()

    # setting all temperatures
    if thermocycler.lid_position != 'open':
        thermocycler.open_lid()
    thermocycler.set_lid_temperature(80)
    thermocycler.set_block_temperature(25)
    temperature_mod.set_temperature(4)

    # METHOD 1 - MAKING AND DISTRIBUTING MASTERMIX
    rapid_enzyme1 = alum_tuberack.rows()[0][0]
    rapid_enzyme2 = alum_tuberack.rows()[0][1]
    nuc_free_water = alum_tuberack.rows()[0][2]
    mastermix = alum_tuberack.rows()[0][3]

    # make mastermix
    for i, tube in enumerate([rapid_enzyme1, rapid_enzyme2, nuc_free_water]):
        pick_up()
        if i < 2:
            p20.transfer(int(num_samp*overage_percent), tube, mastermix.top(),
                         new_tip='never')
            p20.drop_tip()
        else:
            p20.transfer(num_samp*4*overage_percent, nuc_free_water,
                         mastermix.top(),
                         new_tip='never')
            p20.drop_tip()

    ctx.pause('''Mastermix solution made. Mix thouroughly and pulse spin -
                 after, place tube rack back on the temperature module for
                 mastermix to be distributed.''')

    # distribute mastermix and mix
    pick_up()
    for dest in samp_plate.wells()[:num_samp]:
        p20.aspirate(6*overage_percent, mastermix)
        p20.dispense(6*overage_percent, dest.top())
    p20.drop_tip()
    for col in samp_plate.rows()[0][:num_cols]:
        m300.pick_up_tip()
        m300.mix(15, 20, col)
        m300.blow_out()
        m300.drop_tip()

    ctx.pause('''Mastermix distributed and mixed thouroughly -
                 pulse spin to collect contents. Seal plate and place back
                 on deck. After, the thermocycler lid
                 will automatically close and begin the heating and cooling
                 steps.  If needed, please empty trash.''')

    # run thermocycler profile and hold
    thermocycler.close_lid()
    profile = [
        {'temperature': 25, 'hold_time_minutes': 10},
        {'temperature': 42, 'hold_time_minutes': 30},
        {'temperature': 70, 'hold_time_minutes': 15},
    ]
    thermocycler.execute_profile(steps=profile,
                                 repetitions=1,
                                 block_max_volume=20)
    thermocycler.set_block_temperature(4, block_max_volume=20)
    thermocycler.open_lid()
    ctx.pause('Move sample plate from Thermocycler to Magnetic Module')

    # METHOD 2 - MAGNETIC BEAD EXTRACTION
    sample_cols = mag_plate.rows()[0][:num_cols]
    te = reservoir.wells()[0]
    beads = reservoir.wells()[1]
    ethanol = reservoir.wells()[11]
    trash = reservoir.wells()[4]

    # adding te
    ctx.comment('\nAdding low EDTA TE\n')
    m300.pick_up_tip()
    m300.distribute(30, te,
                    [col.top() for col in sample_cols],
                    new_tip='never')
    m300.drop_tip()

    # adding magbeads
    ctx.comment('\nAdding magbeads\n')
    m300.pick_up_tip()
    m300.distribute(50, beads,
                    [col.top() for col in sample_cols],
                    mix_before=(5, 200),
                    new_tip='never')
    m300.drop_tip()

    # mix solution, cut flow rate to avoid bubbles
    m300.flow_rate.aspirate = 7.56  # same flow rate as p20
    m300.flow_rate.dispense = 7.56
    for col in sample_cols:
        m300.pick_up_tip()
        m300.mix(15, 80, col)
        m300.touch_tip()
        m300.drop_tip()
    m300.flow_rate.aspirate = 150  # set flow rate back to default
    m300.flow_rate.dispense = 300

    # 7.5 minute incubation
    ctx.delay(minutes=7.5)
    ctx.pause('''Remove magnetic plate from deck, seal and spin down -
                 place back on the magnetic module.
                 If needed, please empty trash.''')

    # engage magnets with 5 minute rest
    ctx.comment('\nEngaging magnetic module in extraction step\n')
    mag_mod.engage()
    ctx.delay(minutes=5)

    # remove supernatant before ethanol wash
    for i, col in enumerate(sample_cols):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip()
        m300.move_to(col.center())
        m300.aspirate(100, col.bottom().move(
                Point(x=(col.diameter/2-1)*side)))
        m300.dispense(100, trash.top())
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
    pick_up()
    for well in mag_plate.wells()[:num_samp]:
        p20.aspirate(12, te)
        p20.dispense(12, well.top())
    p20.drop_tip()

    m300.flow_rate.aspirate = 7.56  # same flow rate as p20
    m300.flow_rate.dispense = 7.56
    for col in sample_cols:
        m300.pick_up_tip()
        m300.mix(10, 20, col)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip()
    m300.flow_rate.aspirate = 150  # set flow rate back to default
    m300.flow_rate.dispense = 300

    # incubate for 4 minutes at RT
    ctx.delay(minutes=4)
    mag_mod.disengage()
    ctx.pause('''Seal and spin down sample plate -
             remove seal, then place back on magnet.
             If needed, please empty trash.''')
    mag_mod.engage()
    ctx.delay(minutes=3)

    # move supernatant to new wells - columns 5, 6, and 7
    for i, (well, dest) in enumerate(zip(mag_plate.wells()[:num_samp],
                                     mag_plate.wells()[32:])):
        side = -1 if i % 2 == 0 else 1
        pick_up()
        p20.aspirate(12, well.bottom().move(
                Point(x=(well.diameter/2-1)*side)))
        p20.dispense(12, dest)
        p20.drop_tip()
        ctx.comment('\n\n')
    ctx.comment('''Protocol complete -
    If desired, this is a safe stopping point.
    Supernatant is in columns 5, 6, 7. Check for excessive bead carryover.
    Samples can be stored at 4 degrees C for up to 24 hours.''')
