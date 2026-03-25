import math
metadata = {'apiLevel': '2.0'}


def run(ctx):

    num_samples, tip_start = get_values(  # noqa: F821
            'num_samples', 'tip_start')
    column_count = math.ceil(num_samples / 8)

    p20m_racks = [
        ctx.load_labware(
            "opentrons_96_filtertiprack_20ul",
            x) for x in [
            "1",
            "2"]]
    p20m = ctx.load_instrument(
        'p20_multi_gen2',
        'right',
        tip_racks=p20m_racks)

    rna = ctx.load_labware(
        "opentrons_96_aluminumblock_biorad_wellplate_200ul", "4")
    cdna = ctx.load_labware(
        "opentrons_96_aluminumblock_biorad_wellplate_200ul", "5")

    p20m.starting_tip = p20m_racks[0].well(tip_start)
    for source_well, target_well in zip(
            rna.rows()[0][:column_count], cdna.rows()[0][:column_count]):
        p20m.transfer(6.2, source_well, target_well)
