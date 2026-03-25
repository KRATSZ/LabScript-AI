from opentrons import types

metadata = {
    'protocolName': 'PCR/qPCR prep: distribute samples to 384 well plates',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # bring in constant values from json string above
    [plate_count, samp_col_counts, labware_384_well_plate,
     labware_patient_samples, patient_sample_vol, disposal_vol,
     patient_sample_count, include_ntc
     ] = get_values(  # noqa: F821
      'plate_count', 'samp_col_counts', 'labware_384_well_plate',
      'labware_patient_samples', 'patient_sample_vol', 'disposal_vol',
      'patient_sample_count', 'include_ntc')

    ctx.set_rail_lights(True)

    # a samp_col_count value between 1-12 specified for each 384-well plate
    if len(samp_col_counts.split(',')) != plate_count:
        raise Exception('''A count of patient sample columns (between 1 and 12)
        must be specified for each 384-well plate.''')

    for num in samp_col_counts.split(','):
        if (int(num) < 1) or (int(num) > 12):
            raise Exception('''Invalid number of sample columns specified
            (must be 1-12).''')

    # patient sample column count for each 384-well plate
    col_counts = samp_col_counts.split(',')

    # tips
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", slot) for slot in [
      str(slot) for slot in [1, 4, 7]][:plate_count]]

    # p20 multi channel
    p20m = ctx.load_instrument(
        "p20_multi_gen2", "right", tip_racks=tips20)

    # source and destination plates
    patient_samples = [
     ctx.load_labware(labware_patient_samples, slot) for slot in [
      str(slot) for slot in [2, 5, 8]][:plate_count]]
    plates_384 = [
     ctx.load_labware(labware_384_well_plate, slot) for slot in [
      str(slot) for slot in [3, 6, 9]][:plate_count]]

    # patient sample column count for each 384-well plate
    col_counts = samp_col_counts.split(',')

    # to optionally skip no-template control
    if include_ntc:
        well_index = 2
    else:
        well_index = 1

    # distribute sample in "384 plate map.png" arrangement
    for i, plate in enumerate(patient_samples):
        # to yield next 384 column
        next_col = (
         column for column in plates_384[i].columns()[:2*int(col_counts[i])])
        for column in patient_samples[i].columns()[:int(col_counts[i])]:
            dest = [
              well.center().move(types.Point(
               well.diameter*0.08, -well.diameter*0.08, 1)) for well in next(
               next_col)[:2]] + [well.center().move(types.Point(
                well.diameter*0.08, -well.diameter*0.08, 1)) for well in next(
                next_col)[:well_index]]
            p20m.distribute(
             patient_sample_vol, [column[0], column[0]], dest,
             disposal_volume=disposal_vol)
