from opentrons import protocol_api

metadata = {
    'protocolName': 'COVID-19 Patient Sample Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [p1000_mount, extraction_type, samples,
        sample_vol, sample_air_gap] = get_values(  # noqa: F821
        "p1000_mount", "extraction_type", "samples", "sample_vol",
        "sample_air_gap")

    if extraction_type == "single":
        if not 1 <= samples <= 94:
            raise Exception('''Please enter a sample number between 1
                            and 94 for single extraction.''')
    elif extraction_type == "double":
        if not 1 <= samples <= 47:
            raise Exception('''Please enter a sample number between
                            1 and 47 for double extraction.''')

    def pick_up(pip):
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Please replace the empty tip rack.")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # Load Labware
    dwp = ctx.load_labware('kingfisher_96_deepwell_plate_2ml', 2)
    tuberacks = [ctx.load_labware('iclean_15_tuberack', slot)
                 for slot in range(4, 11)]
    tiprack_1000ul = ctx.load_labware('opentrons_96_filtertiprack_1000ul', 1)

    # Load Pipettes
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=[tiprack_1000ul])

    # Get sample and tube rack wells
    if extraction_type == "single":
        sample_wells = dwp.wells()[:samples]
        tube_wells = [well for rack in tuberacks
                      for well in rack.wells()][:samples]
    elif extraction_type == "double":
        sample_wells = dwp.wells()[:samples*2]
        tube_wells = [well for rack in tuberacks for well in rack.wells()
                      for _ in range(2)][:samples*2]

    # Transfer Patient Samples to each well
    for source, dest in zip(tube_wells, sample_wells):
        pick_up(p1000)
        p1000.aspirate(sample_vol, source)
        p1000.air_gap(sample_air_gap)
        p1000.dispense(sample_vol+sample_air_gap, dest)
        p1000.drop_tip()
