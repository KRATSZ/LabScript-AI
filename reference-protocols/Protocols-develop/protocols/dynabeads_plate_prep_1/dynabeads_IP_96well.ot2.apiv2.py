"""PROTOCOL."""
metadata = {
    'protocolName': 'Dynabeads for IP Reagent-In-Plate Plate Prep 1',
    'author': '',
    'source': '',
    'apiLevel': '2.11'
            }


def run(ctx):
    """PROTOCOL."""

    [num_samples] = get_values(  # noqa: F821
        'num_samples')

    total_cols = int(num_samples//8)
    r1 = int(num_samples % 8)
    if r1 != 0:
        total_cols = total_cols + 1

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
    beads = reagent_plate.columns()[0]
    ab = reagent_plate.columns()[1]
    beads_stock = reagent_tube.rows()[0][0]
    ab_stock = reagent_tube.rows()[0][1]

    # protocol

    ctx.comment('\n\n\n~~~~~~~~MIXING AND TRANSFER BEADS ~~~~~~~~\n')
    pip_single.pick_up_tip()
    for i in range(total_cols):
        h = 5 + i * 3
        pip_single.mix(5, 250, beads_stock.bottom(z=h), rate=5)
    for i in range(8):
        pip_single.transfer(total_cols*50,
                            beads_stock,
                            beads[i],
                            blow_out=True,
                            blowout_location='destination well',
                            new_tip='never',
                            mix_before=(5, 100),
                            )
    pip_single.drop_tip()
    ctx.comment('\n\n\n~~~~~~~~TRANSFER AB ~~~~~~~~\n')
    pip_single.pick_up_tip()
    for i in range(8):
        pip_single.transfer(total_cols*50,
                            ab_stock,
                            ab[i],
                            blow_out=True,
                            blowout_location='destination well',
                            new_tip='never',
                            )
    pip_single.drop_tip()
