import math

metadata = {
    'protocolName': 'ELISA: Dilution',
    'author': 'Alise <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.14'
}


def run(ctx):
    [number_of_standards,
     concentration_csv, init_vol_buff] = get_values(  # noqa: F821
     'number_of_standards',
     'concentration_csv', "init_vol_buff")

    # labware setup
    tuberack_1 = ctx.load_labware(
        'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', '1')
    tuberack_4 = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '4')
    deep_plates = [ctx.load_labware('nest_96_wellplate_2ml_deep', slot)
                   for slot in ['5', '6']]

    tiprack_1000 = ctx.load_labware('opentrons_96_tiprack_1000ul', '2')
    tipracks_300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                    for slot in ['3', '7']]

    # instrument setup
    p1000 = ctx.load_instrument(
        'p1000_single',
        mount='left',
        tip_racks=[tiprack_1000])
    p300 = ctx.load_instrument(
        'p300_single',
        mount='right',
        tip_racks=tipracks_300)

    # reagent setup
    tubes = [well for row in tuberack_4.rows() for well in row]
    samples = tubes[2 + number_of_standards:]
    dilution_buffer = tuberack_1.wells_by_name()['A3']

    v_naught_buff = init_vol_buff*1000

    radius_sds = dilution_buffer.diameter/2

    h_naught_buff = 0.85*v_naught_buff/(math.pi*radius_sds**2)

    h_buff = h_naught_buff

    def adjust_height(volume_from_loop):
        nonlocal h_buff

        radius = radius_sds

        dh = (volume_from_loop/(math.pi*radius**2))*1.33

        h_buff -= dh

        if h_buff < 12:
            h_buff = 1

    dil_dests = [row for deep_plate in deep_plates
                 for row in deep_plate.rows()]

    conc_lists = [[int(cell) for cell in line.split(',') if cell]
                  for line in concentration_csv.splitlines() if line]

    concs = [5, 10, 25, 50, 100, 500, 1000, 5000, 10000, 25000, 50000, 100000]

    diluent_vols = [320, 450, 180, 320, 450, 320, 450, 320, 450, 180, 320, 450]

    sample_vols = [80, 50, 120, 80, 50, 80, 50, 80, 50, 120, 80, 50]

    concs_init = [1, 1, 10, 10, 10, 100, 100, 1000, 1000, 10000, 10000, 10000]
    dil_formulae = {
        conc: {'diluent_vol': diluent_vol,
               'sample_vol': sample_vol,
               'conc_init': conc_init,
               'col_index': index}
        for conc, diluent_vol, sample_vol, conc_init, index in zip(
            concs, diluent_vols, sample_vols, concs_init, range(12))
        }

    dilution_concs = []
    for sample_index, concentrations in enumerate(conc_lists):
        new_concs = []
        factors = [10, 100, 1000, 10000, 100000]
        conc_inspect = max(concentrations)

        for factor_index, factor in enumerate(factors):
            if (conc_inspect // factor) > 0 and (conc_inspect // factor) < 10:
                [new_concs.append(factors[:factor_index+1])]
                [concentrations.pop(concentrations.index(num))
                 for num in factors[:factor_index+1] if num in concentrations]
                [new_concs.append([conc_inspect])
                 if conc_inspect not in new_concs[0] else '']
                [concentrations.pop(concentrations.index(conc_inspect))
                 if conc_inspect in concentrations else '']
        [new_concs.append([conc]) for conc in concentrations if concentrations]
        dilution_concs.append(new_concs)

    # transfer dilution buffer

    for sample_index, (row, concs) in enumerate(
            zip(dil_dests, dilution_concs)):
        volumes = [dil_formulae[conc]['diluent_vol']
                   for c_list in concs for conc in c_list]
        dests = [row[dil_formulae[conc]['col_index']]
                 for c_list in concs for conc in c_list]
        for volume, dest in zip(volumes, dests):
            p1000.pick_up_tip()
            p1000.transfer(
                volume,
                dilution_buffer.bottom(z=h_buff),
                dest.top(-20),
                new_tip='never')

            adjust_height(volume)
            p1000.blow_out(dest.top())
            p1000.drop_tip()

    # transfer samples
    for sample_index, (row, concs) in enumerate(
            zip(dil_dests, dilution_concs)):
        for c_list in concs:
            volumes = [dil_formulae[conc]['sample_vol'] for conc in c_list]
            sources = []
            for conc in c_list:
                if dil_formulae[conc]['conc_init'] == 1:
                    sources.append(samples[sample_index])
                else:
                    source_conc = dil_formulae[conc]['conc_init']
                    sources.append(
                        row[dil_formulae[source_conc]['col_index']])
            dests = [row[dil_formulae[conc]['col_index']]
                     for conc in c_list]
            p300.pick_up_tip()
            for volume, source, dest in zip(volumes, sources, dests):
                p300.transfer(volume, source, dest.bottom(2), new_tip='never')
                p300.mix(3, 200, dest.bottom(2))
            p300.drop_tip()
