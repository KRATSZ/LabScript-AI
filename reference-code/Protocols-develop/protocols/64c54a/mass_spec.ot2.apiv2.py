import math

metadata = {
    'protocolName': 'Mass Spec Sample Prep',
    'author': 'Nick <ndiehl@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    num_samples, p1000_mount = get_values(  # noqa: F821
        'num_samples', 'p1000_mount')

    # labware
    source_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '1',
        'source tubes')
    dest_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2',
        'destination tubes')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4')
    tipracks1000 = [
        ctx.load_labware('opentrons_96_tiprack_1000ul', slot)
        for slot in ['3', '5', '6', '7', '8', '9', '10', '11'][
            :math.ceil(num_samples*2/96)]]

    # pipettes
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tipracks1000)

    # define wells and volumes
    num_tubes_per_replacement = len(source_rack.wells())
    num_replacements = math.ceil(num_samples/num_tubes_per_replacement)
    source_sets, dest_sets = [
        [rack.wells()[:num_samples % num_tubes_per_replacement]
         if r == num_replacements - 1
         else rack.wells()
         for r in range(num_replacements)]
        for rack in [source_rack, dest_rack]
    ]

    mobile_phase_a = reservoir.rows()[0][0]

    vol_supernatant = 900.0
    vol_reconstitution = 100.0

    # transfer precipitate
    p1000.flow_rate.aspirate /= 5
    for i, (source_set, dest_set) in enumerate(zip(source_sets, dest_sets)):
        samples_per_set = len(source_set)
        sample_start = (i+1)*num_tubes_per_replacement+1
        sample_end = (i+1)*num_tubes_per_replacement+samples_per_set
        for s, d in zip(source_set, dest_set):
            p1000.transfer(vol_supernatant, s.bottom(3), d)
        if i < num_replacements - 1:
            msg = f'Place next set of samples {sample_start}-{sample_end} in \
slot 1 and fresh 1.5ml tubes in slot 2.'
        else:
            msg = 'Dry the samples to with a N2 dryer or SpeedVac with no \
temp. Place samples 1-24 on slot 1 when complete.'
        ctx.pause(msg)

    # reconstitute in mobile phase A
    p1000.flow_rate.aspirate *= 5
    for i, source_set in enumerate(source_sets):
        samples_per_set = len(source_set)
        sample_start = (i+1)*num_tubes_per_replacement+1
        sample_end = (i+1)*num_tubes_per_replacement+samples_per_set
        for s in source_set:
            p1000.transfer(vol_reconstitution, mobile_phase_a, s.bottom(3),
                           mix_after=(5, 100))
        if i < num_replacements - 1:
            msg = f'Place next set of samples {sample_start}-{sample_end} in \
slot 1 and fresh 1.5ml tubes in slot 2.'
            ctx.pause(msg)
