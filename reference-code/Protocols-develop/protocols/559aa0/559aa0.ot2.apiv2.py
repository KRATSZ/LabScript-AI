metadata = {
    'protocolName': 'PCR/qPCR prep: distribute primers to 384 well plates',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [samp_col_counts, plate_count, labware_384_well_plate, n1_col, n2_col,
     rp_col, ntc_col, primer_volume, disposal_vol, include_ntc, include_multi
     ] = get_values(  # noqa: F821
      'samp_col_counts', 'plate_count', 'labware_384_well_plate', 'n1_col',
      'n2_col', 'rp_col', 'ntc_col', 'primer_volume', 'disposal_vol',
      'include_ntc', 'include_multi')

    ctx.set_rail_lights(True)

    # a samp_col_count value between 1-12 specified for each 384-well plate
    if len(samp_col_counts.split(',')) != plate_count:
        raise Exception('''A count of patient sample columns (between 1 and 12,
        for downstream steps) must be specified for each 384-well plate.''')

    for num in samp_col_counts.split(','):
        if (int(num) < 1) or (int(num) > 12):
            raise Exception('''Invalid number of sample columns specified (
                               expected value between 1 and 12).''')

    # patient sample column count (in downstream steps) for each 384-well plate
    col_counts = samp_col_counts.split(',')

    # p20 multi channel, tips
    tips20 = [
     ctx.load_labware(
      "opentrons_96_filtertiprack_20ul", slot) for slot in [9]]

    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'right', tip_racks=tips20)

    # source and destination plates
    one_ml_plate = ctx.load_labware("nunc_96_wellplate_1000ul", '8')

    available_slots = [
     str(slot) for slot in [*range(1, 12)] if ctx.deck[slot] is None]
    plates = [ctx.load_labware(
     labware_384_well_plate, slot) for slot in available_slots[:plate_count]]

    # optional single or multi dispenses
    if include_multi:
        multi = 2
    else:
        multi = 1

    # define pipetting steps
    def primer_transfer():
        p20m.pick_up_tip()
        for i, plate in enumerate(plates):
            col_count = int(col_counts[i])*2
            vol_in_tip = 0
            for index, column in enumerate(plate.columns()[:col_count]):
                if index % 2 == mod:
                    if vol_in_tip < primer_volume:
                        p20m.blow_out(
                         one_ml_plate.columns_by_name()[str(col)][0].bottom())
                        vol_in_tip = 0
                        p20m.aspirate(
                         (multi*primer_volume) + disposal_vol,
                         one_ml_plate.columns_by_name()[str(col)][0])
                        vol_in_tip += ((multi*primer_volume) + disposal_vol)
                    p20m.dispense(primer_volume, column[well])
                    vol_in_tip -= primer_volume
        p20m.drop_tip()

    # distribute primers (optionally skipping no-template control primer)
    if include_ntc:
        for mod, col, well in zip(
         [0, 0, 1, 1], [n1_col, rp_col, n2_col, ntc_col], [0, 1, 0, 1]):
            primer_transfer()
    else:
        for mod, col, well in zip(
         [0, 0, 1], [n1_col, rp_col, n2_col], [0, 1, 0]):
            primer_transfer()
