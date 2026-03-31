import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Nucleic Acid Purification',
    'author': 'parrish.payne@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samp, m300_mount] = get_values(  # noqa: F821
        "num_samp", "m300_mount")

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a sample number between 1-96")

    # labware
    mag_mod = ctx.load_module('magnetic module gen2', 6)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    dest_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr', 3)

    reag_res = ctx.load_labware('nest_12_reservoir_15ml', 8)
    wash_buff_res = ctx.load_labware('nest_1_reservoir_195ml', 5)
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', 2)

    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [1, 4, 7, 10, 11]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    # functions

    # Helper Functions
    def pick_up(pip):
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Replace the tip racks and empty the waste bin")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def slow_tip_withdrawal(current_pipette, well_location, to_center=False):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            current_pipette.move_to(well_location.top())
        else:
            current_pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # variables
    num_cols = math.ceil(num_samp/8)
    samples = mag_plate.rows()[0][:num_cols]
    wash_buff = wash_buff_res.wells()[0]
    elution_buff = reag_res.wells()[0]  # A1 of wash buff res
    trash = waste_res.wells()[0].top()  # A1 of waste res
    destination = dest_plate.rows()[0][:num_cols]

    # protocol
    ctx.comment('\n----------MIXING LYSATES, BIND & BEADS-----------\n\n')
    mix_vol = 200
    num_mix = 15
    for col in samples:
        pick_up(m300)

        for i in range(num_mix):
            m300.aspirate(mix_vol, col.bottom(5))
            m300.dispense(mix_vol, col.bottom(10))

        slow_tip_withdrawal(m300, col)
        m300.drop_tip()

    ctx.comment('\n-------------INCUBATION ON MAGNET---------------\n\n')
    mag_mod.engage(height_from_base=4.0)
    ctx.delay(minutes=10)

    ctx.comment('\n----------------REMOVING SUPER------------------\n\n')
    sup_vol = 1820   # as per Parker during onsite
    for col in samples:
        pick_up(m300)

        tip_ref_vol = m300.tip_racks[0].wells()[0].max_volume
        num_transfers = math.ceil(sup_vol/tip_ref_vol)
        transfer_vol = sup_vol/num_transfers

        for i in range(num_transfers):
            m300.aspirate(transfer_vol, col.bottom(0.4), rate=0.1)
            # m300.aspirate(20, col.bottom(0.4), rate=0.1)
            slow_tip_withdrawal(m300, col)
            m300.dispense(transfer_vol, trash)
            m300.blow_out()

        m300.drop_tip()

    mag_mod.disengage()

    ctx.pause("Empty liquid waste Reservoir")

    ctx.comment('\n---------------WASH STEP----------------\n\n')

    wash_vol = 500
    num_buff_transfers = math.ceil(wash_vol/tip_ref_vol)
    buff_transfer_vol = wash_vol/num_buff_transfers

    for i in range(3):
        for col in samples:
            pick_up(m300)

            for i in range(num_buff_transfers):
                m300.aspirate(buff_transfer_vol, wash_buff)
                m300.dispense(buff_transfer_vol, col.top())
                m300.blow_out()

            m300.mix(5, 200, col)
            m300.drop_tip()

        mag_mod.engage(height_from_base=4.0)
        ctx.delay(minutes=5)

        for col in samples:
            pick_up(m300)

            for i in range(num_buff_transfers):
                m300.aspirate(buff_transfer_vol, col.bottom(0.4), rate=0.1)
                slow_tip_withdrawal(m300, col)
                m300.dispense(buff_transfer_vol, trash)
                m300.blow_out()

            m300.drop_tip()

        mag_mod.disengage()

    ctx.comment('\n----------------AIR DRY BEADS------------------\n\n')
    ctx.delay(minutes=5)

    ctx.comment('\n----------------ELUTION STEP------------------\n\n')

    for col in samples:

        pick_up(m300)
        m300.aspirate(50, elution_buff)
        m300.dispense(50, col)
        m300.mix(15, 50, col)
        m300.drop_tip()

    mag_mod.engage(height_from_base=4.0)
    ctx.delay(minutes=5)

    for s, d in zip(samples, destination):
        pick_up(m300)
        m300.aspirate(50, s.bottom(0.4), rate=0.1)
        m300.dispense(50, d)
        m300.drop_tip()

    mag_mod.disengage()
