import math
metadata = {
    'protocolName': 'Sample Prep for ELISA Test',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    # load labware
    [mix_reps, v_0_tube, clearance,
        p1000_flow_rate_asp, p1000_flow_rate_disp, touchtip_radius,
        touchtip_z, touchtip_speed,
        p20_mount, p1000_mount] = get_values(  # noqa: F821
        'mix_reps', 'v_0_tube', 'clearance',
        'p1000_flow_rate_asp', 'p1000_flow_rate_disp',
        'touchtip_radius', 'touchtip_z', 'touchtip_speed',
        'p20_mount', 'p1000_mount')

    ctrl_plates = [ctx.load_labware('greiner_384_wellplate_200ul', slot)
                   for slot in ['9', '6', '3']]
    diluent_tubes = ctx.load_labware(
                    'appleton_6_tuberack_50000ul', '7')
    reagent = ctx.load_labware('axygen_24_tuberack_1700ul', '8')
    master_block = ctx.load_labware('greiner_96_wellplate_2000ul', '4')
    tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '2')]
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '1')]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack1000)

    p1000.well_bottom_clearance.aspirate = clearance
    p1000.well_bottom_clearance.dispense = clearance
    p1000.flow_rate.aspirate = p1000_flow_rate_asp
    p1000.flow_rate.dispense = p1000_flow_rate_disp

    # load reagents
    diluent = diluent_tubes.wells()[0]
    mab207 = reagent.rows()[0][1]
    mab210_stock = reagent.rows()[0][0]
    mab210_100_conc = reagent.rows()[1][0]
    mab210_20_conc = reagent.rows()[1][1]
    mab210_2_conc = reagent.rows()[1][2]

    # liquid height tracking
    v_naught = v_0_tube
    radius = diluent.diameter/2
    h_naught = v_naught/(math.pi*radius**2)
    h = h_naught

    def adjust_height(vol):
        nonlocal h
        dh = vol/(math.pi*radius**2)
        h -= dh
        if h < 20:
            h = 1
        else:
            return h * 0.7

    # STEP DOWN STOCK
    airgap = 5
    p20.pick_up_tip()
    p20.transfer(55.4, diluent, mab210_100_conc, new_tip='never',
                 touch_tip=True)
    adjust_height(55.4)
    p20.drop_tip()
    p20.pick_up_tip()
    p20.aspirate(4.6, mab210_stock)
    p20.air_gap(airgap)
    p20.touch_tip(radius=touchtip_radius,
                  v_offset=touchtip_z,
                  speed=touchtip_speed)
    p20.dispense(4.6+airgap, mab210_100_conc)
    p20.touch_tip(radius=touchtip_radius,
                  v_offset=touchtip_z,
                  speed=touchtip_speed)
    p20.blow_out()
    p20.mix(mix_reps, 20, mab210_100_conc)  # mix extra b/c mixing 1/3 totvol
    p20.touch_tip(radius=touchtip_radius,
                  v_offset=touchtip_z,
                  speed=touchtip_speed)
    p20.drop_tip()

    p1000.pick_up_tip()
    p1000.aspirate(160, diluent)
    adjust_height(160)
    p1000.touch_tip(radius=touchtip_radius,
                    v_offset=touchtip_z,
                    speed=touchtip_speed)
    p1000.dispense(160, mab210_20_conc)
    p1000.touch_tip(radius=touchtip_radius,
                    v_offset=touchtip_z,
                    speed=touchtip_speed)
    p20.pick_up_tip()
    p20.transfer(40, mab210_100_conc, mab210_20_conc, new_tip='never',
                 touch_tip=True)
    p20.drop_tip()
    p1000.mix(mix_reps, 180, mab210_20_conc)
    p1000.blow_out()
    p1000.touch_tip(radius=touchtip_radius,
                    v_offset=touchtip_z,
                    speed=touchtip_speed)
    p1000.drop_tip()

    p1000.pick_up_tip()
    p1000.transfer(720, diluent, mab210_2_conc, new_tip='never',
                   touch_tip=True)
    adjust_height(720)
    p20.pick_up_tip()
    p20.transfer(80, mab210_20_conc, mab210_2_conc, new_tip='never',
                 touch_tip=True)
    p20.drop_tip()
    p1000.mix(mix_reps, 700, mab210_2_conc)
    p1000.touch_tip(radius=touchtip_radius,
                    v_offset=touchtip_z,
                    speed=touchtip_speed)
    p1000.blow_out()
    p1000.drop_tip()

    # CREATE MASTERBLOCK - 207 PREP

    # add diluent
    volumes = [900, 925, 950, 960, 980,
               980, 990, 990, 995, 995,
               992.5, 987.5, 985, 1000, 1000,
               1000]
    dest_wells = ['A1', 'A2', 'B1', 'B2', 'C1',
                  'G1', 'C2', 'E2', 'D1', 'D2',
                  'E1', 'F1', 'G1', 'G2', 'H1',
                  'H2']

    p1000.pick_up_tip()
    for vols, wellname in zip(volumes, dest_wells):
        p1000.aspirate(vols, diluent)
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.dispense(vols, master_block.wells_by_name()[wellname].top())
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        adjust_height(vols)
    p1000.drop_tip()

    # add 207f
    volumes = [100, 75, 50, 40, 20,
               20, 10, 10, 5, 5,
               7.5, 12.5, 15]
    dest_wells = ['A1', 'A2', 'B1', 'B2', 'C1',
                  'G1', 'C2', 'E2', 'D1', 'D2',
                  'E1', 'F1', 'G1']

    for vols, wellname in zip(volumes, dest_wells):
        if vols < 100:
            pip = p20
        else:
            pip = p1000
        if not pip.has_tip:
            pip.pick_up_tip()
        pip.transfer(vols, mab207,
                     master_block.wells_by_name()[wellname].top(),
                     new_tip='never', touch_tip=True)

    p1000.drop_tip()
    p20.drop_tip()

    for well in master_block.wells()[:16]:
        p1000.pick_up_tip()
        p1000.mix(mix_reps, 800, well.bottom(z=5))
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.drop_tip()

    # CREATE MASTERBLOCK - 210 PREP
    p1000.pick_up_tip()
    for wells in master_block.columns()[2]:
        p1000.aspirate(1000, diluent)
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.dispense(1000, wells.bottom(z=12))
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        adjust_height(1000)

    vols_dil = [700, 850, 900, 920, 940, 970, 985, 990]
    for wells, vol in zip(master_block.columns()[2], vols_dil):
        p1000.aspirate(vol, diluent)
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.dispense(vol, wells.bottom(z=12))
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        adjust_height(vol)
    p1000.drop_tip()

    p1000.pick_up_tip()
    vols_mab = [300, 150, 100, 80, 60, 30, 15, 10]
    for wells, vol in zip(master_block.columns()[2], vols_mab):
        p1000.transfer(vol, mab210_2_conc,
                       wells.top(), new_tip='never', touch_tip=True)
    p1000.drop_tip()
    for wells in master_block.columns()[2]:
        p1000.pick_up_tip()
        p1000.mix(mix_reps, 1000, well.bottom(z=12))
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.drop_tip()

    # transfer to 384 well plate
    wells = [
                ['A1', 'A23'],
                ['C1', 'C23'],
                ['E1', 'E23'],
                ['G1', 'G23'],
                ['I1', 'I23'],
                ['K1', 'K23'],
                ['M1', 'M23'],
                ['O1', 'O23'],

                ['B1', 'B23'],
                ['D1', 'D23'],
                ['F1', 'F23'],
                ['H1', 'H23'],
                ['J1', 'J23'],
                ['L1', 'L23'],
                ['N1', 'N23'],
                ['P1', 'P23'],

                ['A2', 'A24'],
                ['B2', 'B24'],
                ['C2', 'C24'],
                ['D2', 'D24'],
                ['E2', 'E24'],
                ['F2', 'F24'],
                ['G2', 'G24'],
                ['H2', 'H24'],
                ['I2', 'I24'],
                ['J2', 'J24'],
                ['K2', 'K24'],
                ['L2', 'L24'],
                ['M2', 'M24'],
                ['N2', 'N24'],
                ['O2', 'O24'],
                ['P2', 'P24'],
            ]

    source_wells = [
                    'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1',
                    'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
                    'A3', 'A3', 'B3', 'B3', 'C3', 'C3', 'D3', 'D3',
                    'E3', 'E3', 'F3', 'F3', 'G3', 'G3', 'H3', 'H3',
                    ]

    heights = [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],

        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],

        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
        [12, 5],
        [1, 1],
    ]

    for i, (source_well, chunk, height) in enumerate(zip(source_wells,
                                                         wells,
                                                         heights)):
        p1000.pick_up_tip()
        p1000.aspirate(820, master_block.wells_by_name()[source_well].bottom(
                                                                z=height[0]))
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        for plate in range(2):
            for well in chunk:
                p1000.dispense(180, ctrl_plates[plate].wells_by_name()[well])
                p1000.touch_tip(radius=touchtip_radius,
                                v_offset=touchtip_z,
                                speed=touchtip_speed)
        p1000.dispense(100, master_block.wells_by_name()[source_well])
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.aspirate(260, master_block.wells_by_name()[source_well].bottom(
                                                                z=height[1]))
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        for well in chunk:
            p1000.dispense(80, ctrl_plates[2].wells_by_name()[well])
            p1000.touch_tip(radius=touchtip_radius,
                            v_offset=touchtip_z,
                            speed=touchtip_speed)
        p1000.dispense(100, master_block.wells_by_name()[source_well])
        p1000.blow_out()
        p1000.touch_tip(radius=touchtip_radius,
                        v_offset=touchtip_z,
                        speed=touchtip_speed)
        p1000.drop_tip()
        ctx.comment('\n\n')
