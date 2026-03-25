import math
metadata = {'apiLevel': '2.5'}


def run(ctx):

    num_samples, tip_start = get_values(  # noqa: F821
            'num_samples', 'tip_start')
    column_count = math.ceil(num_samples / 8)

    p20m_racks = [
        ctx.load_labware(
            "opentrons_96_filtertiprack_20ul",
            x) for x in [
            "1",
            "2",
            "3"]]
    p20m = ctx.load_instrument(
        'p20_multi_gen2',
        'right',
        tip_racks=p20m_racks)

    biorad_96_well = ctx.load_labware(
        "opentrons_96_aluminumblock_biorad_wellplate_200ul", "4")
    b_cols = biorad_96_well.rows()[0][:column_count]
    applied_biosystems = ctx.load_labware(
            "{}{}".format("appliedbiosystemsmicroampoptical384",
                          "wellreactionplatewithbarcode_384_wellplate_30ul"),
            "5")

    p20m.starting_tip = p20m_racks[0].well(tip_start)

    applied_wells = [item for sublist in [[[applied_biosystems.wells_by_name()["{}{}".format(a, b + (x * 3))] for b in range(1, 4)] for a in ["A", "B"]] for x in range(0, 6)] for item in sublist]  # noqa: E501
    p20m.transfer(
        2,
        b_cols[0],
        applied_biosystems.wells_by_name()["B1"],
        new_tip="always")
    for col, target_wells in zip(b_cols, applied_wells):
        p20m.pick_up_tip()
        p20m.aspirate(4.5, col)  # Get extra for nice dead volume
        for target_well_num in range(0, 2):
            p20m.dispense(2, target_wells[target_well_num])
        p20m.drop_tip()
        p20m.transfer(2, col, target_wells[2], new_tip="always")
