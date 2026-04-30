metadata = {
    'title': 'Custom Tiprack Reformatting',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [box_count] = get_values(  # noqa: F821
        "box_count")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    """
    This script puts tips into a custom arrangement required
    for use of a multi-channel pipette with only four tips attached
    (on alternating nozzles).
    """
    # p300 multi, full tip boxes, empty tip boxes
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', str(
     slot), 'FULL TIPRACK') for slot in [7, 8, 9][:int(box_count / 2)]]
    p300m = ctx.load_instrument("p300_multi_gen2", 'right', tip_racks=tips300)

    empty300 = [ctx.load_labware('opentrons_96_tiprack_300ul', str(
     slot), 'EMPTY TIPRACK') for slot in [4, 5, 6][:int(box_count / 2)]]

    for full, empty in zip(tips300, empty300):
        for index, column in enumerate(full.columns()):
            p300m.pick_up_tip(column[4])
            p300m.drop_tip(empty.columns()[index][4])

    for box in tips300+empty300:
        for column in box.columns():
            if box in empty300:
                p300m.pick_up_tip(column[4])
                p300m.drop_tip(column[0])
            for s in range(1, 6, 2):
                p300m.pick_up_tip(column[s])
                p300m.drop_tip(column[s+1])
