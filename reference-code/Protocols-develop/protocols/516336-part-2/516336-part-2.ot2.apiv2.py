from opentrons import protocol_api, types
import math

metadata = {
    'protocolName': 'Ligation Sequencing Kit: Adapter Ligation and Clean-Up',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [samples, m300_mount, p300_mount,
        mag_engage_height] = get_values(  # noqa: F821
        "samples", "m300_mount", "p300_mount", "mag_engage_height")

    cols = math.ceil(samples/8)

    # Load Labware
    mag_mod = ctx.load_module('magnetic module', '1')
    mag_plate = mag_mod.load_labware(
        'thermofisher_96_midi_storage_plate_800ul')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_rack = temp_mod.load_labware(
                            'opentrons_24_aluminumblock_generic_2ml_screwcap')
    sample_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr',
                                    2)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 4)
    tipracks_multi = [ctx.load_labware('opentrons_96_tiprack_300ul', slot) for
                      slot in [6, 9]]
    tipsracks_single = ctx.load_labware('opentrons_96_tiprack_300ul', 5)
    trash = ctx.loaded_labwares[12]['A1']

    # Load Pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks_multi)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tipsracks_single])

    # Reagents
    ampure_beads = reservoir['A12']
    elution_buff = reservoir['A5']
    mm = temp_rack['A1']

    # Sample Wells
    mag_plate_wells = mag_plate.rows()[0][:cols]
    sample_plate_wells = sample_plate.rows()[0][:cols]
    sample_plate_single_wells = sample_plate.wells()[:samples]

    # Helper Functions
    def pick_up(pip):
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def remove_supernatant(vol, src, dest, side):
        m300.flow_rate.aspirate = 20
        m300.aspirate(10, src.top())
        while vol > 300:
            m300.aspirate(
                300, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            m300.dispense(300, dest)
            m300.aspirate(10, dest)
            vol -= 300
        m300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        m300.dispense(vol, dest)
        m300.dispense(10, dest)
        m300.flow_rate.aspirate = 50

    sides = [-1, 1] * 6
    sides = sides[:cols]

    def magnet(delay_mins):
        mag_mod.engage(height_from_base=mag_engage_height)
        ctx.delay(minutes=delay_mins, msg='Allowing beads to settle.')

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
            if self.labware_wells[well] + vol >= 14800:
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

    fragBufferTrack = VolTracker(reservoir, 14900, 'multi', start=0, end=4,
                                 msg='Replenish Fragment Buffer')

    # PROTOCOL STEPS

    # Transfer Adapter Ligation Mix to Samples on PCR Plate (1)
    p300.transfer(40, mm, sample_plate_single_wells, new_tip='always',
                  mix_after=(3, 30))

    # Transfer Samples from Sample Plate to Mag Mod (2)
    for src, dest in zip(sample_plate_wells, mag_plate_wells):
        m300.pick_up_tip()
        m300.transfer(100, src, dest, new_tip='never')
        m300.drop_tip()

    # Add AMPure XP Beads to Mag Mod (3)
    for well in mag_plate_wells:
        pick_up(m300)
        m300.transfer(40, ampure_beads, well, new_tip='never',
                      mix_before=(3, 40), mix_after=(3, 50))
        m300.drop_tip()

    # Pause for Hula Mixer/Spin Down (4)
    ctx.pause('''Incubate on Hula Mixer for 5 minutes and spin down the samples.
                 Then place back on the magnet and click resume.''')

    # Engage Magnet and Delay for 5 Minutes (4)
    magnet(5)
    # Remove Supernatant (4)
    for well, side in zip(mag_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(100, well, trash, side)
        m300.drop_tip()

    # (5 x2)
    for _ in range(2):
        # Wash Beads with Fragment Buffer (5)
        for well in mag_plate_wells:
            pick_up(m300)
            m300.aspirate(250, fragBufferTrack.tracker(250))
            m300.dispense(250, well.top(-3))
            m300.mix(3, 100)
            m300.drop_tip()

        # Pellet Beads
        magnet(5)

        # Remove Supernatant (5)
        for well, side in zip(mag_plate_wells, sides):
            pick_up(m300)
            remove_supernatant(100, well, trash, side)
            m300.drop_tip()

    # Pause and Remove Samples for Spin Down (6)
    mag_mod.disengage()
    ctx.pause('''Spin down and place samples back on the maget.
              Then click resume.''')
    magnet(1)

    # Remove Residual Supernatant (6)
    for well, side in zip(mag_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(100, well, trash, side)
        m300.drop_tip()

    # Add 15 uL of Elution Buffer (7)
    mag_mod.disengage()
    pick_up(m300)
    for well in mag_plate_wells:
        m300.transfer(15, elution_buff, well.top(-3), mix_after=(3, 15),
                      new_tip='never')
    ctx.delay(minutes=10, msg='Incubating at Room Temperature for 10 minutes.')
    m300.drop_tip()

    # Engage Magnet (8)
    magnet(5)

    # Transfer Eluate into Final sample plate (9)
    ctx.pause('''Replace old BioRad PCR plate with new BioRad PCR plate for
              storing the new DNA library.''')
    for well, dest, side in zip(mag_plate_wells, sample_plate_wells, sides):
        pick_up(m300)
        remove_supernatant(15, well, dest, side)
        m300.drop_tip()

    temp_mod.deactivate()
    mag_mod.disengage()
