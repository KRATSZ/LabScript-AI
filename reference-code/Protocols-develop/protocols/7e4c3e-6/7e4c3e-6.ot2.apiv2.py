import math
metadata = {'apiLevel': '2.5'}


def run(ctx):

    num_samples, tip_start_20, tip_start_1000 = get_values(  # noqa: F821
            'num_samples', 'tip_start_20', 'tip_start_1000')
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
    p20m.starting_tip = p20m_racks[0].well(tip_start_20)
    p1000s_rack = ctx.load_labware("opentrons_96_filtertiprack_1000ul", "1")
    p1000s = ctx.load_instrument(
        'p1000_single_gen2',
        'left',
        tip_racks=[p1000s_rack])
    p1000s.starting_tip = p1000s_rack.well(tip_start_1000)

    applied_biosystems_plate = ctx.load_labware(
            "appliedbiosystemsmicroampoptical384wellreactionplatewithbarcode_384_wellplate_30ul",  # noqa: E501
            "6")
    tube_rack = ctx.load_labware(
        "opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap", "4")
    pcr_strip = ctx.load_labware(
        "opentrons_96_aluminumblock_generic_pcr_strip_200ul", "5")

    master_mix_1 = tube_rack.wells_by_name()["A1"]
    master_mix_2 = tube_rack.wells_by_name()["B1"]

    p1000s.transfer(200, master_mix_1, pcr_strip.columns()[0], new_tip="once")
    p1000s.transfer(100.8, master_mix_2, pcr_strip.columns()[1])

    for source_well, target_loc in zip([pcr_strip.wells_by_name()["A1"], pcr_strip.wells_by_name()[  # noqa: E501
            "B1"]], [[1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17][:math.ceil(column_count / 2) * 2], [3, 6, 9, 12, 15, 18][:math.ceil(column_count / 2)]]):  # noqa: E501
        p20m.pick_up_tip()
        for letter in ["A", "B"]:
            for num in target_loc:
                p20m.aspirate(8, source_well)
                p20m.dispense(
                    8, applied_biosystems_plate.wells_by_name()[
                        "{}{}".format(
                            letter, num)])
        p20m.drop_tip()
