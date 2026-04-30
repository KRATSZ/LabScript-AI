import math

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Nick <ndiehl@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_samples, num_primers, res_type, tube_type, tip_type, p20_multi_mount,
     p20_single_mount, height_dispense] = get_values(  # noqa: F821
     'num_samples', 'num_primers', 'res_type', 'tube_type', 'tip_type',
     'p20_multi_mount', 'p20_single_mount', 'height_dispense')

    # labware
    pcr_plate = ctx.load_labware('thermofishermicroamp_96_aluminumblock_200ul',
                                 '1', 'destination PCR plate')
    primer_rack = ctx.load_labware(tube_type, '2', 'primer rack')
    sample_plate = ctx.load_labware(
        'thermofishermicroamp_96_aluminumblock_200ul', '4',
        'source sample plate')
    tipracks20s = [ctx.load_labware('opentrons_96_tiprack_20ul', '3')]
    res = ctx.load_labware(res_type, '5', 'reagent reservoir')
    tipracks20m = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['6', '8', '9']]

    # pipettes
    if p20_single_mount == p20_multi_mount:
        raise Exception('Pipette mounts cannot match')
    p20 = ctx.load_instrument('p20_single_gen2', p20_single_mount,
                              tip_racks=tipracks20s)
    m20 = ctx.load_instrument('p20_multi_gen2', p20_multi_mount,
                              tip_racks=tipracks20m)

    # sample and primer
    num_cols = math.ceil(num_samples/8)
    if num_cols*num_primers > 12:
        raise Exception(f'Can only accommodate up to {math.floor(12/num_cols)} \
primers with {num_samples} samples or {math.floor(12/num_primers)} samples \
with {num_primers} primers.')

    # reagents
    mm = res.wells()[0]

    sample_sources = sample_plate.rows()[0][:num_cols]
    sample_dests_sets_m = [
        [pcr_plate.rows()[0][p*num_cols+s] for p in range(num_primers)]
        for s in range(num_cols)]
    primer_sources = primer_rack.wells()[:num_primers]
    primer_dest_sets = [
        [well
         for col in pcr_plate.columns()[p*num_cols:(p+1)*num_cols]
         for well in col]
        for p in range(num_primers)]

    # transfer BigDye + water mix
    reagent_dests_multi = pcr_plate.rows()[0][:num_cols*num_primers]
    m20.pick_up_tip()
    for d in reagent_dests_multi:
        m20.transfer(16, mm, d.bottom(height_dispense), new_tip='never')
    m20.drop_tip()

    # transfer samples
    for s, d_set in zip(sample_sources, sample_dests_sets_m):
        for d in d_set:
            m20.pick_up_tip()
            m20.transfer(3, s, d.bottom(height_dispense), new_tip='never')
            m20.drop_tip()

    # transfer primers
    for primer, dest_set in zip(primer_sources, primer_dest_sets):
        for d in dest_set:
            p20.pick_up_tip()
            p20.transfer(1, primer, d.bottom(height_dispense), new_tip='never')
            p20.drop_tip()
