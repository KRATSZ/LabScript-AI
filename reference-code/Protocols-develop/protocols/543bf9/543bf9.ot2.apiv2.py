import math

metadata = {
    'protocolName': 'Standard Curve Dilutions with CSV File',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [p50_mount, csv_file_1, csv_file_2,
        diluent_vol, asp_speed, disp_speed,
        air_gap_vol, delay_time] = get_values(  # noqa: F821
        "p50_mount", "csv_file_1", "csv_file_2", "diluent_vol", "asp_speed",
        "disp_speed", "air_gap_vol", "delay_time")

    # Load Labware
    plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 6)
    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 3)
    tipracks = [ctx.load_labware('opentrons_96_tiprack_300ul',
                                 slot) for slot in range(1, 3)]

    # Load Pipette
    p50 = ctx.load_instrument('p50_single', p50_mount,
                              tip_racks=tipracks)
    max_vol = p50.max_volume - air_gap_vol

    # Reagents
    stock1 = tuberack['A1']
    stock2 = tuberack['A2']

    well_positions_curve1 = {"Int1": "A1", "Int2": "A2", "Int3": "A3",
                             "Int4": "A4", "Std1": "B1", "Std2": "B2",
                             "Std3": "B3", "Std4": "B4", "Std5": "B5",
                             "Std6": "B6", "Std7": "B7", "Std8": "B8",
                             "Blank (Std9)": "B9", "QC1": "C1",
                             "QC2": "C2", "QC3": "C3", "QC4": "C4"}

    well_positions_curve2 = {"Int1": "E1", "Int2": "E2", "Int3": "E3",
                             "Int4": "E4", "Std1": "F1", "Std2": "F2",
                             "Std3": "F3", "Std4": "F4", "Std5": "F5",
                             "Std6": "F6", "Std7": "F7", "Std8": "F8",
                             "Blank (Std9)": "F9", "QC1": "G1",
                             "QC2": "G2", "QC3": "G3", "QC4": "G4"}

    data_c1 = [[val.strip() for val in line.split(',')] for line in
               csv_file_1.splitlines() if line.split(',')[0].strip()]

    data_c2 = [[val.strip() for val in line.split(',')] for line in
               csv_file_2.splitlines() if line.split(',')[0].strip()]

    transformed_data_c1 = []
    transformed_data_c2 = []

    def transform_data(data, well_positions, results):
        for i, line in enumerate(data):
            if line[4] == '':
                continue
            if line[0] in well_positions_curve1:
                if line[1] == '':
                    src_conc = None
                    sample_src = None
                    dest = plate[well_positions[line[0]]]
                    dil_vol = float(line[4])
                    src_vol = None
                    results.append([src_conc, sample_src, dest, dil_vol,
                                    src_vol])
                    continue
                src_conc = float(line[1])
                if line[2] == 'stock1':
                    sample_src = stock1
                elif line[2] == 'stock2':
                    sample_src = stock2
                else:
                    sample_src = plate[well_positions[line[2]]]
                dest = plate[well_positions[line[0]]]
                src_vol = float(line[3])
                dil_vol = float(line[4])
                results.append([src_conc, sample_src, dest, dil_vol, src_vol])

    def change_flow_rates(asp_speed, disp_speed):
        p50.flow_rate.aspirate = asp_speed
        p50.flow_rate.dispense = disp_speed

    def reset_flow_rates():
        p50.flow_rate.aspirate = 25
        p50.flow_rate.dispense = 50

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

    def preWet(volume, location):
        ctx.comment(f"Pre-Wetting the tip at {location}")
        p50.aspirate(volume, location)
        slow_tip_withdrawal(p50, location)
        p50.dispense(volume, location)
        slow_tip_withdrawal(p50, location)

    # Volume Tracking
    class VolTracker:
        def __init__(self, labware, well_vol, pip_type='single',
                     mode='reagent'):
            self.labware_wells = dict.fromkeys(labware, 0)
            self.well_vol = well_vol
            self.pip_type = pip_type
            self.mode = mode

        def tracker(self, vol, well_only=False):
            '''tracker() will track how much liquid
            was used up per well. If the volume of
            a given well is greater than self.well_vol
            it will remove it from the dictionary and iterate
            to the next well which will act as the reservoir.'''
            well = next(iter(self.labware_wells))
            if self.labware_wells[well] + vol >= self.well_vol:
                del self.labware_wells[well]
                well = next(iter(self.labware_wells))
                if well_only:
                    return well
            if well_only:
                return well
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

    diluentTrack = VolTracker(tuberack.rows()[1][:3], diluent_vol)

    # Liquid Handling Steps
    def liquid_handle(data):
        change_flow_rates(asp_speed, disp_speed)
        for line in data:
            src_conc = line[0]
            sample_src = line[1]
            dest = line[2]
            dil_vol = line[3]
            src_vol = line[4]
            # Add diluent and then transfer samples
            p50.pick_up_tip()
            num_trans = math.ceil(dil_vol/max_vol)
            vol_per_trans = dil_vol/num_trans
            preWet(vol_per_trans, diluentTrack.tracker(vol_per_trans))
            for _ in range(num_trans):
                loc = diluentTrack.tracker(vol_per_trans, well_only=True)
                p50.aspirate(vol_per_trans,
                             diluentTrack.tracker(vol_per_trans))
                ctx.delay(seconds=delay_time)
                slow_tip_withdrawal(p50, loc)
                p50.air_gap(air_gap_vol)
                p50.dispense(vol_per_trans+air_gap_vol, dest)
                ctx.delay(seconds=delay_time)
                slow_tip_withdrawal(p50, dest)
            p50.drop_tip()
            if src_conc is not None:
                p50.pick_up_tip()
                num_trans = math.ceil(src_vol/max_vol)
                vol_per_trans = src_vol/num_trans
                preWet(vol_per_trans, sample_src)
                for _ in range(num_trans):
                    p50.aspirate(vol_per_trans, sample_src)
                    ctx.delay(seconds=delay_time)
                    slow_tip_withdrawal(p50, sample_src)
                    p50.air_gap(air_gap_vol)
                    p50.dispense(vol_per_trans+air_gap_vol, dest)
                    ctx.delay(seconds=delay_time)
                    slow_tip_withdrawal(p50, dest)
                p50.mix(3, (src_vol+dil_vol)/2)
                slow_tip_withdrawal(p50, dest)
                p50.blow_out()
                p50.touch_tip()
                p50.drop_tip()
        reset_flow_rates()

    # First Standard Curve
    transform_data(data_c1, well_positions_curve1,
                   transformed_data_c1)
    liquid_handle(transformed_data_c1)

    # Second Standard Curve
    if len(data_c2) > 0:
        transform_data(data_c2, well_positions_curve2,
                       transformed_data_c2)
        liquid_handle(transformed_data_c2)
