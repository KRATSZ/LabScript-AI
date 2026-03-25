metadata = {
    'protocolName': 'Reagent Addition',
    'author': 'Nick <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    num_samples, _tip_start_column = get_values(  # noqa: F821
        'num_samples', '_tip_start_column')

    # labware setup
    plate = ctx.load_labware('corning_96_wellplate_360ul_flat', '2')
    tiprack300 = ctx.load_labware('opentrons_96_tiprack_300ul', '3')
    wistd = ctx.load_labware('reagent_1_reservoir_130000ul', '5',
                             'WISTD').wells()[0]
    water = ctx.load_labware('reagent_1_reservoir_130000ul', '6',
                             'water').wells()[0]

    # instrument setup
    m300 = ctx.load_instrument('p300_multi_gen2', 'left',
                               tip_racks=[tiprack300])

    if num_samples >= 12:
        samples = plate.rows()[0]
    else:
        samples = plate.rows()[0][:num_samples]

    # start at proper tip
    start_index = _tip_start_column - 1
    for col in tiprack300.columns()[:start_index]:
        for well in col:
            well.has_tip = False

    # transfer WISTD to wells
    for reagent in [wistd, water]:
        m300.pick_up_tip()
        m300.mix(3, 250, reagent)
        for dest in samples:
            m300.transfer(250, reagent, dest.top(-1), new_tip='never')
            m300.blow_out(dest.top(-1))
        m300.drop_tip()
