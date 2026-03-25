"""Protocol."""
from opentrons import protocol_api

metadata = {
    'protocolName': 'Semi-Automated PCR Prep',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):
    """Protocol."""
    [num_samp, p20_rate, p300_rate,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "p20_rate", "p300_rate", "p20_mount", "p300_mount")

    # load labware
    final_plate = ctx.load_labware('corning_384_wellplate_112ul_flat', '1')
    thermocyc_plate = ctx.load_labware('corning_384_wellplate_112ul_flat', '2')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '3')
    tuberacks = [ctx.load_labware('opentrons_15_tuberack_falcon_15ml_conical',
                 slot) for slot in ['4', '5', '6', '7', '8', '9']]
    tiprack20 = ctx.load_labware('opentrons_96_filtertiprack_20ul', '10')
    tiprack300 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '11')

    # load pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tiprack20])
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tiprack300])

    p20.flow_rate.dispense = p20_rate*p20.flow_rate.dispense
    p300.flow_rate.dispense = p300_rate*p300.flow_rate.dispense

    def pickup(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # protocol
    lysis_buffer = reservoir.wells()[0]

    # distribute lysis buffer to all wells
    pickup(p300)
    for well in thermocyc_plate.wells()[:num_samp]:
        p300.distribute(50, lysis_buffer, well, new_tip='never')
    p300.drop_tip()

    # distribute sample to all well
    tubes = [tube for rack in tuberacks for tube in rack.wells()]
    airgap = 5
    tube_ctr = 0
    for well in thermocyc_plate.wells()[:num_samp]:
        pickup(p300)
        p300.aspirate(50, tubes[tube_ctr])
        ctx.delay(seconds=1)
        p300.air_gap(airgap)
        p300.dispense(50, well)
        p300.drop_tip()
        tube_ctr += 1
        ctx.comment('\n')
        if tube_ctr == 90:
            tube_ctr = 0
            ctx.pause('''
                        All samples on deck are transferred-
                        Place remaining tubes in tuberacks starting from
                        Slot 4, placing tubes down by column.
                        ''')

    ctx.pause('''Sample and lysis transfer complete. Spin down, and thermocycle
                 the 384 well plate, and then place the plate back on the deck
                 for final transfer. ''')

    # final transfer to 384 plate
    for source, dest in zip(thermocyc_plate.wells(),
                            final_plate.wells()[:num_samp]):
        pickup(p20)
        p20.aspirate(4, source)
        p20.air_gap(airgap)
        p20.dispense(4, dest)
        p20.blow_out()
        p20.drop_tip()
