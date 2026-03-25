"""Protocol."""
import math

metadata = {
    'protocolName': 'Extraction Prep for TaqPath Covid-19 Combo Kit',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [num_samp, p1000_sample_height,
        plate_height, p1000_mount] = get_values(  # noqa: F821
        "num_samp", "p1000_sample_height", "plate_height", "p1000_mount")

    if not 1 <= num_samp <= 95:
        raise Exception("Enter a sample number between 1-95")

    num_samp = num_samp+1

    # load labware
    samples = [ctx.load_labware('opentrons_15_tuberack_5000ul', slot)
               for slot in ['1', '4', '7', '10', '2', '5', '8', '11']]
    sample_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '3',
                                    label='Sample plate')
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '6')]

    # load instrument
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack1000)

    # PROTOCOL

    # reagents
    sample_map_left = [tube for i, tuberack in enumerate(
                        samples[:4]*len(samples[0].columns()))
                       for col in
                       tuberack.columns()[math.floor(i/4):math.floor(i/4)+1]
                       for tube in col[::-1]]
    sample_map_right = [tube for i, tuberack in enumerate(
                        samples[4:]*len(samples[0].columns()))
                        for col in
                        tuberack.columns()[math.floor(i/4):math.floor(i/4)+1]
                        for tube in col[::-1]]

    plate_map = [well for row in sample_plate.rows()
                 for well in row][:num_samp-1]

    # add patient samples
    samp_ctr = 0
    for i, well in enumerate(plate_map):
        sample_map = sample_map_left if i < 60 else sample_map_right
        p1000.pick_up_tip()
        p1000.aspirate(200, sample_map[samp_ctr].bottom(z=p1000_sample_height))
        p1000.touch_tip()
        p1000.dispense(200, well.bottom(z=plate_height))
        p1000.blow_out()
        p1000.drop_tip()
        samp_ctr += 1
        if samp_ctr == 60:
            samp_ctr = 0
            ctx.comment('\n')
