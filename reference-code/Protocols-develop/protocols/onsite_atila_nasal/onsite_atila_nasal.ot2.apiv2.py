from opentrons import protocol_api

metadata = {
    'protocolName': 'iAMP COVID-19 Detection Kit - Nasal',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [num_samp, reaction_plate,
        p20_mount, m20_mount] = get_values(  # noqa: F821
        "num_samp", "reaction_plate", "p20_mount", "m20_mount")

    num_full_col = num_samp//8
    spill = num_samp % 8

    if not 1 <= num_samp <= 94:
        raise Exception("Enter a sample number 1-94")

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
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                                  label='20uL TIPRACK')
                 for slot in ['10', '11']]

    # INSTRUMENTS
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)

    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tiprack20)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # MAPPING
    all_sample_tubes = [tube
                        for rack in sample_racks
                        for tube in rack.wells()][:num_samp]
    sbm = mmx_plate.rows()[0][0]
    mmx = mmx_plate.rows()[0][1]  # column 2 of mmx plate
    controls_dest = pcr_plate.wells()[94:]
    controls_source = mmx_plate.wells()[94:]

    # protocol
    ctx.comment('\n\n~~~~~~~~MOVING SBM TO PLATE~~~~~~~~~\n')
    if num_full_col > 0:
        pick_up(m20)
        for col in pcr_plate.rows()[0][:num_full_col]:
            m20.aspirate(12, sbm)
            m20.dispense(12, col.bottom(z=2))
            m20.blow_out(col.top(z=-3))
        m20.drop_tip()
        ctx.comment('\n')

    if spill > 0:
        pick_up(p20)
        for source, well in zip(mmx_plate.columns()[0],
                                pcr_plate.columns()[num_full_col][:spill]):
            p20.aspirate(12, source)
            p20.dispense(12, well.bottom(z=2))
            p20.blow_out(well.top(z=-3))
            p20.touch_tip()
        p20.drop_tip()

    ctx.comment('\n\n~~~~~~~~MOVING SAMPLES TO PLATE~~~~~~~~~\n')
    for sample, well in zip(all_sample_tubes, pcr_plate.wells()):
        pick_up(p20)
        p20.aspirate(3, sample.bottom(12))
        p20.dispense(3, well.bottom(z=2))
        p20.mix(3, 12, well.bottom(z=2), rate=1.2)
        p20.blow_out()
        p20.touch_tip()
        p20.drop_tip()

    ctx.delay(minutes=15)

    ctx.comment('\n\n~~~~~~~~MOVING MMX TO PLATE~~~~~~~~~\n')
    num_full_col = 12 if num_samp == 94 else num_full_col
    for col in pcr_plate.rows()[0][:num_full_col]:
        ctx.comment("Using P20-Multi")
        pick_up(m20)
        m20.aspirate(10, mmx)
        m20.dispense(10, col.bottom(z=2))
        m20.blow_out(col.top(z=-3))
        m20.drop_tip()
    ctx.comment('\n')

    if spill > 0 and not num_samp == 94:

        ctx.comment('TRANSFERRING MMX TO UNFILLED COLUMN')
        for source, well in zip(mmx_plate.columns()[1],
                                pcr_plate.columns()[num_full_col][:spill]):
            pick_up(p20)
            p20.aspirate(10, source)
            p20.dispense(10, well.bottom(z=2))
            p20.blow_out(col.top(z=-3))
            p20.touch_tip()
            p20.drop_tip()

    if not num_samp == 94:
        ctx.comment('TRANSFERRING MMX TO CONTROLS')
        ctx.comment("Using P20-Single")
        pick_up(p20)
        for i, source in enumerate(
                        mmx_plate.columns()[1][spill:spill+2]):
            p20.aspirate(10, source)
            p20.dispense(10, controls_dest[i].bottom(z=2))
            p20.blow_out(col.top(z=-3))
            p20.touch_tip()
        p20.drop_tip()

    ctx.comment('\n\n~~~~~~~~MOVING CONTROLS TO PLATE~~~~~~~~~\n')
    for source, dest in zip(controls_source, controls_dest):
        pick_up(p20)
        p20.aspirate(15, source)
        p20.dispense(15, dest.bottom(z=2))
        p20.blow_out(col.top(z=-3))
        p20.touch_tip()
        p20.drop_tip()
