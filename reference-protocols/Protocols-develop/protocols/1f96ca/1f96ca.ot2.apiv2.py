from opentrons.protocol_api.labware import OutOfTipsError
import math

metadata = {
    'protocolName': '''NGS Library Prep: KAPA Hyper Plus 96rx, cat#07962428001,
     ROCHE - part 1 of 2''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [dry_time, bead_pellet_clearance, engage_time, dna_aspirate_clearance,
     labware_dna_sample_plate, labware_pre_pcr_plate,
     labware_tube_strip_or_plate, sample_count
     ] = get_values(  # noqa: F821
      'dry_time', 'bead_pellet_clearance', 'engage_time',
      'dna_aspirate_clearance', 'labware_dna_sample_plate',
      'labware_pre_pcr_plate', 'labware_tube_strip_or_plate', 'sample_count')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=12)
    if sample_count < 1 or sample_count > 96:
        raise Exception('Invalid number of DNA samples (must be 1-96).')

    num_cols = math.ceil(sample_count / 8)

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

    def replace_labware(slot_number, new_labware):
        del ctx.deck[str(slot_number)]
        return ctx.load_labware(new_labware, str(slot_number))

    pause_attention("Please unseal the pre-PCR plate.")

    # tips, p20 single, p300 multi
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", slot) for slot in ['3', '6']]
    tips300 = [ctx.load_labware("opentrons_96_filtertiprack_200ul", '4')]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # aluminum block holding reagent tube strips
    reagent_block = ctx.load_labware(labware_tube_strip_or_plate, '5')
    [frag_mm, erat_mm, liga_mm, beads, water, kapa_mix] = [
     reagent_block.columns_by_name()[str(name + 1)] for name in [*range(6)]]

    # thermocycler pre-chilled block (4), pre-PCR plate
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    pcr_plate = pre_pcr_plate = tc.load_labware(labware_pre_pcr_plate)
    tc.set_block_temperature(4)

    # magnetic module disengaged
    mag = ctx.load_module('magnetic module gen2', 9)
    mag_plate = mag.load_labware(labware_pre_pcr_plate)
    mag.disengage()

    # DNA sample plate, new pre-PCR plate
    temporary_plate = ctx.load_labware(labware_dna_sample_plate, '1')
    dna = new_pre_pcr_plate = temporary_plate.columns()[:num_cols]

    # reservoir for etoh and waste
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", '2')
    [etoh, waste] = [reservoir.wells_by_name()[well] for well in ['A1', 'A3']]

    # mix Frag-MM, 3 ul Frag-MM to pre-PCR plate, add 7 ul DNA
    pause_attention("Please add Frag-MM strip tubes to the block.")
    p20m.distribute(
     3, frag_mm[0].bottom(2),
     [column[0].bottom(2) for column in pre_pcr_plate.columns()[:num_cols]],
     mix_before=(5, 18))
    p20m.transfer(
     7, [column[0].bottom(dna_aspirate_clearance) for column in dna],
     [column[0].bottom(2) for column in pre_pcr_plate.columns()[:num_cols]],
     new_tip='always')
    pause_attention("Please seal the pre-PCR plate.")

    # close cycler lid, hold at 4 degrees C for 15 seconds
    tc.close_lid()
    ctx.delay(seconds=15)

    # 37 degrees C 8 minutes, return to 4 degrees, open lid
    profile = [{'temperature': 37, 'hold_time_minutes': 8}]
    tc.execute_profile(steps=profile, repetitions=1, block_max_volume=10)
    tc.set_block_temperature(4)
    tc.open_lid()
    pause_attention(
     """Please unseal the pre-PCR plate. Please replenish the p20 tip boxes.
     Please add ERAT-mm strip tubes to the block.""")
    p20m.reset_tipracks()

    # add 2 ul ERAT-MM
    p20m.transfer(
     2, erat_mm[0].bottom(2),
     [column[0].bottom(2) for column in pre_pcr_plate.columns()[:num_cols]],
     new_tip='always')

    # close lid, heat lid to 85 degrees C
    pause_attention("Please seal the pre-PCR plate.")

    tc.close_lid()
    tc.set_lid_temperature(85)

    # 65 degrees C 30 min, block to 4 degrees C, open lid
    profile = [{'temperature': 65, 'hold_time_minutes': 30}]
    tc.execute_profile(steps=profile, repetitions=1, block_max_volume=12)
    tc.set_block_temperature(4)
    tc.deactivate_lid()
    tc.open_lid()
    pause_attention("""Please unseal the pre-PCR plate. Please add Liga-MM
    strip tubes to the block.""")

    # add 10 ul Liga-MM
    p20m.transfer(
     10, liga_mm[0].bottom(2),
     [column[0].bottom(2) for column in pre_pcr_plate.columns()[:num_cols]],
     new_tip='always')

    # 20 degrees C 1 hour
    pause_attention("Please seal the pre-PCR plate.")
    tc.close_lid()
    tc.set_block_temperature(20)
    ctx.delay(minutes=60)

    # post ligation clean up
    pause_attention("""Please remove pre-PCR plate from thermocycler module and
    place it on the magnetic module. Please replenish the p20 tip boxes. Please
    add the beads strip tube and water strip tube to the block.""")
    p20m.reset_tipracks()

    # add beads, mix, wait
    p20m.transfer(
     17.6, beads[0].bottom(2),
     [column[0].bottom(2) for column in mag_plate.columns()[:num_cols]],
     mix_after=(20, 20), new_tip='always')
    ctx.delay(minutes=15)

    # engage magnets, wait, remove supernatant
    mag.engage()
    ctx.delay(minutes=engage_time)
    p300m.transfer(40, [
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
    tc.open_lid()
    pause_attention("""Please place a fresh pre-PCR plate in deck slot 1.
    Please replenish the p20 multi tips in deck slot 3 only. Please remove the
    second 20 ul tip box in deck slot 6 and replace it with the P7 index plate.
    Please place a fresh PCR plate on the thermocycler block.""")

    # delete p20 tip box in slot 6, replace with P7 index plate
    tips20.pop(tips20.index(tips20[1]))
    p20m.reset_tipracks()
    p5_index_plate = p7_index_plate = replace_labware(6, labware_pre_pcr_plate)

    # recover eluate to new pre-PCR plate
    p20m.transfer(
     10, [column[0].bottom(1) for column in mag_plate.columns()[:num_cols]],
     [column[0].bottom(2) for column in new_pre_pcr_plate], new_tip='always')

    pause_attention("""Please replenish the p20 tip box. Please add the KAPA
    mix strip tube to the block.""")
    p20m.reset_tipracks()

    # distribute kapa mix to fresh pcr plate on the thermocycler
    p20m.distribute(
     6, kapa_mix[0].bottom(2), [
      column[0].bottom(2) for column in pcr_plate.columns()[:num_cols]])

    pause_attention("Please replenish the p20 tip box.")
    p20m.reset_tipracks()

    # add 4 ul purified library
    p20m.transfer(
     4, [column[0].bottom(2) for column in new_pre_pcr_plate],
     [column[0].bottom(2) for column in pcr_plate.columns()[:num_cols]],
     new_tip='always')

    pause_attention("Please replenish the p20 tip box.")
    p20m.reset_tipracks()

    # add 1 ul P7
    p20m.transfer(1, [
     column[0].bottom(2) for column in p7_index_plate.columns()[:num_cols]],
     [column[0].bottom(2) for column in pcr_plate.columns()[:num_cols]],
     new_tip='always')

    pause_attention("""Please replenish the p20 tip box. Please remove the P7
    plate from the deck and replace it with the P5 plate.""")
    p20m.reset_tipracks()

    # add 1 ul P5
    p20m.transfer(1, [
     column[0].bottom(2) for column in p5_index_plate.columns()[:num_cols]],
     [column[0].bottom(2) for column in pcr_plate.columns()[:num_cols]],
     new_tip='always')

    pause_attention("""Please seal, vortex and spin the PCR plate and then
    return it to the thermocycler module.""")

    # cycling profiles
    profiles = [
     [{'temperature': temp, 'hold_time_seconds': sec} for temp, sec in zip(
      [98], [45])], [
      {'temperature': temp, 'hold_time_seconds': sec} for temp, sec in zip(
       [98, 60, 72], [15, 30, 30])], [
      {'temperature': temp, 'hold_time_seconds': sec} for temp, sec in zip(
       [72], [30])]]

    # run pcr
    tc.close_lid()
    tc.set_lid_temperature(105)
    for profile, reps in zip(profiles, [1, 15, 1]):
        tc.execute_profile(
         steps=profile, repetitions=reps, block_max_volume=12)
    tc.set_block_temperature(4)
    tc.deactivate_lid()
    pause_attention("""PCR steps are complete. Click resume to open the cycler
    and finish the protocol run. Please move the PCR plate to the post PCR OT-2
    for part 2 (post-amplification clean up and pooling).""")
    tc.open_lid()
    tc.deactivate_block()
