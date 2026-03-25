from opentrons import protocol_api

metadata = {
    'protocolName': 'PCR Prep with Strip Tubes',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [
     _num_col,
     _m20_mount
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "_num_col",
        "_m20_mount")

    # VARIABLES
    num_col = _num_col
    m20_mount = _m20_mount

    if not 1 <= num_col <= 12:
        raise Exception("Enter a column number 1-12")

    # LABWARE
    water = ctx.load_labware('nest_12_reservoir_15ml', '3')
    kappa_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '1')
    dna_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '2')
    primer_num_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '4')
    primer_let_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '5')
    final_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '6')

    # TIPRACKS
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in ['7', '8', '9', '10']]

    # INSTRUMENTS
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)

    # protocol
    cols = final_plate.rows()[0][:num_col]
    ctx.comment('\n\nMOVING WATER TO PLATE\n')
    m20.pick_up_tip()
    m20.distribute(3, water.wells()[0], [col for col in cols], new_tip='never')
    m20.drop_tip()

    ctx.comment('\n\nMOVING KAPPA ENZYME TO PLATE\n')
    m20.pick_up_tip()
    for kappa, col in zip(kappa_plate.rows()[0], cols):
        m20.aspirate(10, kappa)
        m20.dispense(10, col)
        m20.blow_out()
    m20.drop_tip()

    ctx.comment('\n\nMOVING PRIMER NUMBER TO PLATE\n')
    for primer_num, col in zip(primer_num_plate.rows()[0], cols):
        m20.pick_up_tip()
        m20.aspirate(1, primer_num)
        m20.dispense(1, col)
        m20.drop_tip()

    ctx.comment('\n\nMOVING PRIMER LETTER TO PLATE\n')
    for primer_let, col in zip(primer_let_plate.rows()[0], cols):
        m20.pick_up_tip()
        m20.aspirate(1, primer_let)
        m20.dispense(1, col)
        m20.drop_tip()

    ctx.comment('\n\nMOVING DNA TO PLATE\n')
    for dna, col in zip(dna_plate.rows()[0], cols):
        m20.pick_up_tip()
        m20.aspirate(5, dna)
        m20.dispense(5, col)
        m20.drop_tip()
