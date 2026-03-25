# flake8: noqa
from opentrons.types import Point

metadata = {
    'protocolName': '4.2 Post Sample Index PCR Size Selection – SPRIselect',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}

def run(ctx):

    engage_height = 23

    [num_samp, tip_rack, m300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_rack", "m300_mount")

    if not 1 <= num_samp <= 8:
        raise Exception("Enter a sample number between 1-8")

    # labware
    temp_mod_reag = ctx.load_module('temperature module', 6)
    temp_mod = ctx.load_module('temperature module gen2', 9)
    dummy_rack = temp_mod.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap',
                                       "DUMMY RACK")
    dummy_plate = temp_mod_reag.load_labware('eppendorf_96_aluminumblock_200ul',
                                             "DUMMY PLATE")
    print(temp_mod, dummy_plate, dummy_rack)
    mag_mod = ctx.load_module('magnetic module', 10)
    mag_mod.disengage()
    strip_tube_plate = mag_mod.load_labware('eppendorf_96_wellplate_200ul',
                                            "SAMPLE PLATE")

    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 11)
    reagent_plate = ctx.load_labware('biorad_96_wellplate_200ul', 4,
                                     "REAGENT PLATE")

    tipracks = [ctx.load_labware(tip_rack, slot)
                for slot in [7]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2',
                               m300_mount,
                               tip_racks=tipracks)

    num_channels_per_pickup = num_samp
    tips_ordered = [
        tip for rack in tipracks
        for row in rack.rows()[
            len(rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]  # noqa: E501
        for tip in row]

    tip_count = 0

    def pick_up():
        nonlocal tip_count
        m300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    def blowout(well):
        m300.blow_out(well.top(z=-5))
        m300.touch_tip(v_offset=-5)
        m300.air_gap(20)

    # mapping
    samples = strip_tube_plate.columns()[0][0]
    trash = reservoir.wells()[-1]
    ethanol = reservoir.wells()[0]
    spri_beads = reagent_plate.rows()[0][0]
    buffer = reagent_plate.rows()[0][11]

    ctx.comment('\n\n~~~~~~~~~~~~~~~~ADDING SPRI BEADS~~~~~~~~~~~~~~~~\n')
    pick_up()
    m300.mix(5, 100, spri_beads)
    m300.aspirate(100, spri_beads)
    m300.dispense(100, samples)
    m300.mix(15, 160, samples)
    m300.blow_out(samples.top())
    m300.touch_tip(v_offset=-5)
    m300.drop_tip()

    ctx.comment('\n\n~~~~~~~~~~~~~~INCUBATING FOR 5 MINUTES~~~~~~~~~~~~~~\n')
    ctx.delay(minutes=5)

    ctx.comment('\n\n~~~~~~~~~~~~~~ENGAGE MAGNET 5 MINUTES~~~~~~~~~~~~~~\n')
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=5)

    ctx.comment('\n\n~~~~~~~~~~~~~~REMOVING SUPERNATANT~~~~~~~~~~~~~~\n')
    length_from_side = 2
    side = -1
    pick_up()
    aspirate_loc = samples.bottom(z=1).move(
            Point(x=(samples.diameter/2-length_from_side)*side))
    m300.aspirate(200, aspirate_loc, rate=0.5)
    m300.dispense(200, trash)
    m300.blow_out()
    m300.air_gap(20)
    m300.drop_tip()

    ctx.comment('\n\n~~~~~~~~~~~~~~TWO ETHANOL WASHES~~~~~~~~~~~~~~\n')
    for i in range(2):
        dispense_loc = samples.bottom(z=5).move(
                Point(x=(samples.diameter/2-length_from_side)*side))
        pick_up()
        m300.aspirate(200, ethanol)
        m300.dispense(200, dispense_loc)
        m300.move_to(samples.top(z=-3))
        ctx.delay(seconds=30)

        m300.aspirate(m300.max_volume, aspirate_loc, rate=0.5)
        m300.dispense(m300.max_volume, trash)
        m300.blow_out()
        m300.drop_tip()

    aspirate_loc = samples.bottom(z=0.5).move(
        Point(x=(samples.diameter/2-length_from_side)*side))

    for _ in range(2):
        pick_up()
        m300.aspirate(50, aspirate_loc, rate=0.5)
        m300.dispense(50, trash)
        m300.drop_tip()
        ctx.delay(minutes=2)

    mag_mod.disengage()

    ctx.comment('\n\n~~~~~~~~~~~~~~ADDING ELUTION SOLUTION~~~~~~~~~~~~~~\n')

    side_mix = 1
    mix_loc = samples.bottom(z=1).move(
            Point(x=(samples.diameter/2-1)*side_mix))
    pick_up()
    m300.aspirate(41, buffer)
    m300.dispense(41, samples)
    for _ in range(15):
        m300.aspirate(25, mix_loc, rate=0.5)
        ctx.delay(seconds=1)
        m300.dispense(25, mix_loc, rate=0.5)
        ctx.delay(seconds=1)
    m300.move_to(samples.top())
    ctx.delay(seconds=5)
    blowout(samples)
    m300.drop_tip()

    ctx.comment('\n\n~~~~~~~~~~~~~~INCUBATING FOR 2 MINUTES~~~~~~~~~~~~~~\n')
    ctx.delay(minutes=2)

    ctx.comment('\n\n~~~~~~~~~~~~~~MOVING ELUTE~~~~~~~~~~~~~~\n')

    pick_up()
    for _ in range(15):
        m300.aspirate(25, mix_loc, rate=0.5)
        ctx.delay(seconds=1)
        m300.dispense(25, mix_loc, rate=0.5)
        ctx.delay(seconds=1)
    m300.move_to(samples.top(z=-5))
    ctx.delay(seconds=5)
    blowout(samples)
    m300.drop_tip()

    aspirate_loc = samples.bottom(z=1).move(
        Point(x=(samples.diameter/2-length_from_side)*side))

    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=5)
    pick_up()
    m300.aspirate(40, aspirate_loc, rate=0.5)
    m300.dispense(40, strip_tube_plate.columns()[1][0])
    blowout(strip_tube_plate.columns()[1][0])
    m300.touch_tip()
    m300.drop_tip()
