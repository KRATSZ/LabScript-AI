"""PROTOCOL."""
metadata = {
    'protocolName': 'Dynabeads for IP Reagent-In-Plate Plate Prep 2',
    'author': '',
    'source': '',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        'num_samples')

    total_cols = int(num_samples//8)
    r1 = int(num_samples % 8)
    if r1 != 0:
        total_cols = total_cols + 1

    #########################

    """PROTOCOL."""
    # load labware
    reagent_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '4',
                                     'reagents')
    reagent_tube = ctx.load_labware('opentrons_15_tuberack_nest_15ml_conical',
                                    '5', 'reagents - stock')
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', '7')

    # load pipette
    pip_single = ctx.load_instrument('p300_single_gen2', 'right',
                                     tip_racks=[tiprack])

    # liquids
    elution = reagent_plate.columns()[11]
    elution_stock = reagent_tube.rows()[0][4]

    # protocol

    ctx.comment('\n\n\n~~~~~~~~TRANSFER ELUTION BUFFER ~~~~~~~~\n')
    pip_single.pick_up_tip()
    for i in range(8):
        pip_single.transfer(total_cols*30,
                            elution_stock,
                            elution[i],
                            new_tip='never',
                            blow_out=True,
                            blowout_location='destination well',
                            )
    pip_single.drop_tip()
