metadata = {
    'protocolName': 'Tube to Plate Viral Media Transfer',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_samp, tube_asp_height, well_disp_height, flow_rate_asp,
        flow_rate_disp,
     p1000_mount] = get_values(  # noqa: F821
        "num_samp", "tube_asp_height", "well_disp_height", "flow_rate_asp",
        "flow_rate_disp", "p1000_mount")

    # load labware
    wellplate = ctx.load_labware('qiagen_96_wellplate_2250ul', '3')
    tiprack = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', '6')]
    tuberacks = [ctx.load_labware(
                 'nest_32_tuberack_8x15ml_8x15ml_8x15ml_8x15ml', slot)
                 for slot in ['1', '4', '7']]

    # load instruments
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack)
    p1000.flow_rate.aspirate = flow_rate_asp
    p1000.flow_rate.dispense = flow_rate_disp

    # PROTOCOL
    tubes = [tube for tuberack in tuberacks for row in tuberack.rows()
             for tube in row][:num_samp]
    wells = [well for row in wellplate.rows() for well in row]

    for tube, well in zip(tubes, wells):
        p1000.pick_up_tip()
        p1000.aspirate(200, tube.bottom(z=tube_asp_height))
        ctx.delay(seconds=1.5)
        p1000.dispense(200, well.bottom(z=well_disp_height))
        p1000.blow_out()
        p1000.drop_tip()
