metadata = {
    'protocolName': 'Extraction Prep with Kingfisher Flex Extractor',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protodest Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [num_samp, mix_reps,
        p300_mount, p1000_mount] = get_values(  # noqa: F821
        "num_samp", "mix_reps",
            "p300_mount", "p1000_mount")

    if not 0 <= num_samp <= 96:
        raise Exception("Enter a sample number between 1-96")

    # load labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '1')
    reservoir2 = ctx.load_labware('nest_12_reservoir_15ml', '2')
    npw4_block = ctx.load_labware('nest_96_wellplate_2200ul', '3')
    sample_block = ctx.load_labware('nest_96_wellplate_2200ul', '4')
    elution_block = ctx.load_labware('nest_96_wellplate_2200ul', '5')
    ethanol_block = ctx.load_labware('nest_96_wellplate_2200ul', '6')
    npw3_block = ctx.load_labware('nest_96_wellplate_2200ul', '7')

    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                  for slot in ['9', '8']]
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '10')]
    tuberack = ctx.load_labware('opentrons_24_tuberack_1500ul', '11')

    # load instrument
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack1000)
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tiprack300)

    num_channels_per_pickup = 1  # (only pickup tips on front-most channel)
    tips_ordered = [
        tip for rack in tiprack300
        for row in rack.rows()[
         len(rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]
        for tip in row]
    tip_count = 0

    def pick_up(pip):
        nonlocal tip_count
        pip.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # reagents
    mag_beads = reservoir.rows()[0][:4]
    ethanol = reservoir.rows()[0][4:8]
    npw3 = reservoir.rows()[0][8:12]
    npw4 = reservoir2.rows()[0][:4]

    proteinase_k = tuberack.rows()[0][:2]
    ntc = tuberack.rows()[1][0]
    hsc = tuberack.rows()[2][0]
    elution_buffer = tuberack.rows()[3][:4]

    # add controls
    airgap = 100
    p1000.pick_up_tip()
    p1000.aspirate(400, ntc)
    p1000.air_gap(airgap)
    p1000.dispense(400+airgap, sample_block.wells()[0])
    p1000.blow_out()
    p1000.drop_tip()

    p1000.pick_up_tip()
    p1000.aspirate(400, hsc)
    p1000.air_gap(airgap)
    p1000.dispense(400+airgap, sample_block.wells()[1])
    p1000.blow_out()
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # add proteinase k
    airgap = 20
    pick_up(p300)
    for s, d in zip(proteinase_k*num_samp, sample_block.wells()[:num_samp]):
        p300.aspirate(24, s)
        p300.air_gap(airgap)
        p300.dispense(24+airgap, d.top(z=-5))
        p300.blow_out()
    p300.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # make npw3, npw4 and ethanol npw3_block
    # ethanol
    p1000.pick_up_tip()
    for ethanol_well, dest in zip(ethanol*num_samp,
                                  ethanol_block.wells()[:num_samp]):
        p1000.aspirate(600, ethanol_well)
        p1000.air_gap(airgap)
        p1000.dispense(600+airgap, dest)
        p1000.blow_out()
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # npw3
    p1000.pick_up_tip()
    for npw3_well, dest in zip(npw3*num_samp,
                               npw3_block.wells()[:num_samp]):
        p1000.aspirate(600, npw3_well)
        p1000.air_gap(airgap)
        p1000.dispense(600+airgap, dest)
        p1000.blow_out()
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # npw4
    p1000.pick_up_tip()
    for npw4_well, dest in zip(npw4*num_samp, npw4_block.wells()[:num_samp]):
        p1000.aspirate(600, npw4_well)
        p1000.air_gap(airgap)
        p1000.dispense(600+airgap, dest)
        p1000.blow_out()
    p1000.drop_tip()

    # elution buffer
    airgap = 25
    pick_up(p300)
    for elution_tubes, elution_well in zip(elution_buffer*num_samp,
                                           elution_block.wells()[:num_samp]):
        p300.aspirate(50, elution_tubes)
        p300.air_gap(airgap)
        p300.dispense(50, elution_well)
        p300.blow_out()
    p300.drop_tip()

    # add magnetic beads
    airgap = 100
    p1000.pick_up_tip()
    for mag_well, dest in zip(mag_beads*num_samp,
                              sample_block.wells()[:num_samp]):
        p1000.mix(mix_reps, 1000, mag_well)
        p1000.aspirate(595, mag_well)
        p1000.air_gap(airgap)
        p1000.dispense(595+airgap, dest.top(z=-5))
        p1000.blow_out()
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')
