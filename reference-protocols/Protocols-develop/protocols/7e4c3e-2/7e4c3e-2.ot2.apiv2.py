import math
metadata = {'apiLevel': '2.0'}


def run(ctx):

    num_samples, tip_start = [96, "A1"]

    num_samples, tip_start = get_values(  # noqa: F821
            'num_samples', 'tip_start')
    column_count = math.ceil(num_samples / 8)

    p20m_racks = [
        ctx.load_labware(
            "opentrons_96_filtertiprack_20ul",
            x) for x in [
            "2",
            "3"]]
    p20m = ctx.load_instrument(
        'p20_multi_gen2',
        'right',
        tip_racks=p20m_racks)

    biorad_96_well = ctx.load_labware(
        "opentrons_96_aluminumblock_biorad_wellplate_200ul", "4")
    b_cols = biorad_96_well.rows()[0][:column_count]
    pcr_strip = ctx.load_labware(
        "opentrons_96_aluminumblock_generic_pcr_strip_200ul", "5")

    p20m.starting_tip = p20m_racks[0].well(tip_start)
    for cols, target_well in zip([b_cols[:6], b_cols[6:]], [
                                pcr_strip.wells_by_name()[x] for x in ["A1", "A2"]]):  # noqa: E501
        for col in cols:
            p20m.transfer(20, col, target_well)
