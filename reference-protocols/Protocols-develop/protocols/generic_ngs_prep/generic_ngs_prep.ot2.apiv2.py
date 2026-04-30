from opentrons import types, protocol_api
import math

metadata = {
    'protocolName': 'Generic NGS Library Prep',
    'author': 'Opentrons',
    'description': 'Generic NGS library prep with optional temp mods',
    'apiLevel': '2.10'
}


def run(ctx):
    [m20_mount,
     m300_mount,
     n_samples,
     temp_mod_s1_lname,
     temp_mod_s4_lname,
     temp_mod_s7_lname,
     temp_s1_part1,
     temp_s4_part1,
     temp_s7_part1,
     temp_s1_part2,
     temp_s4_part2,
     temp_s7_part2,
     samples_loadname,
     reagent1_loadname,
     reagent2_loadname,
     indexing_plate_loadname,
     reservoir_loadname,
     ethanol_res_loadname,
     primer_loadname,
     reag1_vol,
     reag2_vol,
     ethanol_wash_vol,
     mastermix_vol,
     primer_mix_vol,
     bead_vol,
     sample_vol,
     elution_buffer_vol,
     DNA_supernat_vol] = \
        get_values(  # noqa: F821
        "m20_mount",
        "m300_mount",
        "n_samples",
        "temp_mod_s1_lname",
        "temp_mod_s4_lname",
        "temp_mod_s7_lname",
        "temp_s1_part1",
        "temp_s4_part1",
        "temp_s7_part1",
        "temp_s1_part2",
        "temp_s4_part2",
        "temp_s7_part2",
        "samples_loadname",
        "reagent1_loadname",
        "reagent2_loadname",
        "indexing_plate_loadname",
        "reservoir_loadname",
        "ethanol_res_loadname",
        "primer_loadname",
        "reag1_vol",
        "reag2_vol",
        "ethanol_wash_vol",
        "mastermix_vol",
        "primer_mix_vol",
        "bead_vol",
        "sample_vol",
        "elution_buffer_vol",
        "DNA_supernat_vol")

    n_cols = math.ceil(n_samples/8)
    # Deck placement: slots
    mag_slot = 3
    m20_tip_slots = [10, 11]
    m300_tip_slots = [8, 9]
    ethanol_slot = 6

    # Load Modules
    temp_mod_list = []

    for temp_mod, slot in \
            zip([temp_mod_s1_lname, temp_mod_s4_lname, temp_mod_s7_lname],
                ['1', '4', '7']):
        if temp_mod:
            temp_mod_list.append((ctx.load_module(temp_mod, slot)))
        else:
            temp_mod_list.append(None)

    [temperature_mod_slot1,
     temperature_mod_slot4,
     temperature_module_slot7] = \
        [temp_mod_list[0],
         temp_mod_list[1],
         temp_mod_list[2]]

    mag_mod = ctx.load_module('magnetic module gen2', mag_slot)
    mag_plate = mag_mod.load_labware(samples_loadname)

    # Load Labware
    labware_list = []
    for temp_mod, load_name, slot in \
            (zip([temperature_mod_slot1, temperature_mod_slot4,
                  temperature_module_slot7, None],
                 [samples_loadname, reagent1_loadname,
                  reagent2_loadname, reservoir_loadname],
                 ['1', '4', '7', '2'])):
        if temp_mod:
            labware_list.append(temp_mod.load_labware(load_name))
        else:
            labware_list.append(ctx.load_labware(load_name, slot))
    temp_plate_a_samples = labware_list[0]
    temp_plate_b_reagent1 = labware_list[1]
    reagent2_plate = labware_list[2]
    reservoir = labware_list[3]

    [temp_plate_a_samples, temp_plate_b_reagent1, reagent2_plate] = \
        [labware_list[0], labware_list[1], labware_list[2]]

    tipracks200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                   for slot in [m300_tip_slots[0], m300_tip_slots[1]]]
    tipracks20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
                  for slot in [m20_tip_slots[0], m20_tip_slots[1]]]
    trash = ctx.deck['12']['A1']

    # Load Pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tipracks20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks200)

    # Helper Functions
    def replace_labware(slot_number, new_labware):
        del ctx.deck[str(slot_number)]
        return ctx.load_labware(new_labware, str(slot_number))

    def aspirate_with_delay(pipette, volume, source, delay_seconds):
        pipette.aspirate(volume, source)
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)

    def dispense_with_delay(pipette, volume, dest, delay_seconds):
        pipette.dispense(volume, dest)
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Replace the empty tips!")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def reset_pipette_speed(pipette):
        if pipette.name == 'p300_multi_gen2':
            pipette.flow_rate.aspirate = 94
            pipette.flow_rate.dispense = 94
        elif pipette.name == 'p20_multi_gen2':
            pipette.flow_rate.aspirate = 7.6
            pipette.flow_rate.dispense = 7.6

    def remove_supernatant(pip, vol, src, dest, side, mode=None):
        if mode == 'elution':
            pip.flow_rate.aspirate = 10
        else:
            pip.flow_rate.aspirate = 20
        while vol > 190:
            pip.aspirate(
                190, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            pip.dispense(200, dest)
            pip.aspirate(10, dest)
            vol -= 190
        pip.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        pip.dispense(vol, dest)
        if dest == trash:
            pip.blow_out()
        pip.flow_rate.aspirate = 50

    # Volume Tracking
    class VolTracker:
        def __init__(self, labware, well_vol, pip_type='single',
                     mode='reagent', start=0, end=12, msg='Reset Labware'):
            try:
                self.labware_wells = dict.fromkeys(
                    labware.wells()[start:end], 0)
            except Exception:
                self.labware_wells = dict.fromkeys(
                    labware, 0)
            self.labware_wells_backup = self.labware_wells.copy()
            self.well_vol = well_vol
            self.pip_type = pip_type
            self.mode = mode
            self.start = start
            self.end = end
            self.msg = msg

        def tracker(self, vol):
            '''tracker() will track how much liquid
            was used up per well. If the volume of
            a given well is greater than self.well_vol
            it will remove it from the dictionary and iterate
            to the next well which will act as the reservoir.'''
            well = next(iter(self.labware_wells))
            if self.labware_wells[well] + vol >= self.well_vol:
                del self.labware_wells[well]
                if len(self.labware_wells) < 1:
                    ctx.pause(self.msg)
                    self.labware_wells = self.labware_wells_backup.copy()
                well = next(iter(self.labware_wells))
            if self.pip_type == 'multi':
                self.labware_wells[well] = self.labware_wells[well] + vol*8
            elif self.pip_type == 'single':
                self.labware_wells[well] = self.labware_wells[well] + vol
            if self.mode == 'waste':
                ctx.comment(f'''{well}: {int(self.labware_wells[well])} uL of
                            total waste''')
            else:
                ctx.comment(f'''{int(self.labware_wells[well])} uL of liquid
                            used from {well}''')
            return well

    # Wells
    sample_wells = temp_plate_a_samples.rows()[0][:n_cols]
    reagent1 = temp_plate_b_reagent1['A1']
    reagent2 = reagent2_plate['A1']

    # Protocol Steps
    # Set both Temp Mods to 4C
    for tmod, temp in zip([temperature_mod_slot1, temperature_mod_slot4,
                           temperature_module_slot7],
                          [temp_s1_part1, temp_s4_part1, temp_s7_part1]):
        if tmod is not None:
            tmod.set_temperature(temp)

    # Step 1: Enzymatic reaction e.g. end repair or barcoding
    # Step 1.1: Transfer Reagent 1 to Samples
    pip = m300 if reag1_vol > 20 else m20
    for col in sample_wells:
        pick_up(pip)
        pip.flow_rate.aspirate = 5
        pip.flow_rate.dispense = 5
        aspirate_with_delay(pip, reag1_vol, reagent1, 1)
        dispense_with_delay(pip, reag1_vol, col, 1)
        pip.drop_tip()
    reset_pipette_speed(pip)

    # Step 1.2: Transfer Reagent 2 to Samples
    pip = m300 if reag2_vol > 20 else m20
    for col in sample_wells:
        pick_up(pip)
        pip.flow_rate.aspirate = 4
        pip.flow_rate.dispense = 4
        aspirate_with_delay(pip, reag2_vol, reagent2, 2)
        dispense_with_delay(pip, reag2_vol, col, 2)
        pip.drop_tip()
    reset_pipette_speed(pip)

    ctx.pause('''Seal the sample plate. Mix, Spin down and place in a thermocycler.
              Return sample plate to the magnetic module once completed.
              Remove plates/strips containing Reagents 1 and 2.  Place the
              12-channel reservoir on the temperature module in Slot 1. Place
              the Primer Plate on the temperature module in Slot 3. Place empty
              indexing plate in Slot 7. Click Resume when ready to proceed.''')

    # Swapping Labware at Pause
    labware_list = []
    temp_mod_list = []

    for slot, temp_mod_loadname, load_name in zip(['4', '7',
                                                  ethanol_slot],
                                                  [temp_mod_s4_lname,
                                                  temp_mod_s7_lname,
                                                  None],
                                                  [primer_loadname,
                                                  indexing_plate_loadname,
                                                  ethanol_res_loadname]):
        del(ctx.deck[slot])
        if temp_mod_loadname:
            temp_mod = ctx.load_module(temp_mod_loadname, slot)
            temp_mod_list.append(temp_mod)
            labware = temp_mod.load_labware(load_name)
            labware_list.append(labware)
        else:
            labware_list.append(ctx.load_labware(load_name, slot))

    primer = labware_list[0]
    indexing_plate = labware_list[1]
    ethanol_reservoir = labware_list[2]
    ethanol = ethanol_reservoir.wells_by_name()['A1']

    # Wells
    mag_plate_wells = mag_plate.rows()[0][:n_cols]
    buffer1Track = VolTracker(reservoir, 1008, 'multi', start=8, end=10,
                              msg='Replenish Buffer 1')
    spriTrack = VolTracker(reservoir, 1140, 'multi', start=0, end=8,
                           msg='Replenish SPRI')
    mmTrack = VolTracker(reservoir, 1200, 'multi', start=10, end=12,
                         msg='Master Mix Track')
    indexing_plate_wells = indexing_plate.rows()[0][:n_cols]
    primer_plate_wells = primer.rows()[0][:n_cols]
    side_x = 1
    sides = [-side_x, side_x] * (n_cols // 2)

    # Continue Protocol with DNA purification using SPRI
    # Set temperatures for part 2
    for tmod, temp in zip([temperature_mod_slot1, temperature_mod_slot4,
                           temperature_module_slot7],
                          [temp_s1_part2, temp_s4_part2, temp_s7_part2]):
        if tmod is not None:
            tmod.set_temperature(temp)
    # Step 3: Add SPRI solution to Samples
    pip = m300 if bead_vol > 20 else m20
    for col in mag_plate_wells:
        pick_up(pip)
        pip.transfer(bead_vol, spriTrack.tracker(bead_vol), col,
                     new_tip='never',
                     mix_after=(5, (2*bead_vol)/3))
        pip.drop_tip()

    # Step 4: Incubate SPRI at RT
    ctx.delay(minutes=10, msg='''Allowing the mixed SPRI reaction to incubate
                                 for 10 minutes at Room Temperature.''')

    # Step 5: Engage Magnet
    mag_mod.engage()
    ctx.delay(minutes=3, msg="Concentrating the beads for 3 minutes.")

    # Step 6: Remove Supernatant from samples
    supernatant_volume = sample_vol + reag1_vol + reag2_vol + bead_vol
    pip = m300 if supernatant_volume > 20 else m20

    for col, side in zip(mag_plate_wells, sides):
        pick_up(pip)
        remove_supernatant(pip, supernatant_volume, col, trash, side)
        pip.drop_tip()

    # Step 10: Repeat Ethanol Wash
    for _ in range(2):
        # Step 7: Add Ethanol to sammples
        pip = m300 if ethanol_wash_vol > 20 else m20
        for col in mag_plate_wells:
            pick_up(pip)
            pip.transfer(ethanol_wash_vol, ethanol, col, new_tip='never')
            pip.drop_tip()

        # Step 8: Allow ethanol to sit
        ctx.delay(minutes=1, msg="Allowing Ethanol to sit for 1 minute.")

        # Step 9: Remove Supernatant from samples
        pip = m300 if ethanol_wash_vol+10 > 20 else m20
        for col, side in zip(mag_plate_wells, sides):
            pick_up(pip)
            remove_supernatant(pip, ethanol_wash_vol+10, col, trash, side)
            pip.drop_tip()

    # Step 11: Remove any remaining supernatant from samples
    for col, side in zip(mag_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(m300, 130, col, trash, side)
        m300.drop_tip()

    # Step 12: Allow beads to dry
    ctx.delay(minutes=5, msg='Allowing beads to dry...')

    # Step 13: Transfer elution buffer to samples
    pip = m300 if elution_buffer_vol > 20 else m20
    for col in mag_plate_wells:
        pick_up(pip)
        pip.transfer(elution_buffer_vol,
                     buffer1Track.tracker(elution_buffer_vol),
                     col, new_tip='never',
                     mix_after=(5, (2*elution_buffer_vol)/3))
        pip.drop_tip()

    # Step 14: Allow beads to incubate
    ctx.delay(minutes=5, msg='''Allow beads to incubate for
                             5 minutes at Room Temperature''')

    # Step 15: Add PCR Master Mix to indexing plate
    pip = m300 if mastermix_vol > 20 else m20
    pick_up(pip)
    for col in indexing_plate_wells:
        pip.transfer(mastermix_vol, mmTrack.tracker(25), col, new_tip='never')
    pip.drop_tip()

    # Step 16: Transfer Primer Mix to Indexing Plate
    pip = m300 if primer_mix_vol > 20 else m20
    for src, dest in zip(primer_plate_wells, indexing_plate_wells):
        pick_up(pip)
        pip.transfer(primer_mix_vol, src, dest, new_tip='never')
        pip.drop_tip()

    # Step 17: Concentrate sample plate beads
    ctx.delay(minutes=3, msg='''Concentrate beads for 3 minutes''')

    # Step 18: Transfer supernatant from samples to indexing plate
    pip = m300 if DNA_supernat_vol > 20 else m20
    for src, dest, side in zip(mag_plate_wells, indexing_plate_wells, sides):
        pick_up(pip)
        remove_supernatant(pip, DNA_supernat_vol, src, dest, side)
        pip.drop_tip()
