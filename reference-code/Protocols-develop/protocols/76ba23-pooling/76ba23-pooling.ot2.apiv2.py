metadata = {
    'protocolName': 'Pooling and Clean Up',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    ctx.set_rail_lights(True)

    # uploaded parameter values
    [dry_time, plate_count, tip_rack_300, tip_rack_10
     ] = get_values(  # noqa: F821
        "dry_time", "plate_count", "tip_rack_300", "tip_rack_10")

    # tips
    tips10 = [ctx.load_labware(tip_rack_10, str(slot)) for slot in [8, 7]]

    tips300 = [ctx.load_labware(tip_rack_300, str(slot)) for slot in [3]]
    tip_max = tips300[0].wells_by_name()['A1'].max_volume

    # pipettes
    p300s, p10s = [ctx.load_instrument(
     pipette, side, tip_racks=tips) for pipette, side, tips in zip(
     ['p300_single_gen2', 'p10_single'],
     ['left', 'right'], [tips300, tips10])]

    # labware
    [pcr2_plate_1, tube_rack, trough] = [
     ctx.load_labware(labware, slot) for labware, slot in zip(
        ["nest_96_wellplate_100ul_pcr_full_skirt",
         "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
         "nest_12_reservoir_15ml"],
        [str(num) for num in [2, 1, 6]])]

    # magnetic module with deep well plate
    mag = ctx.load_module('magnetic module gen2', '4')
    mag.disengage()
    mag_plate = mag.load_labware('usascientific_96_wellplate_2.4ml_deep')
    mag_height = {
        'omni_96_wellplate_2000ul': 8.5,
        'nest_96_wellplate_2ml_deep': 8.5,
        'usascientific_96_wellplate_2.4ml_deep': 8.5
        }

    # output pools 1 and 2 (optional) in A1, A2 of tube rack in slot 1
    pool_1, pool_2 = [tube_rack.wells_by_name()[well] for well in ['A1', 'A2']]

    # clean up 1 and 2, beads, etoh, water in magnetic module A1,A2,A3,A4,A5
    pool_1_clean_up, pool_2_clean_up, beads, etoh, water = [
     mag_plate.wells_by_name()[
      well] for well in ['A1', 'A2', 'A3', 'A4', 'A5']]

    # waste in trough well A1 in slot 6
    waste = trough.wells_by_name()['A1']

    # for optional 2nd PCR 2 plate in slot 5
    pcr2_plates = [pcr2_plate_1]
    pools_clean_up = [pool_1_clean_up]
    pools = [pool_1]
    if plate_count == 2:
        pools.append(pool_2)
        pools_clean_up.append(pool_2_clean_up)
        pcr2_plate_2 = ctx.load_labware(
         "nest_96_wellplate_100ul_pcr_full_skirt", '5')
        pcr2_plates.append(pcr2_plate_2)

    # pool 5 ul of each PCR2 product into a single pool (for each plate)
    for index, plate in enumerate(pcr2_plates):
        p10s.transfer(
         5, plate.wells(), pools_clean_up[index], new_tip='always')

    ctx.pause("""Please vortex the beads and add to well A3 on the
                 magnetic module. Click resume.""")

    # helper function for repeat large vol transfers
    def rep_max_transfer(remaining, source, dest, tip_max_vol=tip_max, air=0):
        vol = tip_max_vol - air
        while remaining > vol:
            p300s.aspirate(vol, source)
            if air > 0:
                p300s.air_gap(air)
            p300s.dispense(tip_max_vol, dest)
            remaining -= vol
        p300s.aspirate(remaining, source)
        if air > 0:
            p300s.air_gap(air)
        p300s.dispense(remaining + air, dest)

    # add 864 ul beads (1.8X) to each pool
    for index, pool in enumerate(pools_clean_up):
        p300s.pick_up_tip()
        p300s.mix(5, 200, beads)
        rep_max_transfer(864, beads, pool)
        p300s.drop_tip()

    ctx.delay(minutes=5)

    mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
    ctx.delay(minutes=7)

    # remove sup
    for index, pool in enumerate(pools_clean_up):
        p300s.pick_up_tip()
        rep_max_transfer(1344, pool, waste)
        p300s.drop_tip()

    # wash twice with 70 percent etoh, remove final traces of sup
    for rep in range(2):
        p300s.pick_up_tip()
        for index, pool in enumerate(pools_clean_up):
            p300s.transfer(
             [100, 100], [etoh, etoh], pool.top(), air_gap=25, new_tip='never')
        p300s.drop_tip()
        ctx.delay(seconds=15)
        for index, pool in enumerate(pools_clean_up):
            p300s.pick_up_tip()
            p300s.transfer(
             [100, 100], [pool, pool], waste, air_gap=25, new_tip='never')
            if rep == 1:
                p300s.transfer(
                 50, pool, waste, air_gap=20, new_tip='never')
            p300s.drop_tip()

    # air dry beads
    mag.disengage()
    ctx.delay(minutes=dry_time)

    # elute
    for index, pool in enumerate(pools_clean_up):
        p300s.transfer(
         22, water, pool.top(), mix_after=(3, 15), new_tip='always')

    ctx.delay(minutes=2)
    mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
    ctx.delay(minutes=5)

    for index, pool in enumerate(pools_clean_up):
        p300s.transfer(22, pool, pools[index], new_tip='always')
