metadata = {
    'title': 'Syber Green PCR Prep with Cherrypicking',
    'author': 'Nick <ndiehl@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    [input_csv, mm_vol, sample_vol, p20_mount] = get_values(  # noqa: F821
     'input_csv', 'mm_vol', 'sample_vol', 'p20_mount')

    # labware
    pcr_plate = ctx.load_labware('thermofishermicroamp_96_aluminumblock_200ul',
                                 '1', 'final PCR plate')
    source_tubes = ctx.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul', '4',
        'source DNA tubes')
    mm_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2',
        'mastermix rack')
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['3', '6']]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tipracks20)

    # csv parse
    data = [
        [val.strip() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0].strip()]  # check for empty lines

    samples = [source_tubes.wells_by_name()[line[0]] for line in data]
    mms = [mm_rack.wells_by_name()[line[1]] for line in data]
    destinations = [pcr_plate.wells_by_name()[line[2]] for line in data]

    # transfer mm
    for mm, d in zip(mms, destinations):
        p20.pick_up_tip()
        p20.aspirate(mm_vol, mm)
        p20.dispense(mm_vol, d)
        p20.delay(seconds=2)
        p20.drop_tip()

    # transfer sample
    for s, d in zip(samples, destinations):
        p20.transfer(sample_vol, s, d, mix_after=(1, 2))
