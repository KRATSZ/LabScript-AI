"""OPENTRONS."""
metadata = {
    'protocolName': 'Reverse Transcriptase Preparation',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """PROTOCOL."""
    [num_samp, reag_vol, well_plate,
        p20_mount] = get_values(  # noqa: F821
        "num_samp", "reag_vol", "well_plate",
            "p20_mount")
    num_tubes = num_samp+1
    if not 1 <= num_samp <= 95:
        raise Exception("Enter sample number 1-95")

    # load labware
    sample_plate = ctx.load_labware(well_plate, 3)
    tuberacks = [ctx.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', slot)  # noqa: E501
                 for slot in [4, 1, 5, 2]]

    all_tubes = [tube for tuberackset in [tuberacks[:2], tuberacks[2:]]
                 for i in range(6)
                 for j in range(2)
                 for tube in tuberackset[j].columns()[i]][:num_tubes]

    primer_tubes = all_tubes[:-1]

    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [7, 8, 9]]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tipracks)

    mix_tube = all_tubes[-1]
    p20.flow_rate.aspirate = 7.56
    p20.flow_rate.dispense = 7.56
    # add mix
    ctx.comment('\n~~~~~~~~~~~~~~~ADDING MIX~~~~~~~~~~~~~~~~~\n')
    p20.flow_rate.aspirate /= 2
    p20.flow_rate.dispense /= 2
    for well in sample_plate.wells()[:num_samp]:
        p20.pick_up_tip()
        p20.aspirate(reag_vol, mix_tube)
        p20.dispense(reag_vol, well)
        p20.mix(1, reag_vol, well)
        p20.blow_out()
        p20.drop_tip()
        ctx.comment('\n')

    # add primer
    ctx.comment('\n~~~~~~~~~~~~~~~ADDING PRIMER~~~~~~~~~~~~~~\n')
    for tube, well in zip(primer_tubes, sample_plate.wells()):
        p20.pick_up_tip()
        p20.aspirate(1, tube, rate=0.5)
        p20.dispense(1, well, rate=0.5)
        p20.mix(1, 1, well)
        p20.blow_out()
        p20.drop_tip()
