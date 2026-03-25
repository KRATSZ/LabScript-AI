import math
from opentrons import types

metadata = {
    'protocolName': 'Nucleic Acid Purification with Magnetic Beads',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [m300_mount, samples, engage_height] = get_values(  # noqa: F821
        "m300_mount", "samples", "engage_height")

    cols = math.ceil(samples/8)

    # Load Labware
    waste = ctx.load_labware('starlab10ml24wellplate_24_wellplate_10000ul', 1,
                             'Waste Reservoir')
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul',
                                slot) for slot in [2, 7, 8]]
    elution_plate = ctx.load_labware('4titude_96_wellplate_200ul', 3,
                                     'Elution Plate')
    mag_mod = ctx.load_module('magnetic module gen2', 4)
    mag_plate = mag_mod.load_labware('4titude_96_wellplate_200ul')
    reagents = ctx.load_labware('starlab_12_reservoir_22000ul', 5,
                                'Reagent Reservoir')

    # Load Pipette
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips300)

    # Tip Mapping
    reserved_tips = tips300[0].rows()[0]
    available_tips = [tips300[i].rows()[0] for i in range(1, 3)]
    available_tips = [tip for tips in available_tips for tip in tips]

    # Helper Functions
    def remove_supernatant(vol, src, dest, side, mode=None):
        if mode == 'elution':
            m300.flow_rate.aspirate = 10
        else:
            m300.flow_rate.aspirate = 20
        while vol > 200:
            m300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            m300.dispense(200, dest)
            m300.aspirate(10, dest)
            vol -= 200
        m300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        m300.dispense(vol, dest)
        m300.blow_out()
        m300.flow_rate.aspirate = 50

    def reset_flow_rates():
        m300.flow_rate.aspirate = 46.43
        m300.flow_rate.dispense = 46.43

    # Wells
    sample_plate_wells = mag_plate.rows()[0][:cols]
    elution_plate_wells = elution_plate.rows()[0][:cols]

    # Bead transfer
    ctx.pause('Set the deck up as per the SOP')
    m300.pick_up_tip(available_tips[0])
    beads = reagents['A1']
    for dest in sample_plate_wells:
        m300.transfer(20, beads.bottom(z=3), dest.top(z=2),
                      mix_before=(2, 150), air_gap=20, blow_out=True,
                      blowout_location='destination well', new_tip='never')
    m300.drop_tip()
    available_tips.pop(0)
    ctx.delay(minutes=5, msg='5 Min incubation to allow bead binding')
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=3, msg='''3 min incubation to allow beads to move
              to magnet''')

    # Removal of supernatant
    for i, src in enumerate(sample_plate_wells):
        m300.pick_up_tip(reserved_tips[i])
        remove_supernatant(40, src, waste['A1'].bottom(z=10), -1)
        m300.return_tip(reserved_tips[i])

    # Ethanol Washes
    for ethanol in ['A3', 'A4']:
        ctx.comment('Performing Ethanol Wash')
        m300.pick_up_tip(available_tips[0])
        for dest in sample_plate_wells:
            m300.transfer(100, reagents[ethanol].bottom(z=3), dest.top(z=2),
                          air_gap=20, blow_out=True,
                          blowout_location='destination well', new_tip='never')
        m300.drop_tip()
        available_tips.pop(0)

        ctx.delay(seconds=30, msg='Incubate for 30 seconds at RT')

        for i, src in enumerate(sample_plate_wells):
            m300.pick_up_tip(reserved_tips[i])
            remove_supernatant(100, src, waste['A1'].bottom(z=10), -1)
            m300.return_tip(reserved_tips[i])

    # Elution Stage
    ctx.delay(minutes=10, msg='Air dry the pellet for 10mins at RT')
    mag_mod.disengage()
    elution_buff = reagents['A5']
    for dest in sample_plate_wells:
        m300.pick_up_tip(available_tips[0])
        m300.transfer(20, elution_buff.bottom(z=3), dest.bottom(z=3),
                      mix_before=(5, 10), blow_out=True,
                      blowout_location='destination well', new_tip='never')
        m300.drop_tip()
        available_tips.pop(0)

    ctx.delay(minutes=10, msg='''Incubate at RT for 10 mins to elute the
              sample off the beads''')
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=2, msg='''Incubate at RT for 2 mins to allow beads to
              move to magnet''')

    for src, dest in zip(sample_plate_wells, elution_plate_wells):
        if len(available_tips) == 0:
            ctx.pause('Replace the tips in Slot 7 and 8')
            available_tips = [tips300[i].rows()[0] for i in range(1, 3)]
            available_tips = [tip for tips in available_tips for tip in tips]
        m300.pick_up_tip(available_tips[0])
        m300.transfer(20, src.bottom(z=1), dest.bottom(z=3),
                      blow_out=True, blowout_location='destination well',
                      new_tip='never')
        m300.drop_tip()
        available_tips.pop(0)
