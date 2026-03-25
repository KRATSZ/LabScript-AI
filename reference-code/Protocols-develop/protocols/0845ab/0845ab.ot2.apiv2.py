import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Digestion and Bead Cleanup',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.14'
}


def run(ctx):

    [num_samp, real_mode, p20_mount, m300_mount] = get_values(  # noqa: F821
        "num_samp", "real_mode", "p20_mount", "m300_mount")

    # num_samp = 48
    num_col = math.ceil(num_samp/8)
    #
    # m300_mount = 'left'
    # p20_mount = 'right'
    #
    # real_mode = True

    # labware
    mag_mod = ctx.load_module("magnetic module gen2", 1)
    try:
        mag_plate = mag_mod.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt')  # noqa: E501

    except FileNotFoundError:
        mag_plate = mag_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')  # noqa: E501

    try:
        old_plate = ctx.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', 2)  # noqa: E501
    except FileNotFoundError:
        old_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                     2)

    tuberack = ctx.load_labware('opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', 3)  # noqa: E501

    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 6)
    trash = ctx.load_labware('nest_1_reservoir_195ml', 8).wells()[0].top()
    tmt_plate = ctx.load_labware('opentrons_96_tiprack_sarstedt_200ul', 9)

    if not ctx.is_simulating:

        hs_mod = ctx.load_module('heaterShakerModuleV1', 10)
        hs_mod.close_labware_latch()
    else:
        dummy = ctx.load_labware('nest_12_reservoir_15ml', 10)
        dummy = dummy

    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in [4, 5]]
    tips20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
              for slot in [7, 11]]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips300)

    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        pipette.default_speed = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        pipette.default_speed = 400

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(f"Replace empty tip rack for {pip}")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # mapping
    sample_cols = old_plate.rows()[0][:num_col]
    dest_cols = mag_plate.rows()[0][:num_col]
    dest_wells = [well for well in mag_plate.wells()[:num_samp]]

    pool_well1 = tuberack['B1']
    pool_well2 = tuberack['B2']
    pool_well3 = tuberack['B3']

    num_pools = int(num_samp/16)

    all_pools = [pool_well1, pool_well2, pool_well3][:num_pools]

    acn = reservoir['A1']
    ethanol = reservoir['A2']

    beads = tuberack['A1']
    mm_teab = tuberack['A2']
    ha = tuberack['A3']
    formic_acid = tuberack['A4']

    digestion_solution = tmt_plate['A12']

    # protocol
    ctx.comment('\n---------------ADDING BEADS TO PLATES----------------\n\n')

    pick_up(p20)
    p20.mix(15, 20, beads, rate=1.5)
    for well in dest_wells:
        p20.aspirate(4, beads)
        slow_tip_withdrawal(p20, beads)
        p20.dispense(4, well)
        p20.blow_out()
    p20.drop_tip() if real_mode else p20.return_tip()

    ctx.comment('\n---------------Transferring Sample----------------\n\n')
    for s, d in zip(sample_cols, dest_cols):
        pick_up(m300)
        m300.aspirate(30, s)
        m300.dispense(30, d)
        m300.blow_out()
        m300.drop_tip() if real_mode else m300.return_tip()

    ctx.comment('\n---------------Transferring ACN----------------\n\n')
    for col in dest_cols:
        pick_up(m300)
        m300.aspirate(70, acn)
        m300.dispense(70, col)
        m300.mix(3, 85, col, rate=0.7)
        m300.drop_tip() if real_mode else m300.return_tip()

    ctx.delay(minutes=2 if real_mode else 0.5)

    mag_mod.engage(height_from_base=1)

    ctx.delay(minutes=5 if real_mode else 0.5)

    ctx.comment('\n---------------Removing Super----------------\n\n')
    pick_up(m300)
    for col in dest_cols:
        m300.aspirate(100, col, rate=0.1)
        m300.aspirate(10, col.bottom(z=0.5), rate=0.1)
        m300.dispense(110, trash)
        ctx.delay(seconds=1.5)
        m300.blow_out()
    m300.drop_tip() if real_mode else m300.return_tip()

    for _ in range(2):
        ctx.comment('\n---------------Adding Ethanol----------------\n\n')
        pick_up(m300)
        for col in dest_cols:
            m300.aspirate(100, ethanol, rate=0.5)
            slow_tip_withdrawal(m300, ethanol)
            m300.dispense(100, col.top())
        m300.drop_tip() if real_mode else m300.return_tip()

        ctx.comment('\n---------------Removing Ethanol----------------\n\n')
        pick_up(m300)
        for col in dest_cols:
            m300.aspirate(100, col, rate=0.1)
            m300.aspirate(10, col.bottom(z=0.5), rate=0.1)
            m300.dispense(110, trash)
            ctx.delay(seconds=1.5)
            m300.blow_out()
        m300.drop_tip() if real_mode else m300.return_tip()

    mag_mod.disengage()

    ctx.comment('\n--------------ADDING Digestion Solution--------------\n\n')
    for col in dest_cols:
        pick_up(m300)
        m300.aspirate(20, digestion_solution)
        m300.dispense(20, col)
        m300.mix(2, 15, col)
        m300.blow_out()
        m300.drop_tip() if real_mode else m300.return_tip()

    if not ctx.is_simulating:
        hs_mod.open_labware_latch()
    ctx.pause('Move plate to heater shaker')
    if not ctx.is_simulating:
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_temperature(37)
    ctx.pause('Overnight Digestion')
    if not ctx.is_simulating:
        hs_mod.deactivate_heater()
        hs_mod.open_labware_latch()
    ctx.pause("Move plate to magnetic module")

    mag_mod.engage(height_from_base=1)
    ctx.delay(minutes=2 if real_mode else 0.5)

    ctx.comment('\n---------------Transferring Sample----------------\n\n')
    new_cols = mag_plate.rows()[0][num_col:num_col+num_col]
    new_wells = [well for col in mag_plate.columns()[num_col:num_col+num_col]
                 for well in col]

    for s, d in zip(dest_cols, new_cols):
        pick_up(m300)
        m300.aspirate(20, s, rate=0.05)
        m300.dispense(20, d)
        m300.move_to(d.top())
        ctx.delay(seconds=1.5)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip() if real_mode else m300.return_tip()

    tmt_wells = [well for col in tmt_plate.columns()[:num_col]
                 for well in col]

    for well in tmt_wells:
        pick_up(p20)
        p20.aspirate(5, mm_teab)
        p20.dispense(5, well)
        p20.mix(3, 9, well)
        p20.drop_tip() if real_mode else p20.return_tip()

    ctx.comment('\n-----From TMT Wells to Sample Wells----------\n\n')
    for s, d in zip(tmt_wells, new_wells):
        pick_up(p20)
        p20.aspirate(9, s)
        p20.dispense(9, d)
        p20.mix(3, 20, d)
        p20.drop_tip() if real_mode else p20.return_tip()

    ctx.delay(minutes=60 if real_mode else 0.5)

    for well in new_wells:
        pick_up(p20)
        p20.aspirate(5, ha)
        p20.dispense(5, well)
        p20.mix(1, 20, well)
        p20.drop_tip() if real_mode else p20.return_tip()

    ctx.delay(minutes=15 if real_mode else 0.5)
    # WHAT IS POOL VOLUME?
    chunked_wells_of_16 = [new_wells[i:i+16]
                           for i in range(0, len(new_wells), 16)]

    for chunk, pool in zip(chunked_wells_of_16, all_pools):
        pick_up(p20)
        for well in chunk:
            for _ in range(2):
                p20.aspirate(20, well)
                p20.dispense(20, pool)
        p20.drop_tip() if real_mode else p20.return_tip()

    for pool in all_pools:
        pick_up(p20)
        p20.aspirate(10, formic_acid)
        p20.dispense(10, pool)
        p20.mix(3, 20, pool)
        p20.drop_tip() if real_mode else p20.return_tip()
