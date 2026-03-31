from opentrons import protocol_api

metadata = {
    'protocolName': 'iAMP COVID-19 Detection Kit - Pt. 2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [num_samp, reaction_plate,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "reaction_plate", "p20_mount", "p300_mount")

    num_full_col = num_samp//8

    if not 1 <= num_samp <= 94:
        raise Exception("Enter a sample number 1-96")

    # LABWARE
    mmx_plate = ctx.load_labware(
                  'biorad_96_aluminumblock_200ul', '8',
                  label='the MASTERMIX PLATE')
    pcr_plate = ctx.load_labware(
                  reaction_plate, '9',
                  label='the PCR PLATE')
    sample_racks = [ctx.load_labware(
                      'opentrons_15_tuberack_5000ul',
                      slot, label="the SAMPLE RACK")
                    for slot in ['1', '2', '3', '4', '5', '6', '7']]

    # TIPRACKS
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '10',
                                  label='20uL TIPRACK')]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '11',
                                   label='200uL TIPRACK')]

    # INSTRUMENTS
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)

    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tiprack200)

    # MAPPING
    spill = num_samp % 8
    all_sample_tubes = [tube
                        for rack in sample_racks
                        for tube in rack.wells()][:num_samp]
    mmx = mmx_plate.rows()[0][:2]  # column 1 of mmx plate
    controls_source = mmx_plate.wells()[94:]
    controls_dest = pcr_plate.wells()[94:]

    # protocol
    ctx.comment('\n\n~~~~~~~~MOVING MMX TO PLATE~~~~~~~~~\n')
    mmx_vol = 20
    mmx_ctr = 0
    if num_full_col > 0:
        p300.pick_up_tip()
        for i, col in enumerate(pcr_plate.rows()[0][:num_full_col if num_samp != 94 else 12]):  # noqa: E501
            p300.aspirate(mmx_vol, mmx[mmx_ctr])
            p300.dispense(mmx_vol, col)
            p300.blow_out(col.top(z=-3))
            if i == 5:
                mmx_ctr += 1

        p300.drop_tip()
        ctx.comment('\n')

    if spill > 0 and not num_samp == 94:
        ctx.comment('TRANSFERRING MMX TO UNFILLED COLUMN')
        if not p20.has_tip:
            p20.pick_up_tip()
        for source, well in zip(mmx_plate.columns()[mmx_ctr],
                                pcr_plate.columns()[num_full_col][:spill]):
            p20.transfer(20, source,
                         well,
                         new_tip='never',
                         touch_tip=True,
                         blow_out=True,
                         blowout_location='destination well')
        p20.drop_tip()
        ctx.comment('\n')

    if not num_samp == 94:
        ctx.comment('TRANSFERRING MMX TO CONTROLS')
        p20.pick_up_tip()
        for i, source in enumerate(
                        mmx_plate.columns()[mmx_ctr][spill:spill+2]):

            p20.transfer(20, source,
                         controls_dest[i],
                         new_tip='never',
                         touch_tip=True,
                         blow_out=True,
                         blowout_location='destination well')
        p20.drop_tip()

    ctx.comment('\n\n~~~~~~~~MOVING SAMPLES TO PLATE~~~~~~~~~\n')
    for sample, well in zip(all_sample_tubes, pcr_plate.wells()):
        p20.pick_up_tip()
        p20.aspirate(5, sample)
        p20.dispense(5, well)
        p20.blow_out()
        p20.touch_tip()
        p20.drop_tip()

    ctx.comment('\n\n~~~~~~~~MOVING CONTROLS TO PLATE~~~~~~~~~\n')
    for source, dest in zip(controls_source, controls_dest):
        p20.pick_up_tip()
        p20.aspirate(5, source)
        p20.dispense(5, dest)
        p20.blow_out(dest.top(z=-3))
        p20.touch_tip()
        p20.drop_tip()
