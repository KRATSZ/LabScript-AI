# flake8: noqa

from opentrons.types import Point

metadata = {
    'protocolName': 'Luciferase Reporter Assay for NF-kB Activation (up to 4 plates) - Protocol 3: Treatment',
    'author': 'Boren Lin, Opentrons',
    'description': 'The protocol performs liquid handling to apply test articles (e.g., serial dilutions of drug candidates) to the reporter cells cultured in 96-well plates.',
    'apiLevel': '2.13'
}

PLATE_SLOT = [2, 5, 8, 11]
TOTAL_COL = 12

TREAT_PLATE_SLOT = [1, 4, 7, 10]

SUPERNATANT = 120
TREATMENT_VOL = 100

def run(ctx):

    [TOTAL_PLATE, m300_mount] = get_values(  # noqa: F821
        "TOTAL_PLATE", "m300_mount")

    # labware
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', 9, 'waste')
    tiprack_refill = ctx.load_labware('opentrons_96_tiprack_300ul', 3)
    tips_refill_loc = tiprack_refill.rows()[0][:12]
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', 6)
    p300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=[tiprack])

    waste = waste_res.wells()[0]

    #protocol

    for x in range(TOTAL_PLATE):
        working_plate = ctx.load_labware('corning_96_wellplate_360ul_flat', PLATE_SLOT[x])
        treat_plate = ctx.load_labware('corning_96_wellplate_360ul_flat', TREAT_PLATE_SLOT[x])
        cells_all = working_plate.rows()[0][:TOTAL_COL]
        treatment = treat_plate.rows()[0][:TOTAL_COL]

        ctx.comment('\n\n\n~~~~~~~~REMOVE SUPERNATANT~~~~~~~~\n')

        p300.pick_up_tip()
        for i in range(TOTAL_COL):
            start = cells_all[i]
            p300.move_to(start.top(z=-0.2))
            p300.aspirate(SUPERNATANT*1.1, start.bottom(z=0.2).move(Point(x=-2.5)), rate = 0.2)
            p300.dispense(SUPERNATANT*1.1, waste.top(z=-5), rate = 3)
            p300.blow_out
        p300.drop_tip()

        ctx.comment('\n\n\n~~~~~~~~TREAT CELLS~~~~~~~~\n')

        ctx.pause('Place a New Full Tipbox on Slot 3')
        for j in range(TOTAL_COL):
            start = treatment[j]
            end = cells_all[j]
            p300.pick_up_tip(tips_refill_loc[j])
            p300.aspirate(TREATMENT_VOL, start.bottom(z=0.2), rate = 3)
            p300.air_gap(20)
            p300.dispense(TREATMENT_VOL+20, end.top(z=-4), rate = 0.3)
            p300.blow_out()
            p300.touch_tip()
            p300.drop_tip()
