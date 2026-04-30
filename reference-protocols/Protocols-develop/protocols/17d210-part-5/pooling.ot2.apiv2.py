import math

metadata = {
    'protocolName': 'Verogen ForenSeq DNA Signature Prep Kit Part 5/5: \
Pooling',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_samples_per_plate, m20_mount, sample_vol, num_plates,
     transfer_scheme] = get_values(  # noqa: F821
     'num_samples_per_plate', 'm20_mount', 'sample_vol', 'num_plates',
     'transfer_scheme')

    # load labware
    tips20m = [ctx.load_labware('opentrons_96_tiprack_20ul', '3')]
    pcr_plates = [
        ctx.load_labware('amplifyt_96_wellplate_200ul', slot,
                         f'library plate {i+1}')
        for i, slot in enumerate(['1', '2', '4', '5', '6'][:num_plates])]
    pool_strips = ctx.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '9',
        'pool strips').rows()[0][0:5]

    # load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20m)

    num_cols = math.ceil(num_samples_per_plate/8)
    sample_sets = [plate.rows()[0][:num_cols] for plate in pcr_plates]

    # transfer
    for strip, set in zip(pool_strips, sample_sets):
        if transfer_scheme == 'same':
            m20.pick_up_tip()
        for sample in set:
            if not m20.has_tip:
                m20.pick_up_tip()
            m20.transfer(sample_vol, sample, strip, mix_before=(5, sample_vol),
                         new_tip='never')
            if transfer_scheme == 'change':
                m20.drop_tip()
        if m20.has_tip:
            m20.drop_tip()
