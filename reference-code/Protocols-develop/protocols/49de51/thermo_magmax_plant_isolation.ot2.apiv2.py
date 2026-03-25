import math
from opentrons.types import Point

metadata = {
        'apiLevel': '2.5',
        'protocolName': 'ThermoFisher MagMAX Plant DNA Isolation',
        'author': 'Chaz <chaz@opentrons.com>',
        'source': 'Custom Protocol Request'
        }


def run(ctx):

    num_samples = get_values(  # noqa: F821
            'num_samples')[0]
    plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '6')
    num_cols = math.ceil(num_samples / 8)

    reagents = ctx.load_labware(
            'nest_12_reservoir_15ml', '3')
    liquid_trash = ctx.load_labware(
            'nest_1_reservoir_195ml', '9').wells()[0]

    # Lysis
    lysis_buffer_b = reagents.columns()[0]
    rnase_a = reagents.columns()[1]
    lysis_buffer_a_wash_1 = ctx.load_labware(
        'nest_1_reservoir_195ml', '5').wells()[0]
    # Precipitation
    precipitation_solution = reagents.columns()[2]
    # Initial wash
    beads = reagents.columns()[3]
    ethanol_wash_2 = ctx.load_labware(
        'nest_1_reservoir_195ml', '2').columns()[0]
    elution_buffer = reagents.columns()[4]

    # Modules
    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()
    mag_plate = magdeck.load_labware('nest_96_wellplate_2ml_deep',
                                     'deepwell plate')
    tempdeck = ctx.load_module('Temperature Module Gen2', '4')
    temp_plate = tempdeck.load_labware('nest_96_wellplate_2ml_deep')

    # tipracks
    tip_racks = [
        ctx.load_labware(
            'opentrons_96_filtertiprack_200ul',
            x) for x in [
            '7',
            '8',
            '10',
            '11']]

    # pipette
    p300m = ctx.load_instrument(
        'p300_multi_gen2', "right", tip_racks=tip_racks)

    # define tip pickups
    tip_count = 0
    tip_max = len(tip_racks * 96)

    def pick_up():
        nonlocal tip_count
        nonlocal tip_max
        if tip_count == tip_max:
            ctx.pause('Please refill tipracks before resuming.')
            p300m.reset_tipracks()
            tip_count = 0
        tip_count += 8

    def pick_up_plate():
        for _ in range(num_cols):
            pick_up()

    plate_cols = plate.rows()[0][:num_cols]
    mag_plate_cols = mag_plate.rows()[0][:num_cols]
    temp_plate_cols = temp_plate.rows()[0][:num_cols]

    # Initial Lysis
    ctx.home()
    tempdeck.set_temperature(65)

    def initial_lysis(plate):
        pick_up_plate()
        [p300m.transfer(500, lysis_buffer_a_wash_1, col) for col in plate_cols]
        pick_up_plate()
        [p300m.transfer(70, lysis_buffer_b, col) for col in plate_cols]
        pick_up_plate()
        [p300m.transfer(20, rnase_a, col) for col in plate_cols]
        ctx.home()
    initial_lysis(plate)

    # Precipitation
    ctx.pause('Homogenize samples, then return plate tempdeck on robot.')
    ctx.delay(600)
    pick_up_plate()
    [p300m.transfer(130, precipitation_solution, col)
     for col in temp_plate_cols]
    ctx.home()

    # Initial wash
    def magdeck_remove_supernatant():
        pick_up_plate()
        for i, col in enumerate(mag_plate_cols):
            side = -1 if i % 2 == 0 else 1
            loc = col.bottom(0.5).move(Point(x=side * 2))
            p300m.pick_up_tip()
            for _ in range(2):
                p300m.move_to(col.center())
                p300m.transfer(200, loc, liquid_trash, new_tip='never')
                p300m.blow_out(liquid_trash)
            p300m.drop_tip()

    ctx.pause("""Incubate on ice for 5 minutes, then return plate to deck.
            Replace lysis buffer A with wash buffer 1.""")

    def initial_wash(plate):
        pick_up_plate()
        [p300m.transfer(400, plate_cols[x], mag_plate_cols[x])
         for x in range(0, 12)]
        pick_up_plate()
        [p300m.transfer(25, beads, col, mix_before=(3, 100))
         for col in mag_plate_cols]
        pick_up_plate()
        [p300m.transfer(400, ethanol_wash_2, col, mix_after=(3, 200))
         for col in mag_plate_cols]
        magdeck.engage()
        ctx.delay(300)
        magdeck_remove_supernatant()
        magdeck.disengage()
        pick_up_plate()
        [p300m.transfer(400, lysis_buffer_a_wash_1, col)
         for col in mag_plate_cols]
    initial_wash(plate)

    # Final wash
    ctx.pause("""Vortex plate for 1 minute at 750 RPM,
         then replace onto magdeck. Replace ethanol with wash buffer 2.""")
    magdeck.engage()

    def wash_2_function():
        ctx.delay(120)
        pick_up_plate()
        [p300m.transfer(400, col, liquid_trash) for col in mag_plate_cols]
        magdeck.disengage()
        pick_up_plate()
        [p300m.transfer(400, ethanol_wash_2, col) for col in mag_plate_cols]
        # mix?
        magdeck.engage()
        ctx.delay(120)
        magdeck_remove_supernatant()
    wash_2_function()
    wash_2_function()
    ctx.delay(300)
    magdeck.disengage()
    pick_up_plate()
    [p300m.transfer(150, elution_buffer, col) for col in mag_plate_cols]
    ctx.home()

    # Heat plate
    tempdeck.set_temperature(70)
    ctx.pause('Vortex plate, then return to tempdeck on robot')
    ctx.delay(300)
    # Elution
    ctx.pause("""Return plate to magdeck. Replace original
             plate at position 6 with a new skirted plate""")

    def elute(plate):
        magdeck.engage()
        ctx.delay(300)
        pick_up_plate()
        [p300m.transfer(400, temp_plate_cols[x], plate_cols[x])
         for x in range(0, 12)]
        ctx.home()
    elute(plate)
