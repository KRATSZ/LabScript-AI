"""Protocol."""
metadata = {
    'protocolName': 'Plate Filling Heat Inactivated Covid Samples for PCR',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [num_samp, plate, m300_mount] = get_values(  # noqa: F821
        'num_samp', 'plate', 'm300_mount')

    if not 1 <= num_samp <= 94:
        raise Exception("Enter a number of samples between 1-94")

    # load labware
    plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '5')
    reservoir = ctx.load_labware('nest_1_reservoir_195ml', '1')
    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in ['3', '4']]
    tuberacks = [ctx.load_labware(
        'opentrons_15_tuberack_5000ul', slot)
        for slot in ['6', '7', '8', '9', '10', '11', '2']]

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack)

    # multi as single channel
    num_chan = 1
    tip_count = 0
    tips_ordered = [tip
                    for row in tiprack[1].rows()[
                     len(tiprack[1].rows())-num_chan::-1*num_chan]
                    for tip in row]

    def pick_up():
        nonlocal tip_count
        m300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # protocol
    sample_tubes = [tube for rack in tuberacks
                    for row in rack.rows()
                    for tube in row][:num_samp]

    plate_wells = [well for row in plate.rows() for well in row]

    # distribute saline
    m300.pick_up_tip()
    for col in plate.rows()[0]:
        m300.aspirate(250, reservoir.wells()[0])
        m300.touch_tip()
        m300.dispense(250, col)
        m300.blow_out()
    m300.drop_tip()

    # distribute sample
    for s, d in zip(sample_tubes, plate_wells[2:]):
        pick_up()
        m300.aspirate(250, s)
        m300.touch_tip()
        m300.dispense(250, d)
        m300.blow_out()
        m300.drop_tip()
