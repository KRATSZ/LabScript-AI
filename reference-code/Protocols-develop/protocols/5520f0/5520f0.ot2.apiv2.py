metadata = {
    'protocolName': 'Staining Cell-Based Assay Plates',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [m300_mount, plates, new_tip, disp_speed,
        asp_height] = get_values(  # noqa: F821
        "m300_mount", "plates", "new_tip", "disp_speed",
        "asp_height")

    cols = 24

    # Load Labware
    plates = [ctx.load_labware(
              'perkinelmer_384_wellplate_145ul', slot)
              for slot in range(1, plates+1)]
    pbs_reservoir = ctx.load_labware('nest_1_reservoir_195ml', 7)
    reagent_reservoir = ctx.load_labware('nest_12_reservoir_15ml', 8)
    waste_reservoir = ctx.load_labware('nest_1_reservoir_195ml', 9)
    tipracks = [ctx.load_labware('opentrons_96_tiprack_300ul',
                                 slot) for slot in range(10, 12)]

    # Load Pipette
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks)

    # Single Well Reagents
    # primary_antibody = reagent_reservoir.rows()[0][4]
    # secondary_antibody = reagent_reservoir.rows()[0][5]

    # Wells
    # pbs_wells = pbs_reservoir.rows()[0] + reagent_reservoir.rows()[0][:6]

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

    # Volume Trackers for Multi-well Reagents
    wasteTrack = VolTracker(waste_reservoir, 194000, 'multi', 'waste',
                            msg='Empty Waste Reservoir', start=0, end=1)
    pbsTrack = VolTracker(pbs_reservoir, 194000, 'multi', start=0, end=1,
                          msg='Replenish PBS')
    pfaTrack = VolTracker(reagent_reservoir, 14900, 'multi',
                          start=0, end=4, msg='Replenish 4% PFA')
    permTrack = VolTracker(reagent_reservoir, 14900,
                           'multi', start=4, end=8,
                           msg='Replenish Perm Buffer')
    primaryAntiTrack = VolTracker(reagent_reservoir, 14900,
                                  'multi', start=8, end=10,
                                  msg='Replenish Primary Antibody')
    secondaryAntiTrack = VolTracker(reagent_reservoir, 14900,
                                    'multi', start=10, end=12,
                                    msg='Replenish Secondary Antibody')

    # Protocol Steps

    # Add/Remove PBS
    m300.flow_rate.dispense = disp_speed

    def add_remove_pbs(wells, vol):
        ctx.comment('Adding and Removing PBS')
        if not m300.has_tip:
            m300.pick_up_tip()
        for well in wells:
            m300.aspirate(vol, pbsTrack.tracker(vol))
            m300.dispense(vol, well)
            m300.aspirate(vol, well.bottom(asp_height))
            m300.dispense(vol, wasteTrack.tracker(vol))
        # m300.drop_tip()

    for i, plate in enumerate(plates, 1):
        ctx.comment(f"Starting Plate {i}")
        dest_wells = [plate.rows()[i][col] for col in range(cols) for i in
                      range(2)][:cols*2]

        # Remove Media (1)
        ctx.comment('Removing Media')
        if not m300.has_tip:
            m300.pick_up_tip()
        for well in dest_wells:
            m300.transfer(45, well.bottom(asp_height),
                          wasteTrack.tracker(45), new_tip='never')
        # m300.drop_tip()
        # Add/Remove PBS (2-3)
        add_remove_pbs(dest_wells, 50)
        # Add/Remove PBS (4-5)
        add_remove_pbs(dest_wells, 50)

        # Add/Remove 4% PFA (6-8)
        # m300.pick_up_tip()
        ctx.comment('Adding and Removing 4% PFA')
        for well in dest_wells:
            m300.transfer(50, pfaTrack.tracker(50), well, new_tip='never')
        # m300.drop_tip()
        ctx.delay(minutes=20, msg='Pausing for 20 minutes...')
        # m300.pick_up_tip()
        for well in dest_wells:
            m300.transfer(50, well.bottom(asp_height),
                          wasteTrack.tracker(50), new_tip='never')
        # m300.drop_tip()

        # Add/Remove Perm Buffer (9-11)
        # m300.pick_up_tip()
        ctx.comment('Adding and Removing Perm Buffer')
        for well in dest_wells:
            m300.transfer(50, permTrack.tracker(50), well, new_tip='never')
        # m300.drop_tip()
        ctx.delay(minutes=15, msg='Pausing for 15 minutes...')
        # m300.pick_up_tip()
        for well in dest_wells:
            m300.transfer(50, well.bottom(asp_height),
                          wasteTrack.tracker(50), new_tip='never')
        # m300.drop_tip()

        # Add/Remove PBS (12-13)
        add_remove_pbs(dest_wells, 50)
        # Add/Remove PBS (14-15)
        add_remove_pbs(dest_wells, 50)

        # Add/Remove Primary Antibody Solution (16-18)
        # m300.pick_up_tip()
        ctx.comment('Adding and Removing Primary Antibody Solution')
        for well in dest_wells:
            m300.transfer(25, primaryAntiTrack.tracker(25),
                          well, new_tip='never')
        # m300.drop_tip()
        ctx.delay(minutes=60, msg='Pausing for 60 minutes...')
        # m300.pick_up_tip()
        for well in dest_wells:
            m300.transfer(25, well.bottom(asp_height),
                          wasteTrack.tracker(25), new_tip='never')
        # m300.drop_tip()

        # Add/Remove PBS (19-20)
        add_remove_pbs(dest_wells, 50)
        # Add/Remove PBS (21-22)
        add_remove_pbs(dest_wells, 50)

        # Add/Remove Secondary Antibody Solution (23-25)
        # m300.pick_up_tip()
        ctx.comment('Adding and Removing Secondary Antibody Solution')
        for well in dest_wells:
            m300.transfer(25, secondaryAntiTrack.tracker(25),
                          well, new_tip='never')
        # m300.drop_tip()
        ctx.delay(minutes=30, msg='Pausing for 30 minutes...')
        # m300.pick_up_tip()
        for well in dest_wells:
            m300.transfer(25, well.bottom(asp_height),
                          wasteTrack.tracker(25), new_tip='never')
        # m300.drop_tip()

        # Add/Remove PBS (26-27)
        add_remove_pbs(dest_wells, 50)
        # Add/Remove PBS (28-29)
        add_remove_pbs(dest_wells, 50)

        # Add PBS (30)
        # m300.pick_up_tip()
        ctx.comment('Adding Final PBS')
        for well in dest_wells:
            m300.aspirate(50, pbsTrack.tracker(50))
            m300.dispense(50, well)
        if new_tip == "always":
            m300.drop_tip()
    if new_tip == "never":
        m300.drop_tip()
