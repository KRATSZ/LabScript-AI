metadata = {
    'protocolName': 'Rerack',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [m300_mount] = get_values(  # noqa: F821
        'm300_mount')

    # load labware
    tips200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['5', '3', '6', '9']]

    # load pipette
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount)

    # rerack
    sources = [well for rack in tips200[1:] for well in rack.rows()[0]]
    destinations = [
        col[(i+1)*2] for col in tips200[0].columns()
        for i in range(3)]

    for i, (s, d) in enumerate(zip(sources, destinations)):
        m300.pick_up_tip(s)
        if i == 0:  # ghost aspirate
            m300.aspirate(20, ctx.loaded_labwares[12].wells()[0].top())
            m300.dispense(20, ctx.loaded_labwares[12].wells()[0].top())
        m300.drop_tip(d)
