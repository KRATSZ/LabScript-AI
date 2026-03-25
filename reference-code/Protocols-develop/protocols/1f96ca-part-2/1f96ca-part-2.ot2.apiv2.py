from opentrons.protocol_api.labware import OutOfTipsError
import math

metadata = {
    'protocolName': '''NGS Library Prep: KAPA Hyper Plus 96rx, cat#07962428001,
    ROCHE - part 2 of 2: post-PCR clean up and pooling''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [labware_pool, dry_time, bead_pellet_clearance, engage_time,
     labware_pre_pcr_plate, labware_tube_strip_or_plate, sample_count
     ] = get_values(  # noqa: F821
      'labware_pool', 'dry_time', 'bead_pellet_clearance', 'engage_time',
      'labware_pre_pcr_plate', 'labware_tube_strip_or_plate', 'sample_count')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if sample_count < 1 or sample_count > 96:
        raise Exception('Invalid number of DNA samples (must be 1-96).')

    num_cols = math.ceil(sample_count / 8)

    # tips, p20 single, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", slot) for slot in [
      '3', '4', '7', '8']]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", slot) for slot in [
      '10', '11']]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # define helper functions
    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    def pick_up_or_refill(current_pipette):
        try:
            current_pipette.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             "Please Refill the {} Tip Box".format(current_pipette))
            current_pipette.reset_tipracks()
            current_pipette.pick_up_tip()

    def pre_wet(volume, location):
        for rep in range(2):
            p300m.aspirate(volume, location)
            p300m.dispense(volume, location)

    def etoh_settings():
        p300m.flow_rate.dispense = 300
        p300m.flow_rate.blow_out = 300

    def default_settings():
        p300m.flow_rate.dispense = 94
        p300m.flow_rate.blow_out = 94

    def etoh_transfer(volume, source, dest):
        p300m.aspirate(volume, source)
        p300m.air_gap(15)
        p300m.dispense(volume, dest)
        if dest != waste.top():
            for rep in range(3):
                if rep != 0:
                    p300m.aspirate(100, column[0].top())
                ctx.delay(seconds=1)
                p300m.blow_out()
    """
    pick_up() function to use only the rear-most channel of the p20 multi
    """
    num_channels_per_pickup = 1  # (only pickup tips on rear-most channel)
    tips_ordered = [
        tip for rack in tips300[:1]
        for row in rack.rows(
        )[len(rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]
        for tip in row[2:]]

    tip_count = 0

    def pick_up(pip):
        nonlocal tip_count
        pip.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    pause_attention(
     """Please unseal the PCR plate and place it on the magnetic module.
     Please place the beads, water and intermediate_pools strip tubes on
     the block.""")

    # aluminum block holding reagent tube strips
    reagent_block = ctx.load_labware(labware_tube_strip_or_plate, '5')
    [beads, water, intermediate_pools] = [
     reagent_block.columns_by_name()[str(name + 1)] for name in [*range(3)]]

    # magnetic module disengaged
    mag = ctx.load_module('magnetic module gen2', 9)
    mag_plate = mag.load_labware(labware_pre_pcr_plate)
    mag.disengage()

    # post-PCR plate
    temporary_plate = ctx.load_labware(labware_pre_pcr_plate, '1')
    post_pcr_plate = temporary_plate.columns()[:num_cols]

    # reservoir for etoh and waste
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", '2')
    [etoh, waste] = [reservoir.wells_by_name()[well] for well in ['A1', 'A3']]

    # pool tube
    tube_rack = ctx.load_labware(labware_pool, '6')
    pool = tube_rack.wells_by_name()['A1']

    # add 9.6 ul beads, mix, wait, engage magnets, wait, remove sup
    p20m.transfer(
     9.6, beads[0].bottom(2),
     [column[0].bottom(2) for column in mag_plate.columns()[:num_cols]],
     mix_after=(20, 11), new_tip='always')
    ctx.delay(minutes=15)
    mag.engage()
    ctx.delay(minutes=engage_time)
    p300m.transfer(22, [
     column[0].bottom(bead_pellet_clearance) for column in mag_plate.columns()[
      :num_cols]], waste.top(), new_tip='always')

    # add 80% ethanol, wait, remove supernatant, repeat
    etoh_settings()
    for rep, vol in zip([*range(2)], [(100, 150), (60, 100)]):
        pick_up_or_refill(p300m)
        pre_wet(100, etoh.bottom(2))
        for column in mag_plate.columns()[:num_cols]:
            etoh_transfer(vol[0], etoh.bottom(2), column[0].top())
        p300m.drop_tip()
        ctx.delay(seconds=30)
        for column in mag_plate.columns()[:num_cols]:
            pick_up_or_refill(p300m)
            pre_wet(100, etoh.bottom(2))
            etoh_transfer(vol[1], column[0].bottom(1), waste.top())
            p300m.drop_tip()
    default_settings()

    # wait for beads to dry, disengage magnets, elute
    ctx.delay(minutes=dry_time)
    mag.disengage()
    p20m.transfer(10, water[0].bottom(2), [
     column[0].bottom(2) for column in mag_plate.columns()[:num_cols]],
     mix_after=(5, 5), new_tip='always')
    ctx.delay(minutes=20)
    mag.engage()
    ctx.delay(minutes=engage_time)
    pause_attention("Please place a fresh post-PCR plate in deck slot 1.")

    # recover eluate to post-PCR plate
    p20m.transfer(10, [column[0].bottom(1) for column in mag_plate.columns()[
     :num_cols]], [column[0].bottom(2) for column in post_pcr_plate],
     new_tip='always')

    # transfer 4 ul of each library to intermediate pool
    p20m.transfer(
     4, [column[0].bottom(2) for column in post_pcr_plate],
     intermediate_pools[0].bottom(2), new_tip='always')

    # combine intermediate pools using one-tip pickup with p300 multi-channel
    for well in intermediate_pools:
        pick_up(p300m)
        p300m.aspirate(num_cols*4, well.bottom(1))
        p300m.dispense(num_cols*4, pool.center())
        p300m.blow_out()
        p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
        p300m.drop_tip()
