import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Swift Rapid NGS Part 4 - SPRI Clean',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_samp, tip_type, overage_percent, bead_dry_time,
        p300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_type", "overage_percent",
        "bead_dry_time", "p300_mount")

    # keep user in range
    num_samp = int(num_samp)
    if not 0.0 <= overage_percent <= 10.0:
        raise Exception("Enter a an overage percent between 5-10%")
    overage_percent = 1+overage_percent/100
    num_cols = math.ceil(int(num_samp/8))

    # load labware
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_mod.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')
    final_plate = ctx.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt', '9')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2')
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['4', '5']]

    # load instrument
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=tiprack300)

    num_cols = math.ceil(int(num_samp/8))
    sample_cols = mag_plate.rows()[0][8:8+num_cols]
    beads = reservoir.wells()[1]
    ethanol = reservoir.wells()[11]
    trash = reservoir.wells()[4]
    te = reservoir.wells()[0]

    # adding magbeads
    ctx.comment('\nAdding magbeads\n')
    m300.pick_up_tip()
    m300.distribute(30, beads,
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
        m300.aspirate(55, col.bottom().move(
                Point(x=(col.diameter/2-1)*side)))
        m300.dispense(55, trash.top())
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
            m300.aspirate(200, col.bottom().move(
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
        m300.aspirate(22, te)
        m300.dispense(22, col.top())
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

    for i, (well, dest) in enumerate(zip(sample_cols,
                                     final_plate.rows()[0][4:])):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip()
        m300.aspirate(20, well.bottom().move(
                Point(x=(well.diameter/2-1)*side)))
        m300.dispense(20, dest)
        m300.drop_tip()
        ctx.comment('\n\n')
    ctx.comment('''Protocol complete -
    If desired, this is a safe stopping point.
    Supernatant is in columns 5, 6, and 7.
    Samples can be stored in -20C freezer.''')
