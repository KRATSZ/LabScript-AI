metadata = {'apiLevel': '2.0'}


def run(ctx):

    a1_init_vol, a3_init_vol, a4_init_vol, b3_init_vol, tip_start = get_values(  # noqa: F821, E501
            'a1_init_vol', 'a3_init_vol', 'a4_init_vol', 'b3_init_vol', 'tip_start')  # noqa: E501

    p1000s_rack = ctx.load_labware("opentrons_96_filtertiprack_1000ul", "1")
    p1000s = ctx.load_instrument(
        'p1000_single_gen2',
        'left',
        tip_racks=[p1000s_rack])
    p1000s.starting_tip = p1000s_rack.well(tip_start)

    tube_rack = ctx.load_labware(
        "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", "4")
    tube_a1 = tube_rack.wells_by_name()["A1"]
    tube_a3 = tube_rack.wells_by_name()["A3"]
    tube_a4 = tube_rack.wells_by_name()["A4"]
    tube_b3 = tube_rack.wells_by_name()["B3"]

    deepwell_a1 = ctx.load_labware("nest_96_wellplate_2ml_deep", "6")
    deepwell_a3 = ctx.load_labware("nest_96_wellplate_2ml_deep", "2")
    deepwell_a4 = ctx.load_labware("nest_96_wellplate_2ml_deep", "5")
    deepwell_b3 = ctx.load_labware("nest_96_wellplate_2ml_deep", "3")

    def height_offset(vol_used, tube_type="50ml", init_vol=50):
        if tube_type == "50ml":
            liquid_top = init_vol * 2
            # 1mm per 2ml
            if vol_used == 0:
                return liquid_top
            offset = vol_used / 500
            if offset > liquid_top:
                ctx.comment("WARNING: Not enough liquid in 50ml tube")
                return 1
            return liquid_top - offset
        if tube_type == "15ml":
            liquid_top = init_vol * 7.5
            # 1mm per 2ml
            if vol_used == 0:
                return liquid_top
            offset = vol_used / 133
            if offset > liquid_top:
                ctx.comment("WARNING: Not enough liquid in 15ml tube")
                return 1
            return liquid_top - offset

    for init_vol, tube, tube_type, deepwell, vol in zip(
        [
            a1_init_vol, a3_init_vol, a4_init_vol, b3_init_vol], [
            tube_a1, tube_a3, tube_a4, tube_b3], [
                "15ml", "50ml", "50ml", "50ml"], [
                    deepwell_a1, deepwell_a3, deepwell_a4, deepwell_b3], [
                        50, 245, 200, 200]):
        vol_used = 0
        p1000s.pick_up_tip()
        for well in deepwell.wells():
            p1000s.transfer(
                vol,
                tube.bottom(
                    height_offset(
                        vol_used,
                        tube_type=tube_type,
                        init_vol=init_vol)),
                well,
                new_tip='never')
        p1000s.drop_tip()
