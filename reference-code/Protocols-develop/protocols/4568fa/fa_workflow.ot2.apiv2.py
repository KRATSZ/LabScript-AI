metadata = {
    'protocolName': 'FA Workflow',
    'author': 'Nick <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}

TEST_MODE = False


def run(ctx):

    [dil_csv_1, desired_conc, tube_type, rna_starting_format, dil_plate_type,
     fill_plate_blank, fill_second_plate, p300_mount,
     p20_mount] = get_values(  # noqa: F821
        'dil_csv_1', 'desired_conc', 'tube_type', 'rna_starting_format',
        'dil_plate_type', 'fill_plate_blank', 'fill_second_plate',
        'p300_mount', 'p20_mount')

    if TEST_MODE:
        mix_reps = 1
    else:
        mix_reps = 10

    tempdeck1 = ctx.load_module('temperature module gen2', '1')
    # tempdeck1.set_temperature(4)
    dil_plate_final = ctx.load_labware(
        'microampenduraplate_96_aluminumblock_200ul', '3', 'final plate')
    dil_plate_1 = ctx.load_labware(dil_plate_type, '2', 'dilution plate 1')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '9',
                                 'reagent reservoir')
    tempdeck2 = ctx.load_module('temperature module gen2', '10')
    # tempdeck2.set_temperature(70)
    if rna_starting_format == 'tubes':
        tuberacks = [
            ctx.load_labware(tube_type, slot, f'tuberack {i+1}')
            for i, slot in enumerate(['5', '6'])]
        sample_sources = [
            well for tuberack in tuberacks for well in tuberack.wells()]
    else:
        tuberacks = [ctx.load_labware(tube_type, '6', 'tuberack')]
        sample_plate = tempdeck1.load_labware(rna_starting_format,
                                              'sample sources')
        sample_sources = sample_plate.wells()

    tipracks200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['4', '7']]
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['8', '11']]

    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tipracks200)
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tipracks20)

    water = reservoir.wells()[0]
    blank_solution = reservoir.wells()[1]
    # hs_dil = tuberacks[-1].columns()[-1][1:]
    hs_dil = reservoir.wells()[2]
    rinse_buffer = reservoir.wells()[10:]

    data = [
        [val.strip() for val in line.split(',')]
        for line in dil_csv_1.splitlines()
        if line and line.split(',')[0].strip()][1:]
    num_samples = len(data)

    # dilute 2x to 4µg/ml
    dils_1 = dil_plate_1.wells()[:num_samples]
    dils_2 = dil_plate_1.wells()[48:48+num_samples]  # use half of plate

    # pre-allocate water for dilution to 100µg/ml
    ctx.home()
    ctx.pause('Ensure temperature module on slot 10 is set to 70C and \
temperature module on slot 1 is set to 4C. If not, please cancel run, set \
these temperatures, and run protocol again once these temperatures are \
reached.')
    p300.pick_up_tip()
    for dil, line in zip(dils_1, data):
        sample_name = line[1]
        conc = float(line[2])
        if conc < 0.25:
            raise Exception(f'Sample {sample_name} below allowable \
concentration of 0.25mg/ml.')
        sample_vol = 10/conc
        dil_1_vol = 100 - sample_vol
        p300.transfer(dil_1_vol, water, dil, new_tip='never')

    # pre-allocate water for final desired dilution
    for well in dils_2:
        p300.transfer(100-desired_conc, water, well, new_tip='never')
    p300.drop_tip()

    # perform dilutions
    for sample, dil1, dil2, line in zip(sample_sources, dils_1, dils_2, data):
        conc = float(line[2])
        sample_vol = 10/conc
        p20.pick_up_tip()
        p20.flow_rate.aspirate = 10
        p20.flow_rate.dispense = 10
        p20.mix(mix_reps, 20, sample)
        p20.flow_rate.aspirate = 3.78
        p20.flow_rate.dispense = 7.56
        p20.transfer(sample_vol, sample, dil1, new_tip='never')
        p20.drop_tip()

    p300.flow_rate.aspirate = 100
    p300.flow_rate.dispense = 150
    for dil1 in dils_1:
        p300.pick_up_tip()
        p300.mix(mix_reps, 80, dil1)
        p300.drop_tip()
    p300.flow_rate.aspirate = 46.43
    p300.flow_rate.dispense = 92.86

    for sample, dil1, dil2, line in zip(sample_sources, dils_1, dils_2, data):
        p20.pick_up_tip()
        p20.transfer(desired_conc, dil1, dil2, new_tip='never')
        p20.drop_tip()

    p300.flow_rate.aspirate = 100
    p300.flow_rate.dispense = 150
    for dil2 in dils_2:
        p300.pick_up_tip()
        p300.mix(mix_reps, 80, dil2)
        p300.drop_tip()
    p300.flow_rate.aspirate = 46.43
    p300.flow_rate.dispense = 92.86

    # determine transfer scheme depending on number of samples
    if 1 <= num_samples <= 15:
        dests = dil_plate_final.rows_by_name()['A'] + [
            dil_plate_final.wells_by_name()[well]
            for well in ['D1', 'D4', 'D7']]
        dests = dests[:num_samples]
        triplicates = [col[:3] for col in dil_plate_final.columns()] + [
            dil_plate_final.rows_by_name()['D'][i*3:(i+1)*3] for i in range(3)]
        triplicate_sets = triplicates[:num_samples]
        dils_final = dests[:num_samples]
        final_dest = dil_plate_final.wells_by_name()['D12']
        # final_set = dil_plate_final.rows_by_name()['D'][9:]
        blank_wells = [
            well for well in [
                well for row in dil_plate_final.rows()[:4] for well in row]
            if well not in [
                well for set in [*triplicate_sets, *[[final_dest]]]
                for well in set]]

    elif 15 < num_samples <= 31:
        dests = dil_plate_final.rows_by_name()['A'] + \
                    dil_plate_final.rows_by_name()['D'] + [
                    dil_plate_final.wells_by_name()[well]
                    for well in ['G1', 'G4', 'G7', 'G10', 'H1', 'H4', 'H7']]
        dests = dests[:num_samples]
        triplicates = [col[:3] for col in dil_plate_final.columns()] + [
            col[3:6] for col in dil_plate_final.columns()] + [
            dil_plate_final.rows_by_name()['G'][i*3:(i+1)*3]
                for i in range(4)] + [
            dil_plate_final.rows_by_name()['H'][i*3:(i+1)*3] for i in range(3)]
        triplicate_sets = triplicates[:num_samples]
        dils_final = dests[:num_samples]
        final_dest = dil_plate_final.wells_by_name()['H12']
        # final_set = dil_plate_final.rows_by_name()['H'][9:]
        blank_wells = [
            well for well in dil_plate_final.wells()
            if well not in [
                well for set in [*triplicate_sets, *[[final_dest]]]
                for well in set]]
    else:
        raise Exception(f'Invalid number of samples given ({num_samples}). \
Must be 1-31 samples.')

    if num_samples > 15 or fill_plate_blank:
        blank_wells = [
            well for well in dil_plate_final.wells()
            if well not in [
                well for set in [*triplicate_sets, *[[final_dest]]]
                for well in set]]
    else:
        blank_wells = [
            well for well in [
                well for row in dil_plate_final.rows()[:4] for well in row]
            if well not in [
                well for set in [*triplicate_sets, *[[final_dest]]]
                for well in set]]

    # pre-add HS diluent
    p300.pick_up_tip()
    for i, d in enumerate(dests):
        p300.aspirate(135, hs_dil.bottom(1))
        # p300.touch_tip(hs_dil[i//11])
        p300.dispense(135, d.bottom(3))
    p300.aspirate(27, hs_dil.bottom(1))
    # p300.touch_tip(hs_dil[0])
    p300.dispense(27, final_dest.bottom(3))
    p300.drop_tip()

    # transfer sample
    for s, d in zip(dils_2, dils_final):
        p20.transfer(15, s, d.bottom(3))

    # transfer RNA ladder
    # p20.transfer(3, rna_ladder, final_dest)
    final_well_display = final_dest.display_name.split(' ')[0]
    ctx.pause(f'Add 3ul RNA ladder to well {final_well_display}')

    # mix all samples with diluent
    p300.flow_rate.aspirate = 100
    p300.flow_rate.dispense = 150
    for set in triplicate_sets:
        p300.pick_up_tip()
        p300.mix(mix_reps, 120, set[0].bottom(3))
        # # transfer triplicates
        # p300.transfer(50, set[0].bottom(3),
        #               [well.bottom(3) for well in set[1:]], new_tip='never')
        p300.drop_tip()

    # mix RNA ladder with diluent
    p300.pick_up_tip()
    p300.mix(mix_reps, 20, final_dest.bottom(2))
    p300.drop_tip()
    p300.flow_rate.aspirate = 46.43
    p300.flow_rate.dispense = 92.86

    # heat samples
    ctx.pause('Seal the plate in slot 3 and place on the temperature module on \
slot 10. Resume when finished.')
    p300.home()
    if not TEST_MODE:
        ctx.delay(minutes=2)
    p300.home()
    ctx.pause('Move the plate from temperature module on slot 10 to temperature \
module on slot 1.')
    if not TEST_MODE:
        ctx.delay(minutes=5)
    p300.home()
    [td.deactivate() for td in [tempdeck1, tempdeck2]]
    ctx.pause('Centrifuge the plate on temperature module on slot 1. Replace \
on temperature module on slot 3 and remove plate seal when complete.')

    # transfer triplicates
    for set in triplicate_sets:
        p300.pick_up_tip()
        p300.mix(mix_reps, 50, set[0].bottom(3))
        p300.transfer(50, set[0].bottom(3),
                      [well.bottom(3) for well in set[1:]], new_tip='never')
        p300.drop_tip()

    # transfer blank solution to blank wells
    p300.transfer(50, blank_solution, [b.bottom(3) for b in blank_wells])

    # fill second plate if selected
    if fill_second_plate:
        ctx.pause('Plate on slot 3 is complete. Remove and place second clean \
plate on aluminum block on slot 3 for full-plate buffer addition.')
        p300.pick_up_tip()
        for i, well in enumerate(dil_plate_final.wells()):
            p300.transfer(200, rinse_buffer[i//48], well,
                          new_tip='never')
        p300.drop_tip()
