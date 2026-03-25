from opentrons import protocol_api

metadata = {
    'protocolName': 'iAMP COVID-19 Detection Kit - Pt. 2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [num_samp, reaction_plate,
        p20_mount] = get_values(  # noqa: F821
        "num_samp", "reaction_plate", "p20_mount")

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a sample number 1-96")

    # LABWARE
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

    # INSTRUMENTS
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)

    # MAPPING
    all_sample_tubes = [tube
                        for rack in sample_racks
                        for tube in rack.wells()][:num_samp]

    # protocol

    ctx.comment('\n\n~~~~~~~~MOVING SAMPLES TO PLATE~~~~~~~~~\n')
    for sample, well in zip(all_sample_tubes, pcr_plate.wells()):
        p20.pick_up_tip()
        p20.aspirate(10, sample)
        p20.dispense(10, well)
        p20.blow_out()
        p20.touch_tip()
        p20.drop_tip()
