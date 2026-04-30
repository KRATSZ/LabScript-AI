import math

metadata = {
    'protocolName': 'COVID MM-QC-v3 Protocol',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [p1000_mount, temperature, volume, mm_height] = get_values(  # noqa: F821
     "p1000_mount", "temperature", "volume", "mm_height")

    # Load Labware
    tuberack = ctx.load_labware(
        'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 4)
    temp_mod = ctx.load_module('temperature module gen2', 10)
    dest_tubes = temp_mod.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap')
    tiprack_1000ul = ctx.load_labware('opentrons_96_filtertiprack_1000ul', 1)

    # Load Instruments
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=[tiprack_1000ul])

    # Liquid Level Tracking
    float(mm_height)
    min_h = 1
    compensation_coeff = 1.1
    heights = dict(zip(tuberack.wells()[:1], [mm_height]))

    def h_track(vol, tube):
        nonlocal heights

        # calculate height decrement based on volume
        dh = ((math.pi*((tube.diameter/2)**2))/vol)*compensation_coeff

        # make sure height decrement will not crash into the bottom of the tube
        h = heights[tube] - dh if heights[tube] - dh > min_h else min_h
        heights[tube] = h
        return h

    # Set Temperature to 8C
    temp_mod.set_temperature(temperature)

    # Transfer Reagent to Tubes
    p1000.pick_up_tip()
    for d_tube in dest_tubes.wells():
        h = h_track(60, tuberack['A1'])
        p1000.transfer(volume, tuberack['A1'].bottom(h), d_tube,
                       new_tip='never')
    p1000.drop_tip()
