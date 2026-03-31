"""Protocol."""
import math
metadata = {
    'protocolName': 'Plate Filling Heat Inactivated Covid Samples for PCR - Part 2',  # noqa: E501
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [num_samp, m20_mount] = get_values(  # noqa: F821
        'num_samp', 'm20_mount')

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a number of samples between 1-96")

    if not num_samp % 8 == 0:
        raise Exception("Enter a number of samples which is divisible by 8")

    num_col = math.ceil(num_samp/8)

    # load labware
    source_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '1')
    final_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '2')
    tiprack = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
               for slot in ['3']]

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tiprack)

    # protocol
    # distribute to inter plate
    airgap = 2
    for s, d in zip(source_plate.rows()[0], final_plate.rows()[0][:num_col]):
        m20.pick_up_tip()
        m20.aspirate(6, s)
        m20.touch_tip()
        m20.air_gap(airgap)
        m20.dispense(airgap, d.top())
        m20.dispense(6, d)
        m20.blow_out()
        m20.drop_tip()
