import math

metadata = {
    'protocolName': 'Normalization and Pooling',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [transfer_csv, m20_mount, m300_mount, sample_vol
     ] = get_values(  # noqa: F821
        'transfer_csv', 'm20_mount', 'm300_mount', 'sample_vol')

    # load labware
    tips20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '6')]
    tips200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '4')]
    sample_plate = ctx.load_labware('eppendorfmetaladapter_96_wellplate_200ul',
                                    '5', 'sample plate')
    normalization_plate = ctx.load_labware(
        'eppendorfmetaladapter_96_wellplate_200ul', '8', 'normalization plate')
    pool_tube = ctx.load_labware('eppendorf_24_tuberack_1500ul', '11',
                                 'pool tube (A1)').wells()[0]
    rsb = ctx.load_labware('nest_12_reservoir_15ml', '7',
                           'reagent reservoir').wells()[-1]

    # load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips200)

    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in transfer_csv.splitlines()][1:]

    num_cols = math.ceil(len(data)/6)

    def _pick_up(pip, mode):
        tips_single = [
            well for rack in pip.tip_racks[::-1]
            for col in rack.columns()[::-1]
            for well in col[::-1]]
        tips_multi = [
            well for rack in pip.tip_racks
            for well in rack.rows()[2]]

        tips = tips_single if mode == 'single' else tips_multi
        for tip_well in tips:
            if tip_well.has_tip:
                pip.pick_up_tip(tip_well)
                return

    # transfer RSB
    for line in data:
        dest = normalization_plate.wells_by_name()[line[0]]
        vol = float(line[1])
        pip = m300 if vol >= 20 else m20
        _pick_up(pip, 'single')
        pip.aspirate(vol, rsb)
        pip.dispense(vol, dest)
        pip.drop_tip()

    # transfer sample
    pip = m300 if sample_vol >= 20 else m20
    for s, d in zip(sample_plate.rows()[0][:num_cols],
                    normalization_plate.rows()[0][:num_cols]):
        _pick_up(pip, 'multi')
        pip.transfer(sample_vol, s, d, mix_after=(5, 10), new_tip='never')
        pip.drop_tip()

    # pool
    all_pool_sources = [
        well for col in normalization_plate.columns()[:num_cols]
        for well in col[:6]]
    for source in all_pool_sources:
        _pick_up(m20, 'single')
        m20.aspirate(5, source)
        m20.dispense(5, pool_tube)
        m20.drop_tip()
