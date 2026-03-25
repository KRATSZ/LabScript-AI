# flake8: noqa

metadata = {
    'protocolName': 'Luciferase Reporter Assay for NF-kB Activation (up to 4 plates) - Protocol 2: Transfection of Luciferase Reporter Construct',
    'author': 'Boren Lin, Opentrons',
    'description': 'The protocol performs liquid handling to conduct transient DNA transfection to develop reporter cells in a 96-well setting for luciferase reporter assay.',
    'apiLevel': '2.13'
}

PLATE_SLOT = [2, 5, 8, 11]
TOTAL_COL = 12

MASTERMIX_VOL = 20


def run(ctx):


    [TOTAL_PLATE, m300_mount] = get_values(  # noqa: F821
        "TOTAL_PLATE", "m300_mount")

    # labware
    mastermix_stock = ctx.load_labware('nest_96_wellplate_2ml_deep', 6, 'master mix')
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', 3)
    p300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=[tiprack])

    mastermix = mastermix_stock.rows()[0][:TOTAL_PLATE]

    #protocol

    for x in range(TOTAL_PLATE):
        working_plate = ctx.load_labware('corning_96_wellplate_360ul_flat', PLATE_SLOT[x])
        cells_all = working_plate.rows()[0][:TOTAL_COL]

        ctx.comment('\n\n\n~~~~~~~~TRANSFER CELLS~~~~~~~~\n')
        p300.pick_up_tip()
        start = mastermix[x]
        p300.mix(5, MASTERMIX_VOL*TOTAL_COL*0.75, start.bottom(z=1), rate = 3)
        for i in range(TOTAL_COL):
            end = cells_all[i]
            p300.aspirate(MASTERMIX_VOL, start.bottom(z=0.2), rate = 0.5)
            p300.air_gap(20)
            p300.dispense(MASTERMIX_VOL+20, end.top(z=-2), rate = 0.75)
            p300.blow_out()
            p300.touch_tip()
        p300.drop_tip()
