from opentrons import protocol_api

metadata = {
    'protocolName': 'Custom CSV Mass Spec Sample Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [
        csv_file,
        sample_vol,
        mecn_transfer,
        p300_mount,
        m300_mount,
        asp_rate,
        disp_rate,
        asp_rate_multi,
        disp_rate_multi,
        temp_mod,
        disp_height,
        pl_blowout_height,
        airgap,
        mecn_volume,
        reservoir_loc,
        mecn_dil_loc,
        starting_tip_col
        ] = get_values(  # noqa: F821
            "csv_file",
            "sample_vol",
            "mecn_transfer",
            "p300_mount",
            "m300_mount",
            "asp_rate",
            "disp_rate",
            "asp_rate_multi",
            "disp_rate_multi",
            "temp_mod",
            "disp_height",
            "pl_blowout_height",
            "airgap",
            "mecn_volume",
            "reservoir_loc",
            "mecn_dil_loc",
            "starting_tip_col")

    # CHANGE VARIABLES HERE
    sample_vol = 30
    mecn_transfer = True
    p300_mount = "left"
    m300_mount = "right"
    asp_rate = 6
    disp_rate = 6
    asp_rate_multi = 10
    disp_rate_multi = 10
    temp_mod = True
    disp_height = 12.5
    pl_blowout_height = 10
    airgap = 10
    mecn_volume = 90
    reservoir_loc = 3
    mecn_dil_loc = 3
    starting_tip_col = 4

    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in csv_file.splitlines()
                     if line.split(',')[0].strip()][1:]

    columns = len(transfer_info[0])-1
    print(columns)

    # Load Labware
    if temp_mod:
        temp_mod_3 = ctx.load_module('temperature module gen2', '3')
        temp_mod_6 = ctx.load_module('temperature module gen2', '6')
        temp_mod_3.set_temperature(4)
        temp_mod_6.set_temperature(4)

    tuberack = 'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap'
    well_plate = 'nest_96_wellplate_2ml_deep'
    tiprack1 = ctx.load_labware('opentrons_96_tiprack_300ul', 8)
    tiprack2 = ctx.load_labware('opentrons_96_tiprack_300ul', 10)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 7)

    if columns == 5:
        for line in transfer_info:
            s_slot, d_slot = line[1] + line[4]
            for rack, plate in zip([s_slot], [d_slot]):
                if not int(rack) in ctx.loaded_labwares:
                    ctx.load_labware(tuberack, rack)
                if not int(plate) in ctx.loaded_labwares:
                    if temp_mod:
                        temp_mod_3.load_labware(well_plate)
                    else:
                        ctx.load_labware(well_plate, plate)
    elif columns == 7:
        for line in transfer_info:
            s_slot, d1_slot, d2_slot = line[1] + line[4] + line[6]
            for rack, plate1, plate2 in zip([s_slot], [d1_slot], [d2_slot]):
                if not int(rack) in ctx.loaded_labwares:
                    ctx.load_labware(tuberack, rack)
                if not int(plate1) in ctx.loaded_labwares:
                    if temp_mod:
                        temp_mod_3.load_labware(well_plate)
                    else:
                        ctx.load_labware(well_plate, plate1)
                if not int(plate2) in ctx.loaded_labwares:
                    if temp_mod:
                        temp_mod_6.load_labware(well_plate)
                    else:
                        ctx.load_labware(well_plate, plate2)
    # else:
    #     raise ValueError('Invalid CSV File Format. Check your CSV file.')

    # Load Pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tiprack1])
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[tiprack2])

    # Helper Functions
    def pick_up(pip, loc=None):
        try:
            if loc:
                pip.pick_up_tip(loc)
            else:
                pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Please replace the empty tip racks!")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def preWet(pipette, volume, location, reps, sample_height, b_height, airgap_vol):  # noqa: E501
        ctx.comment(f'Pre-Wetting the tip(s) with {volume} uL at {location}')
        for _ in range(reps):
            sample_height = int(sample_height)
            pipette.aspirate(volume, location.top(-sample_height))
            pipette.air_gap(airgap_vol)
            pipette.dispense(volume, location.top(-b_height))
            pipette.blow_out(location.top(-b_height))

    # Protocol Steps
    p300.flow_rate.aspirate = asp_rate
    p300.flow_rate.dispense = disp_rate
    p300.flow_rate.blow_out = 1000
    m300.flow_rate.aspirate = asp_rate_multi
    m300.flow_rate.dispense = disp_rate_multi

    # One Plate
    if columns == 5:
        for line in transfer_info:

            s_slot, s_well, pickup_height, d1_slot, d1_well = line[1:7]
            rack_by_row = [tube
                           for row in
                           ctx.loaded_labwares[int(s_slot)].rows()
                           for tube in row]
            source = rack_by_row[int(s_well) - 1]
            dest1 = ctx.loaded_labwares[int(d1_slot)][d1_well.upper()]

            pick_up(p300)
            preWet(p300, sample_vol, source, 1, pickup_height, pl_blowout_height, airgap)  # noqa: E501

            p300.aspirate(sample_vol, source.top(-int(pickup_height)))
            p300.air_gap(airgap)
            p300.dispense(sample_vol, dest1.bottom(disp_height))
            p300.blow_out()
            p300.blow_out()
            p300.touch_tip()

            p300.drop_tip()
            ctx.comment('\n\n')

    # Two Plates
    if columns == 7:
        airgap = 10
        for line in transfer_info:
            s_slot, s_well, pickup_height, d1_slot, d1_well, d2_slot, d2_well = line[1:8]  # noqa: E501
            rack_by_row = [tube
                           for row in
                           ctx.loaded_labwares[int(s_slot)].rows()
                           for tube in row]
            source = rack_by_row[int(s_well) - 1]
            dest1 = ctx.loaded_labwares[int(d1_slot)][d1_well.upper()]
            dest2 = ctx.loaded_labwares[int(d2_slot)][d2_well.upper()]

            pick_up(p300)

            # Prewet
            preWet(p300, sample_vol, source, 1, pickup_height, pl_blowout_height, airgap)  # noqa: E501

            # 1st pickup and dispense for wellplate 1
            p300.aspirate(sample_vol, source.top(-int(pickup_height)))
            p300.air_gap(airgap)

            # 1st dispense
            p300.dispense(sample_vol, dest1.bottom(disp_height))
            p300.blow_out()
            p300.blow_out()
            p300.touch_tip()

            # 2nd pickup from source
            p300.aspirate(sample_vol, source.top(-int(pickup_height)))
            p300.air_gap(airgap)
            # 2nd well
            p300.dispense(sample_vol, dest2.bottom(disp_height))
            p300.blow_out()
            p300.blow_out()
            p300.touch_tip()

            p300.drop_tip()

    ctx.pause('Press Resume on the Opentrons app to continue')
    # Acetonitrile (MeCN) Transfer
    m300.starting_tip = tiprack2.rows()[0][starting_tip_col-1]
    if mecn_transfer:
        pick_up(m300)

        # Prewet the tips. Did not use function so default parameters are selected  # noqa: E501
        m300.aspirate(mecn_volume, reservoir.wells()[reservoir_loc-1].bottom(1))  # noqa: E501
        m300.air_gap(airgap)
        m300.dispense(mecn_volume, reservoir.wells()[reservoir_loc-1].top(-5))
        m300.blow_out(reservoir.wells()[reservoir_loc-1].top(-5))

        # Updated to account for plate dilution, incorporate aliquout and reservoir location, add air gap, dispense volume and blow out  # noqa: E501
        for col in ctx.loaded_labwares[mecn_dil_loc].rows()[0]:
            m300.aspirate(mecn_volume, reservoir.wells()[reservoir_loc-1].bottom(1))  # noqa: E501
            m300.air_gap(airgap)
            m300.dispense(mecn_volume, col.center())
            m300.blow_out()
            m300.blow_out()
        m300.drop_tip()
