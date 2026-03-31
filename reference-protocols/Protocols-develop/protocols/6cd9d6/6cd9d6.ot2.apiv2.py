from opentrons import types, protocol_api
import math

metadata = {
    'protocolName': 'Custom NGS Library Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [m20_mount, m300_mount, samples] = get_values(  # noqa: F821
        "m20_mount", "m300_mount", "samples")

    cols = math.ceil(samples/8)

    # Load Modules
    temperature_module_a = ctx.load_module('temperature module gen2', 1)
    temperature_module_b = ctx.load_module('temperature module gen2', 3)
    mag_mod = ctx.load_module('magnetic module gen2', 4)
    mag_plate = mag_mod.load_labware('biorad_96_wellplate_200ul_pcr')

    # Load Labware
    temp_plate_a = temperature_module_a.load_labware(
                    'biorad_96_wellplate_200ul_pcr')
    temp_plate_b = temperature_module_b.load_labware(
                    'opentrons_96_aluminumblock_generic_pcr_strip_200ul')
    reagent2_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 2)

    tipracks200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                   for slot in [7, 8]]
    tipracks20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
                  for slot in [10, 11]]
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
        while vol > 200:
            pip.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            pip.dispense(200, dest)
            pip.aspirate(10, dest)
            vol -= 200
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
    sample_wells = temp_plate_a.rows()[0][:cols]
    reagent1 = temp_plate_b['A1']
    reagent2 = reagent2_plate['A1']

    # Protocol Steps
    # Set both Temp Mods to 4C
    temperature_module_a.set_temperature(4)
    temperature_module_b.set_temperature(4)

    # Step 1: Transfer Reagent 1 to Samples
    for col in sample_wells:
        pick_up(m20)
        m20.flow_rate.aspirate = 5
        m20.flow_rate.dispense = 5
        aspirate_with_delay(m20, 2, reagent1, 1)
        dispense_with_delay(m20, 2, col, 1)
        m20.drop_tip()
    reset_pipette_speed(m20)

    # Step 2: Transfer Reagent 2 to Samples
    for col in sample_wells:
        pick_up(m20)
        m20.flow_rate.aspirate = 4
        m20.flow_rate.dispense = 4
        aspirate_with_delay(m20, 12, reagent2, 2)
        dispense_with_delay(m20, 12, col, 2)
        m20.drop_tip()
    reset_pipette_speed(m20)

    ctx.pause('''Seal the sample plate. Mix, Spin down and place in a thermocycler.
              Return sample plate to the magnetic module once completed.
              Remove plates/strips containing Reagents 1 and 2.  Place the
              12-channel reservoir on the temperature module in Slot 1. Place
              the Primer Plate on the temperature module in Slot 3. Place empty
              indexing plate in Slot 2. Click Resume when ready to proceed.''')

    # Swapping Labware at Pause
    del ctx.deck[str(1)]
    temperature_module_a = ctx.load_module('temperature module gen2', 1)
    reservoir = temperature_module_a.load_labware('nest_12_reservoir_15ml')
    ethanol = ctx.load_labware('nest_1_reservoir_195ml', 6)['A1']

    del ctx.deck[str(3)]
    temperature_module_b = ctx.load_module('temperature module gen2', 3)
    primer = temperature_module_b.load_labware('biorad_96_wellplate_200ul_pcr')

    indexing_plate = replace_labware(2, 'biorad_96_wellplate_200ul_pcr')

    # Wells
    mag_plate_wells = mag_plate.rows()[0][:cols]
    buffer1Track = VolTracker(reservoir, 1008, 'multi', start=8, end=10,
                              msg='Replenish Buffer 1')
    spriTrack = VolTracker(reservoir, 1140, 'multi', start=0, end=8,
                           msg='Replenish SPRI')
    mmTrack = VolTracker(reservoir, 1200, 'multi', start=10, end=12,
                         msg='Master Mix Track')
    indexing_plate_wells = indexing_plate.rows()[0][:cols]
    primer_plate_wells = primer.rows()[0][:cols]
    side_x = 1
    sides = [-side_x, side_x] * (cols // 2)

    # Continue Protocol
    # Step 3: Add SPRI solution to Samples
    for col in mag_plate_wells:
        pick_up(m300)
        m300.transfer(95, spriTrack.tracker(95), col, new_tip='never',
                      mix_after=(5, 60))
        m300.drop_tip()

    # Step 4: Incubate SPRI at RT
    ctx.delay(minutes=10, msg='''Allowing the mixed SPRI reaction to incubate
                                 for 10 minutes at Room Temperature.''')

    # Step 5: Engage Magnet
    mag_mod.engage()
    ctx.delay(minutes=3, msg="Concentrating the beads for 3 minutes.")

    # Step 6: Remove Supernatant from samples
    for col, side in zip(mag_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(m300, 130, col, trash, side)
        m300.drop_tip()

    # Step 10: Repeat Ethanol Wash
    for _ in range(2):
        # Step 7: Add Ethanol to sammples
        for col in mag_plate_wells:
            pick_up(m300)
            m300.transfer(180, ethanol, col, new_tip='never')
            m300.drop_tip()

        # Step 8: Allow ethanol to sit
        ctx.delay(minutes=1, msg="Allowing Ethanol to sit for 1 minute.")

        # Step 9: Remove Supernatant from samples
        for col, side in zip(mag_plate_wells, sides):
            pick_up(m300)
            remove_supernatant(m300, 190, col, trash, side)
            m300.drop_tip()

    # Step 11: Remove Supernatant from samples
    for col, side in zip(mag_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(m300, 130, col, trash, side)
        m300.drop_tip()

    # Step 12: Allow beads to dry
    ctx.delay(minutes=5, msg='Allowing beads to dry...')

    # Step 13: Transfer Buffer 1 to samples
    for col in mag_plate_wells:
        pick_up(m300)
        m300.transfer(21, buffer1Track.tracker(21), col, new_tip='never',
                      mix_after=(5, 15))
        m300.drop_tip()

    # Step 14: Allow beads to incubate
    ctx.delay(minutes=5, msg='''Allow beads to incubate for
                             5 minutes at Room Temperature''')

    # Step 15: Add PCR Master Mix to indexing plate
    pick_up(m300)
    for col in indexing_plate_wells:
        m300.transfer(25, mmTrack.tracker(25), col, new_tip='never')
    m300.drop_tip()

    # Step 16: Transfer Primer Mix to Indexing Plate
    for src, dest in zip(primer_plate_wells, indexing_plate_wells):
        pick_up(m20)
        m20.transfer(5, src, dest, new_tip='never')
        m20.drop_tip()

    # Step 17: Concentrate sample plate beads
    ctx.delay(minutes=3, msg='''Concentrate beads for 3 minutes''')

    # Step 18: Transfer supernatant from samples to indexing plate
    for src, dest, side in zip(mag_plate_wells, indexing_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(m300, 20, src, dest, side)
        m300.drop_tip()
