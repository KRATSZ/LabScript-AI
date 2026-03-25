"""PROTOCOL."""
metadata = {
    'protocolName': 'Covid-19 Saliva Sample Plating',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):
    """PROTOCOL."""
    [num_samp, delay_after_asp,
        asp_rate, disp_rate, p1000_mount] = get_values(  # noqa: F821
        "num_samp", "delay_after_asp", "disp_rate", "asp_rate", "p1000_mount")

    # load labware
    plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '1')
    tiprack = [ctx.load_labware('opentrons_96_tiprack_1000ul', '2')]
    tuberacks = [ctx.load_labware('opentrons_15_tuberack_15000ul',
                 slot) for slot in ['4', '5', '6', '7', '8', '9', '10']]

    # load instrument
    p1000 = ctx.load_instrument('p1000_single_gen2', 'left', tip_racks=tiprack)

    # protocol
    tubes_by_row = [tube for rack in tuberacks
                    for row in rack.rows() for tube in row]
    wells_by_row = [well for row in plate.rows() for well in row]

    p1000.flow_rate.aspirate = asp_rate*p1000.flow_rate.aspirate
    p1000.flow_rate.dispense = disp_rate*p1000.flow_rate.dispense

    for sample, dest_well in zip(tubes_by_row, wells_by_row[:num_samp]):
        p1000.pick_up_tip()
        p1000.aspirate(200, sample)
        ctx.delay(seconds=delay_after_asp)
        p1000.dispense(200, dest_well)
        p1000.blow_out()
        p1000.drop_tip()
