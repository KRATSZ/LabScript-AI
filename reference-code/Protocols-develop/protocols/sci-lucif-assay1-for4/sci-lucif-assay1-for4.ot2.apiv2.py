# flake8: noqa

metadata = {
    'protocolName': 'Luciferase Reporter Assay for NF-kB Activation (up to 4 plates) - Protocol 1: Cell Culture Preparation',
    'author': 'Boren Lin, Opentrons',
    'description': 'The protocol performs liquid handling to prepare up to four 96-well plates of mammalian cells for luciferase reporter assay.',
    'apiLevel': '2.13'
}

PLATE_SLOT = [2, 5, 8, 11]
TOTAL_COL = 12

CELL_VOL =100

def run(ctx):

    [TOTAL_PLATE, m300_mount] = get_values(  # noqa: F821
        "TOTAL_PLATE", "m300_mount")

    # labware
    cell_stock = ctx.load_labware('nest_12_reservoir_15ml', 6, 'cell stock')
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', 3)
    p300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=[tiprack])

    cells_source = cell_stock.wells()[:TOTAL_PLATE]

    #protocol

    for x in range(TOTAL_PLATE):
        working_plate = ctx.load_labware('corning_96_wellplate_360ul_flat', PLATE_SLOT[x])
        cells_all = working_plate.rows()[0][:TOTAL_COL]

        ctx.comment('\n\n\n~~~~~~~~TRANSFER CELLS~~~~~~~~\n')
        p300.pick_up_tip()
        start = cells_source[x]
        p300.mix(5, 250, start.bottom(z=5), rate = 0.75)
        p300.mix(5, 250, start.bottom(z=2), rate = 0.75)

        for i in range(TOTAL_COL):
            p300.mix(2, CELL_VOL, start.bottom(z=1), rate = 0.75)
            p300.aspirate(CELL_VOL, start.bottom(z=0.5), rate = 0.5)
            p300.air_gap(20)
            end = cells_all[i]
            p300.dispense(CELL_VOL+20, end.top(z=-2), rate = 0.75)
            p300.blow_out()
            p300.touch_tip()
        p300.drop_tip()
