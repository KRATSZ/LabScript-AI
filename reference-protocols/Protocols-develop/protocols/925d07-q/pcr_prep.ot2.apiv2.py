import math

metadata = {
    'title': 'QIAcuity Plate Transfer',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    num_samples, transfer_volume, m20_mount = get_values(  # noqa: F821
        'num_samples', 'transfer_volume', 'm20_mount')

    source_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                    '1', 'source plate (NEST)')
    dest_plate = ctx.load_labware('qiacuity_96_wellplate_200ul', '2',
                                  'destination plate (QIAcuity)')
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '4')]

    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20)

    num_cols = math.ceil(num_samples/8)

    m20.flow_rate.aspirate = 5
    m20.flow_rate.dispense = 5

    for s, d in zip(source_plate.rows()[0][:num_cols],
                    dest_plate.rows()[0][:num_cols]):
        m20.transfer(transfer_volume, s.bottom(0.5), d.bottom(3))
