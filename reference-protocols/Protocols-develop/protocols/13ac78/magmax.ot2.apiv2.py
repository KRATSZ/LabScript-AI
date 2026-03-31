from opentrons.types import Point

metadata = {
    'protocolName': 'Custom 384-Well Plate PCR Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    num_samples, m20_mount, p20_mount = get_values(  # noqa: F821
        'num_samples', 'm20_mount', 'p20_mount')

    tipracks20m = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['2', '3', '4', '5', '6']]
    tipracks20s = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['1']]

    strips = ctx.load_labware('ssibio_96_tuberack_200ul', '8')
    plate384 = ctx.load_labware('thermofishermicroamp_384_wellplate_50ul',
                                '11')

    mm = strips.rows()[0][:3]
    samples = [strips.columns()[i][0] for i in [5, 7]]
    pos_control = strips.wells_by_name()['A10']
    water = strips.wells_by_name()['A12']

    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20m)
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tipracks20s)

    dests1 = [
        well for i in range(3) for row in plate384.rows()[0:2]
        for well in row[i*8:(i+1)*8]]

    # mastermix
    m20.pick_up_tip()
    for i, d in enumerate(dests1):
        m20.transfer(8.5, mm[i//16].bottom().move(Point(x=0.8, y=0.4, z=-4.5)),
                     d, new_tip='never')
    m20.drop_tip()

    ctx.pause('Ensure samples are loaded in place before resuming.')

    dests2 = [
        well for row in plate384.rows()[0:2] for well in row[:22]]

    # sample
    for i, d in enumerate(dests2):
        m20.pick_up_tip()
        m20.transfer(
            1, samples[i//22].bottom().move(Point(x=0.8, y=0.4, z=-4.5)),
            d.bottom().move(Point(x=1.0, y=-0.1, z=1)),
            mix_after=(5, 5), new_tip='never')
        m20.touch_tip(d, speed=20, radius=0.9)
        m20.drop_tip()

    # control
    for s, d_col in zip([pos_control, water], plate384.columns()[-2:]):
        for d in d_col:
            p20.transfer(1, s.bottom().move(Point(x=0.8, y=0.4, z=-4.5)),
                         d.bottom().move(Point(x=0.5, y=-0.1, z=1)),
                         mix_after=(5, 5))

    ctx.comment('Remove plate, seal, and place in QuantStudio 5 cycler.')
