metadata = {
    'apiLevel': '2.12',
    'protocolName': 'Rapid Barcoding Kit (SQK-RBK004)',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Custom Protocol Request'
}


def run(ctx):

    sample_count, sample_vol = get_values(  # noqa: F821
            'sample_count', 'sample_vol')
    thermocycler = ctx.load_module('thermocycler')
    thermocycler.open_lid()
    thermocycler_plate = thermocycler.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt')

    magdeck = ctx.load_module('magnetic module gen2', '4')  # update to gen2
    magdeck.disengage()
    mag_plate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    mag_well = mag_plate.wells_by_name()["A1"]

    tempdeck = ctx.load_module(
        'temperature module gen2',
        '1')  # update to gen2
    temp_plate = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_0.5ml_screwcap')

    RAP = temp_plate.wells_by_name()["A1"]
    AMPure_beads = temp_plate.wells_by_name()["A2"]

    fragmentation_mixes = [temp_plate.wells_by_name()["{}{}".format(
        a, b)] for a in ["B", "C"] for b in range(1, 7)][0:sample_count]

    tube_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '5')
    H2O = tube_rack.wells_by_name()["A1"]
    ethanol_70 = tube_rack.wells_by_name()["A2"]
    tris_nacl = tube_rack.wells_by_name()["A3"]
    liquid_trash = tube_rack.wells_by_name()["B1"]
    cleaned_library = tube_rack.wells_by_name()["C1"]

    p20s = ctx.load_instrument(
        'p20_single_gen2', 'left', tip_racks=[
            ctx.load_labware(
                'opentrons_96_filtertiprack_20ul', '6')])
    p300s = ctx.load_instrument(
        'p300_single_gen2', "right", tip_racks=[
            ctx.load_labware(
                'opentrons_96_filtertiprack_200ul', '9')])

    tempdeck.set_temperature(4)

    p20s.default_speed = 50  # Slow to 1/8 speed
    # Adjust to 7.5 with H2O
    for well in thermocycler_plate.wells()[0:sample_count]:
        p20s.transfer((7.5 - sample_vol), H2O, well, mix_after=(2, 4))

    # Move 2.5 of fragmentation mixes to block
    for i, f in enumerate(fragmentation_mixes):
        p20s.transfer(2.5, f, thermocycler_plate.wells()[
                      i], mix_after=(2, 5), new_tip='always')
    p20s.default_speed = 400

    # Thermocycle
    thermocycler.close_lid()
    thermocycler.set_lid_temperature(90)
    thermocycler.execute_profile(
        steps=[
            {
                'temperature': 30, 'hold_time_seconds': 60}, {
                'temperature': 80, 'hold_time_seconds': 60}, {
                'temperature': 15, 'hold_time_seconds': 10}],
        repetitions=1, block_max_volume=10)
    thermocycler.open_lid()

    # Pool Samples
    if 20 * sample_count > 200:
        pooled_library = tube_rack.wells_by_name()["B2"]
    else:
        pooled_library = mag_plate.wells_by_name()["A1"]

    for well in thermocycler_plate.wells()[0:sample_count]:
        p20s.transfer(10, well, pooled_library, new_tip='always')

    # Wash

    # Add beads, wait
    p300s.transfer(
        (10 * sample_count),
        AMPure_beads,
        pooled_library,
        mix_before=(
            10,
            (8 * sample_count)),
        mix_after=(
            2,
            (10 * sample_count)),
        new_tip='always')
    ctx.delay(300)

    # Move half of beads to magplate, pull down, move rest.
    if 20 * sample_count > 200:
        p300s.transfer(
            (10 * sample_count),
            pooled_library,
            mag_well,
            mix_before=(
                3,
                (15 * sample_count)),
            new_tip='always')
        magdeck.engage()
        ctx.delay(450)
        p300s.transfer(200, mag_well, liquid_trash, new_tip='always')
        p300s.transfer(
            (10 * sample_count),
            pooled_library,
            mag_well,
            mix_before=(
                3,
                (5 * sample_count)),
            new_tip='always')

    magdeck.engage()
    ctx.delay(600)  # Drag down for a full 10 minutes
    p300s.transfer(200, mag_well, liquid_trash, new_tip='always')

    p300s.default_speed = 100  # Slow down pipette speed to 1/8
    for _ in range(0, 2):
        p300s.transfer(
            200,
            ethanol_70,
            mag_well.bottom(7),
            new_tip='always')  # halfway
        ctx.delay(10)
        p300s.transfer(200, mag_well, liquid_trash, new_tip='always')
        ctx.delay(10)
    p300s.default_speed = 400

    # Dry for 10 minutes
    ctx.delay(600)
    magdeck.disengage()

    p20s.transfer(10, tris_nacl, mag_well, mix_after=(3, 8), new_tip='always')
    ctx.delay(120)
    magdeck.engage()
    ctx.delay(300)
    p20s.transfer(10, mag_well, cleaned_library, new_tip='always')

    # Add RAP
    p20s.transfer(1, RAP, mag_well, mix_after=(2, 5), new_tip='always')
    ctx.delay(300)
