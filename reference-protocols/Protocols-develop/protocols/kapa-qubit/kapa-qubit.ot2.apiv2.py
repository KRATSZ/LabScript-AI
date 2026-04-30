metadata = {
    'protocolName': 'Kapa Qubit',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_col, m20_mount, m300_mount] = get_values(  # noqa: F821
        "num_col", "m20_mount", "m300_mount")

    # num_col = 3
    # m300_mount = 'left'
    # m20_mount = 'right'

    # labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 3)
    dest_plate = ctx.load_labware('agilent_96_wellplate_270ul', 2)
    source_plate = ctx.load_labware('agilent_96_wellplate_270ul', 1)
    tips200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in [7]]
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in [9]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips200)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)

    # mapping
    buffer = reservoir['A1']
    standard1 = source_plate['A11']
    standard2 = source_plate['A12']
    sample_cols_source = source_plate.rows()[0][:num_col]
    sample_cols_dest = dest_plate.rows()[0][2:2+num_col]

    # transfer buffer to column 1 2 and sample columns
    m300.pick_up_tip()
    for col in dest_plate.rows()[0][:2]:
        m300.aspirate(190, buffer)
        m300.dispense(190, col)
    ctx.comment('\n\n')

    for col in sample_cols_dest:
        m300.aspirate(198, buffer)
        m300.dispense(198, col)
    m300.drop_tip()
    ctx.comment('\n\n')

    # transfer standards
    for standard, col in zip([standard1, standard2], dest_plate.rows()[0][:2]):
        m20.pick_up_tip()
        m20.aspirate(10, standard)
        m20.dispense(10, col)
        m20.mix(5, 20, col)
        m20.blow_out()
        m20.drop_tip()

    ctx.comment('\n\n')
    for s, d in zip(sample_cols_source, sample_cols_dest):
        m20.pick_up_tip()
        m20.aspirate(2, s)
        m20.dispense(2, d)
        m20.mix(5, 20, d)
        m20.blow_out()
        m20.drop_tip()
