import math

metadata = {
    'protocolName': 'Phytip Protein A, ProPlus, ProPlus LX Columns - \
Neutralization',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


# for Elution buffer 80 uL, add Neutralization buffer 20 uL;
# for Elution buffer 100 uL, add Neutralization buffer 25 uL


def run(ctx):

    num_samples, vol_neutralization_buffer = get_values(  # noqa: F821
        'num_samples', 'vol_neutralization_buffer')

    num_cols = math.ceil(num_samples/8)

    tiprack = ctx.load_labware(
        'opentrons_96_tiprack_300ul', '6', '300ul opentrons tiprack')

    elution_plate = ctx.load_labware(
        'thermoscientific_96_wellplate_v_450', '11', 'elute plate')
    tuberack = ctx.load_labware(
        'opentrons_15_tuberack_nest_15ml_conical', '10', 'elution buffer')

    neutral_buffer = tuberack.rows()[0][4]

    s300 = ctx.load_instrument(
        'p300_single_gen2', 'right', tip_racks=[tiprack])

    # neutralization)
    s300.pick_up_tip()
    for col in range(num_cols):
        s300.blow_out(neutral_buffer)
        s300.aspirate(vol_neutralization_buffer*9, neutral_buffer, rate=0.5)
        for i in range(8):
            well = elution_plate.rows()[i][col]
            s300.dispense(vol_neutralization_buffer, well.top(1), rate=0.5)
            s300.touch_tip()
    s300.drop_tip()
