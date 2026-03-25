metadata = {
    'apiLevel': '2.0',
    'protocolName': 'Ammonia ytrium dilution',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
}


def run(ctx):

    i_vol = get_values(  # noqa: F821
            'init_vol')[0]
    tip_racks = [
        ctx.load_labware(
            'opentrons_96_filtertiprack_20ul',
            x) for x in [
            "7",
            "8"]]
    p20s = ctx.load_instrument(
        'p20_single_gen2',
        'right',
        tip_racks=tip_racks)
    ammonia = ctx.load_labware(
        "opentrons_6_tuberack_falcon_50ml_conical",
        '9').wells_by_name()["A1"]
    ytrium_plate = ctx.load_labware(
        "96wellplatemountedcappshaker_96_wellplate_360ul", '1')
    output_plate = ctx.load_labware("leo_99_wellplate_50ul", '3')

    def height_offset(vol_used, init_vol=i_vol):
        liquid_top = init_vol * 2
        # 1mm per 2ml
        if vol_used == 0:
            return liquid_top
        offset = vol_used / 2000
        if offset > liquid_top:
            ctx.comment("WARNING: Not enough liquid in 50ml tube")
            return 1
        return liquid_top - offset

    vol_used = 0

    for i, well in enumerate(ytrium_plate.wells()):
        output_well = output_plate.wells()[i]
        p20s.transfer(
            10,
            ammonia.bottom(
                height_offset(vol_used)),
            output_well,
            new_tip='always')
        vol_used += 10
        p20s.transfer(
            5, well, output_well, mix_after=(
                1, 10), new_tip='always')
