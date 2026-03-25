import math

# metadata
metadata = {
    'protocolName': 'Nucleic Acid Purification and PCR Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    num_samples, mix_csv, p20_mount, p300_mount = get_values(  # noqa: F821
        'num_samples', 'mix_csv', 'p20_mount', 'p300_mount')
    # num_samples, p20_mount, p300_mount, mix_csv = [
    #     96, 'left', 'right',
    #     'mix tube,PCR plate start well,PCR plate end well\nA1,A1,H2\nB1,A3,\
    #     H6\nC1,A7,H8\nD1,A9,H12']

    if num_samples < 1 or num_samples > 96:
        raise Exception('Invalid number of samples (must be 1-96).')
    if p20_mount == p300_mount:
        raise Exception('Pipette mounts cannot match.')

    # load labware and modules
    res12 = ctx.load_labware(
        'usascientific_12_reservoir_22ml', '1', 'reagent reservoir')
    tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '2')]
    tipracks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['3', '6', '9']
    ]
    cuvette_racks = [
        ctx.load_labware(
            'greinerbioone_24_bloodrack_13x100',
            slot, 'blood sample rack ' + str(i+1))
        for i, slot in enumerate(['4', '5', '7', '8'])
    ]
    tempdeck = ctx.load_module('tempdeck', '10')
    tempdeck.set_temperature(50)
    temp_plate = tempdeck.load_labware(
        'biozym_96_aluminumblock_200ul', 'PCR plate')
    pcr_mix_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '11', 'PCR mix tube rack')

    # pipettes
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_mount, tip_racks=tiprack20)
    m300 = ctx.load_instrument(
        'p300_multi', p300_mount, tip_racks=tipracks300)

    # setup
    cuvettes = [
        cuv for rack in cuvette_racks for cuv in rack.wells()][:num_samples]
    samples20 = temp_plate.wells()[:num_samples]
    samples300 = temp_plate.rows()[0][:math.ceil(num_samples/8)]
    conc_dil = res12.wells()[0]
    buffer_b = res12.wells()[1]
    buffer_c = res12.wells()[2:5]
    liq_waste = [chan.top(2) for chan in res12.wells()[8:]]
    pcr_mix_sources = [
        line.split(',')[0].strip().upper()
        for line in mix_csv.splitlines()[1:] if line]
    mix_dest_sets = [
        [val.strip().upper() for val in line.split(',')[1:3]]
        for line in mix_csv.splitlines()[1:] if line]

    tips20_max = 96*len(tiprack20)
    tips300_max = 12*len(tipracks300)
    tips20_count = 0
    tips300_count = 0

    def pick_up(pip):
        nonlocal tips20_count
        nonlocal tips300_count
        if pip == p20:
            if tips20_count == tips20_max:
                ctx.pause('Replace 20ul tiprack in slot 2 before resuming.')
                p20.reset_tipracks()
            p20.pick_up_tip()
            tips20_count += 1
        else:
            if tips300_count == tips300_max:
                ctx.pause('Replace 300ul tiprack in slots 3, 6, and 9 before \
resuming.')
                m300.reset_tipracks()
            m300.pick_up_tip()
            tips300_count += 1

    # mix and transfer blood samples
    for s, d in zip(cuvettes, samples20):
        pick_up(p20)
        p20.transfer(10, s, d, mix_before=(5, 10), air_gap=5, new_tip='never')
        p20.air_gap(10)
        p20.drop_tip()

    # distribute concentration dilution
    pick_up(m300)
    m300.distribute(
        50, conc_dil, [s.top(2) for s in samples300], new_tip='never')

    ctx.delay(minutes=5, msg='Incubating at 50˚C for 5 minutes.')

    # distribute Buffer B
    if not m300.hw_pipette['has_tip']:
        pick_up(m300)
    m300.distribute(
        100, buffer_b, [s.top(2) for s in samples300], new_tip='never')

    ctx.delay(minutes=5, msg='Incubating at 50˚C for 5 minutes.')

    # remove supernatant from all samples
    for s in samples300:
        if not m300.hw_pipette['has_tip']:
            pick_up(m300)
        m300.transfer(
            170, s.bottom(0.5), liq_waste[0], new_tip='never', air_gap=30)
        m300.blow_out(liq_waste[0])
        m300.drop_tip()

    # transfer Buffer C 3x
    for wash in range(3):
        pick_up(m300)
        m300.transfer(
            200, buffer_c[wash], [s.top(2) for s in samples300],
            new_tip='never', air_gap=30)
        # remove supernatant from all samples
        for s in samples300:
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
            m300.transfer(
                170, s.bottom(0.5), liq_waste[wash+1], new_tip='never',
                air_gap=30)
            m300.blow_out(liq_waste[wash+1])
            m300.drop_tip()

    tempdeck.set_temperature(95)
    ctx.delay(minutes=10, msg='Incubating at 95˚C for 10 minutes.')
    tempdeck.deactivate()

    keys = [k for k in temp_plate.wells_by_name().keys()]

    def parse_destinations(start, end):
        start_ind, end_ind = keys.index(start), keys.index(end) + 1
        return temp_plate.wells()[start_ind:end_ind]

    for s, d_set in zip(pcr_mix_sources, mix_dest_sets):
        source = pcr_mix_rack.wells_by_name()[s]
        pick_up(p20)
        start, end = d_set
        for d in parse_destinations(start, end):
            p20.transfer(8, source, d.top(2), air_gap=5, new_tip='never')
        p20.drop_tip()
