from opentrons import types

metadata = {
    'protocolName': 'Custom Cherrypicking PCR Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [p20_mount, ctrl_csv, assembly_csv, ctrl_transfer_vol,
        assembly_transfer_vol, pipette_homing,
        asp_height] = get_values(  # noqa: F821
        "p20_mount", "ctrl_csv", "assembly_csv", "ctrl_transfer_vol",
        "assembly_transfer_vol", "pipette_homing", "asp_height")

    # Load Labware
    temp_mod = ctx.load_module('temperature module gen2', 9)
    tiprack_20ul = [ctx.load_labware('opentrons_96_tiprack_20ul', slot) for
                    slot in [5, 6, 8, 11]]
    lw_name = 'appliedbiosystems_96_wellplate_200ul_on_eppendorf_cooling_block'
    for slot in [1, 2, 3]:
        ctx.load_labware(lw_name, slot)
    for slot in [4, 7, 10]:
        ctx.load_labware('eppendorf_24_tuberack_generic_2.0ml_screwcap', slot)

    # Load Pipette
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack_20ul)

    ctrl_info = [[val.strip().lower() for val in line.split(',')] for line in
                 ctrl_csv.splitlines() if line.split(',')[0].strip()][6:]

    assembly_info = [[val.strip().lower() for val in line.split(',')] for line
                     in assembly_csv.splitlines() if
                     line.split(',')[0].strip()][6:]

    # Create Eppendorf Rack to Opentrons Racks Conversion Map
    map_info = '''A1,10,A1\nA2,10,A2\nA3,10,A3\nA4,10,A4\nA5,10,A5\nA6,10,A6
    \nB1,10,B1\nB2,10,B2\nB3,10,B3\nB4,10,B4\nB5,10,B5\nB6,10,B6\nC1,10,C1
    \nC2,10,C2\nC3,10,C3\nC4,10,C4\nC5,10,C5\nC6,10,C6\nD1,10,D1\nD2,10,D2
    \nD3,10,D3\nD4,10,D4\nD5,10,D5\nD6,10,D6\nE1,7,A1\nE2,7,A2\nE3,7,A3\nE4,7,A4
    \nE5,7,A5\nE6,7,A6\nF1,7,B1\nF2,7,B2\nF3,7,B3\nF4,7,B4\nF5,7,B5\nF6,7,B6
    \nG1,7,C1\nG2,7,C2\nG3,7,C3\nG4,7,C4\nG5,7,C5\nG6,7,C6\nH1,7,D1\nH2,7,D2
    \nH3,7,D3\nH4,7,D4\nH5,7,D5\nH6,7,D6\nI1,4,A1\nI2,4,A2\nI3,4,A3\nI4,4,A4
    \nI5,4,A5\nI6,4,A6\nJ1,4,B1\nJ2,4,B2\nJ3,4,B3\nJ4,4,B4\nJ5,4,B5\nJ6,4,B6
    \nK1,4,C1\nK2,4,C2\nK3,4,C3\nK4,4,C4\nK5,4,C5\nK6,4,C6\nL1,4,D1\nL2,4,D2
    \nL3,4,D3\nL4,4,D4\nL5,4,D5\nL6,4,D6\n'''

    plate_map = [[val.strip().upper() for val in line.split(',')] for line in
                 map_info.splitlines() if line.split(',')[0].strip()]
    conversion_map = {row[0]: [row[1], row[2]] for row in plate_map}

    # Load Control Labware
    for line in ctrl_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[3:5]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                if int(slot) == 9:
                    temp_mod.load_labware(lw.lower())
                else:
                    ctx.load_labware(lw.lower(), slot)

    # Load Assembly Labware
    for line in assembly_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[3:5]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                if int(slot) == 9:
                    temp_mod.load_labware(lw.lower())
                else:
                    ctx.load_labware(lw.lower(), slot)

    # Load Protocol Steps

    # Set Temperature Module
    temp_mod.start_set_temperature(4)

    # Drop Tip Height
    trash = ctx.deck['12']['A1']
    drop_loc = trash.center().move(types.Point(z=-40))

    # Step 1: Control
    for line in ctrl_info:
        s_slot, s_well, d_slot, d_well = line[1:3] + line[4:6]
        c_slot, c_well = conversion_map[s_well.upper()]
        p20.pick_up_tip()
        p20.aspirate(ctrl_transfer_vol, ctx.loaded_labwares[int(c_slot)][
                          c_well.upper()].bottom(0.5))
        p20.dispense(ctrl_transfer_vol,
                     ctx.loaded_labwares[int(d_slot)][d_well.upper()])
        if pipette_homing == "False":
            p20.drop_tip(drop_loc, home_after=False)
        else:
            p20.drop_tip(drop_loc)

    temp_mod.await_temperature(4)

    # Step 2: Assembly
    for line in assembly_info:
        s_slot, s_well, d_slot, d_well = line[1:3] + line[4:6]
        if not ctx.loaded_labwares[int(s_slot)].is_tiprack and \
                not ctx.loaded_labwares[int(d_slot)].is_tiprack:
            p20.pick_up_tip()
            p20.aspirate(assembly_transfer_vol,
                         ctx.loaded_labwares[int(s_slot)][
                            s_well.upper()].bottom(asp_height))
            p20.dispense(assembly_transfer_vol,
                         ctx.loaded_labwares[int(d_slot)][d_well.upper()])
            if pipette_homing == "False":
                p20.drop_tip(drop_loc, home_after=False)
            else:
                p20.drop_tip(drop_loc)
