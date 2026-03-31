import math

metadata = {
    'protocolName': 'OT-2 Demo',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [left_pip, right_pip, source_lw, dest_lw, num_samples, sample_vol,
     using_magdeck] = get_values(  # noqa: F821
        'left_pip', 'right_pip', 'source_lw', 'dest_lw', 'num_samples',
        'sample_vol', 'using_magdeck')

    # load labware
    source_rack = ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap',
                                   '1')
    source_res = ctx.load_labware('nest_12_reservoir_15ml', '3')
    dest_labware = ctx.load_labware(dest_lw, '2')
    if using_magdeck:
        magdeck = ctx.load_module('magnetic module gen2', '7')

    # load instrument
    pip_l = ctx.load_instrument(left_pip, 'left')
    pip_r = ctx.load_instrument(right_pip, 'right')

    tipracks_l_type = f'opentrons_96_tiprack_{pip_l.max_volume}ul'
    tipracks_r_type = f'opentrons_96_tiprack_{pip_r.max_volume}ul'
    tipracks_l = [ctx.load_labware(tipracks_l_type, '4')]
    tipracks_r = [ctx.load_labware(tipracks_r_type, '5')]

    pip_l.tip_racks = tipracks_l
    pip_r.tip_racks = tipracks_r
    ctx.set_rail_lights(on=True)

    # protocol
    ctx.pause('''Welcome to the OT-2 Demo Protocol-
                    This is the `Pause` function.
                    Pauses can be put at any point during a protocol
                    to replace plates, reagents, spin down plates,
                    or for any other instance where human intervention
                    is needed. Protocols continue after a `Pause` when
                    the `Resume` button is selected. Select `Resume`
                    to see more OT-2 features.''')

    pip = pip_l
    sources = source_rack.wells()
    destinations = dest_labware.wells()[:num_samples]
    for i, d in enumerate(destinations):
        dests_per_source = math.ceil(num_samples/len(sources))
        source = sources[i//dests_per_source]
        pip.transfer(sample_vol, source, d)

    pip = pip_r
    sources = source_res.wells()[:math.ceil(num_samples/8)]
    destinations = dest_labware.rows()[0][:math.ceil(num_samples/8)]

    for s, d in zip(sources, destinations):
        pip.transfer(sample_vol, s, d)

    if using_magdeck:
        ctx.comment('Engaging magnetic module...')
        for _ in range(3):
            magdeck.engage(height=18)
            magdeck.disengage()
        ctx.comment('Protocol complete. Move labware to magnetic module for \
bead separation.')
    else:
        ctx.comment('Protocol complete. Please remove your plate for further \
processing')
