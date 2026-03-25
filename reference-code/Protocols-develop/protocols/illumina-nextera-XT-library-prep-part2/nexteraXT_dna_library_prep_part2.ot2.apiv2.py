import math

metadata = {
    'protocolName': 'Illumina Nextera XT NGS Prep 2: Clean-Up Libraries',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.2'
    }


def run(protocol):
    [pip_type, pip_mount, mag_gen, no_of_samps, init_vol,
     bead_ratio, rsb_vol, final_vol, dry_time] = get_values(  # noqa: F821
     'pip_type', 'pip_mount', 'mag_gen', 'no_of_samps', 'init_vol',
     'bead_ratio', 'rsb_vol', 'final_vol', 'dry_time')

    # labware setup
    mag_deck = protocol.load_module(mag_gen, '4')
    mag_plate = mag_deck.load_labware('biorad_96_wellplate_200ul_pcr')
    in_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '5', 'Load Plate'
    )
    out_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '1', 'Final Plate (empty)'
    )
    trough = protocol.load_labware(
        'usascientific_12_reservoir_22ml', '2', 'Reservoir, 12-channel'
    )
    tip_no = no_of_samps * 4 + 3
    no_racks = tip_no//96 + (1 if tip_no % 96 > 0 else 0)
    tips = [
        protocol.load_labware('opentrons_96_tiprack_300ul', str(slot))
        for slot in range(6, 7+no_racks)
    ]

    pip = protocol.load_instrument(pip_type, pip_mount, tip_racks=tips)
    pipC = pip_type.split('_')[1]

    # Volume Tracking - adapted from Sakib
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
                    protocol.pause(self.msg)
                    self.labware_wells = self.labware_wells_backup.copy()
                well = next(iter(self.labware_wells))
            if self.pip_type == 'multi':
                self.labware_wells[well] = self.labware_wells[well] + vol*8
            elif self.pip_type == 'single':
                self.labware_wells[well] = self.labware_wells[well] + vol
            """
            Removed the display of comments
            """
            # if self.mode == 'waste':
            #     protocol.comment(f'''{well}: {int(self.labware_wells[well])}
            #         uL of total waste''')
            # else:
            #     protocol.comment(f'''{int(self.labware_wells[well])}
            #         uL of liquidused from {well}''')
            return well

    # reagent setup
    rsb = trough['A1']  # resuspension buffer
    beads = trough['A2']  # AMPure XP beads
    # 80% ethanol
    ethanol = VolTracker(
        trough, 14000, pipC, start=2, end=6, msg='Out of Ethanol; replace')
    # liquid waste
    liquid_trash = VolTracker(
        trough, 14500, pipC, start=8, end=12, msg='Empty liqud waste.')

    if pipC == 'multi':
        num_cols = math.ceil(no_of_samps/8)
        inputs = in_plate.rows()[0][:num_cols]
        mag = mag_plate.rows()[0][:num_cols]
        outputs = out_plate.rows()[0][:num_cols]
    else:
        inputs = [well for well in in_plate.wells()][:no_of_samps]
        mag = [well for well in mag_plate.wells()][:no_of_samps]
        outputs = [well for well in out_plate.wells()][:no_of_samps]

    bead_vol = init_vol*bead_ratio

    # Transfer PCR Product
    pip.transfer(init_vol, inputs, mag, new_tip='always')

    # Transfer beads to each well
    pip.distribute(bead_vol, beads, [well.top() for well in mag])

    total_vol = bead_vol + init_vol + 5

    protocol.pause("Shake at 1800 rpm for 2 minutes.")

    # Incubate at RT for 5 minutes
    protocol.delay(minutes=5)

    # Engage MagDeck for 2 minutes, remain engaged
    mag_deck.engage()
    protocol.delay(minutes=2)

    # Remove supernatant
    for well in mag:
        pip.transfer(total_vol, well, liquid_trash.tracker(total_vol).top())

    # Wash beads twice with 80% ethanol
    for cycle in range(1, 3):
        protocol.comment(f"\nBeginning ethanol wash {cycle}...\n")
        pip.pick_up_tip()
        for well in mag:
            pip.transfer(
                200, ethanol.tracker(200), well.top(), new_tip='never')
        pip.drop_tip()
        protocol.delay(seconds=30)
        for well in mag:
            pip.pick_up_tip()
            pip.transfer(
                220, well, liquid_trash.tracker(220).top(), new_tip='never')
            pip.drop_tip()

    # Air dry
    protocol.delay(minutes=dry_time)

    # Turn off MagDeck
    mag_deck.disengage()

    # Transfer RSB to well
    pip.pick_up_tip()
    pip.transfer(rsb_vol, rsb, [well.top() for well in mag], new_tip='never')
    pip.drop_tip()

    protocol.pause("Shake at 1800 rpm for 2 minutes.")

    # Turn on MagDeck for 2 minutes
    mag_deck.engage()
    protocol.delay(minutes=2)

    # Transfer supernatant to new PCR plate
    pip.transfer(final_vol, mag, outputs, new_tip='always')

    # Disengage MagDeck
    mag_deck.disengage()
