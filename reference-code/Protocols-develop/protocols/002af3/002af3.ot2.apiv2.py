metadata = {
        'apiLevel': '2.5',
        'protocolName': 'qPCR 96 well -> 384 well transfer',
        'author': 'Opentrons <protocols@opentrons.com>',
        'source': 'Custom Protocol Request'
        }


def run(ctx):

    column_count = get_values(  # noqa: F821
            'column_count')
    column_count = column_count[0]

    # Change to HARD-SHELL BIO-RAD PCR 384 WELL PLATE 50 UL
    cfx_plate = ctx.load_labware('hardshellbioradpcr_384_wellplate_50ul', '3')
    # THERMO FISHER SCIENTIFIC ELUTION TUBES 96 WELL PLATE 650 UL
    control_plate = ctx.load_labware(
       'thermofisherscientificelutiontubes_96_wellplate_650ul', '2')

    tip_racks = [
        ctx.load_labware(
            'opentrons_96_filtertiprack_20ul',
            x) for x in [
            '7',
            '8',
            '10',
            '11']]
    p20m = ctx.load_instrument(
        'p20_multi_gen2', "right", tip_racks=tip_racks)

    # Sample
    sample_plate_1 = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '1')
    if column_count > 12:
        sample_plate_2 = ctx.load_labware(
            'nest_96_wellplate_2ml_deep', '4')

    cols = []
    for x in range(1, 8):
        for y in ["A", "B"]:
            cols.append([cfx_plate.wells_by_name()[
                        "{}{}".format(y, x + (z * 8))] for z in range(0, 3)])

    if column_count < 12:
        transfers_needed = list(
            zip(sample_plate_1.rows()[0][:column_count],
                cols[:column_count]))
    if column_count > 12:
        transfers_needed = list(
            zip(sample_plate_1.rows()[0][:column_count],
                cols[:column_count])) + list(
            zip(sample_plate_2.rows()[0][:column_count - 12],
                cols[12:(column_count - 12) + 12]))

    for from_well, to_wells in transfers_needed:
        for to_well in to_wells:
            p20m.transfer(5, from_well, to_well, new_tip='always')

    # Controls
    for to_well in [cfx_plate.wells_by_name()[x] for x in ["A8", "A16"]]:
        p20m.transfer(5, control_plate.wells_by_name()[
                      "A1"], to_well, new_tip='always')
    p20m.transfer(
        5,
        control_plate.wells_by_name()["A3"],
        cfx_plate.wells_by_name()["A24"],
        new_tip='always')
