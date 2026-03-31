metadata = {
    'protocolName': 'Combo IC',
    'author': 'Abel.Tesfaslassie@opentrons.com',
    'description': 'Sterile Workflows',
    'apiLevel': '2.11'
}


def run(ctx):

    [final_vol, p20_mount, p300_mount, pre_dilutionA, pre_dilutionB,
     pre_dilutionC, pre_dilutionD, pre_dil_factA, pre_dil_factB,
     pre_dil_factC, pre_dil_factD, serial_dil_factA, serial_dil_factB,
     serial_dil_factC, serial_dil_factD] = get_values(  # noqa: F821
        'final_vol', 'p20_mount', 'p300_mount', 'pre_dilutionA',
        'pre_dilutionB', 'pre_dilutionC',
        'pre_dilutionD', 'pre_dil_factA', 'pre_dil_factB',
        'pre_dil_factC', 'pre_dil_factD', 'serial_dil_factA',
        'serial_dil_factB', 'serial_dil_factC', 'serial_dil_factD')

    # Labware setup is as follows:

    # Reagent Resevoir
    dmso_res = ctx.load_labware('nest_12_reservoir_15ml', '1')
    # Tips
    p20_tip_rack = ctx.load_labware('opentrons_96_filtertiprack_20ul', '3')
    p200_tip_rack = ctx.load_labware('opentrons_96_filtertiprack_200ul', '6')
    # Plates
    compound_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '2')
    hdpf1 = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '4')
    hdpf2 = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '5')
    vsp = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '7')
    hsp = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '8')
    vdpf1 = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '10')
    vdpf2 = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '11')

    #  Pipette setup
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[p20_tip_rack])
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[p200_tip_rack])

    # volume Definitiions:
    vol19 = final_vol
    vol1 = vol19 * 12 * 1.1
    vol2 = vol19 * 8 * 1.1
    vol12 = vol1 / (-1 + serial_dil_factC)
    vol14 = vol1 / (-1 + serial_dil_factD)
    vol16 = vol2 / (-1 + serial_dil_factA)
    vol18 = vol2 / (-1 + serial_dil_factB)
    vol11 = vol12 + vol1
    vol13 = vol14 + vol1
    vol15 = vol16 + vol2
    vol17 = vol18 + vol2
    vol7 = vol11 / pre_dil_factC
    vol8 = vol13 / pre_dil_factD
    vol9 = vol15 / pre_dil_factA
    vol10 = vol17 / pre_dil_factB
    vol3 = vol11 - vol7
    vol4 = vol13 - vol8
    vol5 = vol15 - vol9
    vol6 = vol17 - vol10

    # Procedure Step:
    # 1 Transfering DMSO to vertical stamp plate col 1 & col 12 row B-H
    destination1 = [
        well for col in [
            vsp.columns()[c] for c in [0, 11]]
        for well in col[1:]]
    p300.pick_up_tip()
    for d in destination1:
        p300.transfer(vol1, dmso_res.wells_by_name()['A1'], destination1,
                      new_tip='never')
    p300.return_tip()

    # 2 Transfering DMSO to horizontal stamp plate row A & H col 2-12
    destination2 = [
        well for row in [
            hsp.rows()[c] for c in [0, 7]] for well in row[1:]]
    p300.pick_up_tip()
    for d in destination2:
        p300.transfer(vol2, dmso_res.wells_by_name()['A1'], destination2,
                      new_tip='never')
    p300.drop_tip()

    # 3 Transfering predilution DMSO volume for compound C
    if pre_dilutionC:
        pip = p20 if vol3 <= 20 else p300
        pip.pick_up_tip()
        pip.transfer(vol3, dmso_res['A1'], vsp['A2'], new_tip='never')

    # compound D
    if pre_dilutionD:
        pip = p20 if vol4 <= 20 else p300
        if not pip.has_tip:
            pip.pick_up_tip()

        pip.transfer(vol4, dmso_res['A1'], vsp['A11'], new_tip='never')

    # 4 Transfering predilution DMSO volume for compound A
    if pre_dilutionA:
        pip = p20 if vol5 <= 20 else p300
        if not pip.has_tip:
            pip.pick_up_tip()
        pip.transfer(vol5, dmso_res['A1'], hsp['B1'], new_tip='never')

    # compound B
    if pre_dilutionB:
        pip = p20 if vol6 <= 20 else p300
        if not pip.has_tip:
            pip.pick_up_tip()
        pip.transfer(vol6, dmso_res['A1'], hsp['G1'], new_tip='never')

    for pip in [p20, p300]:
        if pip.has_tip:
            pip.drop_tip()

    # 5 Transfering compound C & D volume to vertical stamp plate
    if pre_dilutionC:
        pip = p20 if vol7 <= 20 else p300
        pip.transfer(vol7, compound_plate['B1'], vsp['A2'], new_tip='once')

    if pre_dilutionD:
        pip = p20 if vol8 <= 20 else p300
        pip.transfer(vol8, dmso_res['A1'], vsp['A11'], new_tip='once')

    # 6 Transfering compound A & B volume to horiztonal stamp plate
    if pre_dilutionA:
        pip = p20 if vol9 <= 20 else p300
        pip.transfer(vol9, compound_plate['A1'], hsp['B1'], new_tip='once')

    if pre_dilutionB:
        pip = p20 if vol10 <= 20 else p300
        pip.transfer(vol10, compound_plate['A2'], hsp['G1'], new_tip='once')

    # 7 Serial dilution of compounds C
    p300.pick_up_tip()
    source_7 = vsp["A2"] if pre_dilutionC else compound_plate["B1"]
    pip.transfer(vol11, source_7, vsp["A1"], new_tip='never')
    p300.mix(5, 100, vsp["A1"])
    p300.drop_tip()

    # Serial Dilution across row A of vsp plate slot 7
    source3 = vsp.columns()[0][:6]
    destination3 = vsp.columns()[0][1:7]
    p300.pick_up_tip()
    for s, d in zip(source3, destination3):
        p300.transfer(vol12, s, d, new_tip='never')
        p300.mix(5, 100, d)
    p300.drop_tip()

    # 10 thru 12
    p300.pick_up_tip()
    source_10 = vsp["A11"] if pre_dilutionD else compound_plate["B2"]
    pip.transfer(vol13, source_10, vsp["A12"], new_tip='never')
    p300.mix(5, 100, vsp["A12"])
    p300.drop_tip()

    # Serial Dilution across row A of vsp plate
    source4 = vsp.columns()[11][:6]
    destination4 = vsp.columns()[11][1:7]
    p300.pick_up_tip()
    for s, d in zip(source4, destination4):
        p300.transfer(vol14, s, d, new_tip='never')
        p300.mix(5, 100, d)
    p300.drop_tip()

    # Serial Dilution of compound A & B
    p300.pick_up_tip()
    source_13 = hsp["B1"] if pre_dilutionA else compound_plate["A1"]
    p300.transfer(vol15, source_13, hsp["A1"], new_tip='never')
    p300.mix(5, 100, hsp["A1"])
    p300.drop_tip()

    # Serial Dilution across row A of hsp plate
    source5 = hsp.rows()[0][:10]
    destination5 = hsp.rows()[0][1:11]
    p300.pick_up_tip()
    for s, d in zip(source5, destination5):
        p300.transfer(vol16, s, d, new_tip='never')
        p300.mix(5, 100, d)
    p300.drop_tip()

    # 16-18
    p300.pick_up_tip()
    source_16 = hsp["G1"] if pre_dilutionB else compound_plate["A2"]
    p300.transfer(vol17, source_16, hsp["H1"], new_tip='never')
    p300.mix(5, 100, hsp["H1"])
    p300.drop_tip()

    # Serial Dilution across row A of hsp plate
    source6 = hsp.rows()[7][:10]
    destination6 = hsp.rows()[7][1:11]
    p300.pick_up_tip()
    for s, d in zip(source6, destination6):
        p300.transfer(vol18, s, d, new_tip='never')
        p300.mix(5, 100, d)
    p300.drop_tip()

    # 19-20 ---- distribution of vol from VSP plate col1 across vdpf1
    # plate rows in slot 10 (vsp H1 --> vdpf1 row H , vsp G1 --> vdpf1
    # row G...)
    source7 = vsp.columns()[0]
    destination7_sets = vdpf1.rows()
    p20.pick_up_tip()
    for s, d_set in zip(source7, destination7_sets):
        p20.transfer(vol19, s, d_set, blowout_location='destination well',
                     new_tip='never')
    p20.drop_tip()

    # 21-22--- distribution of final vol from VSP plate col1 across vdpf1
    # plate rows in slot 11 (vsp H1 --> vdpf2 row H , vsp G1 --> vdpf2
    # row G...)
    source8 = vsp.columns()[11]
    destination8_sets = vdpf2.rows()
    p20.pick_up_tip()
    for s, d_set in zip(source8, destination8_sets):
        p20.transfer(vol19, s, d_set, blowout_location='destination well',
                     new_tip='never')
    p20.drop_tip()

    # 23-24--- distribution of vol from hsp plate row A across vdpf1 plate
    # rows in slot 4 (hsp A12 --> hdpf1 A12-H12, hsp A11 --> vdpf1 A11-H11...)
    source9 = hsp.rows()[0]
    destination9_sets = hdpf1.columns()
    p20.pick_up_tip()
    for s, d_set in zip(source9, destination9_sets):
        p20.transfer(vol19, s, d_set, blowout_location='destination well',
                     new_tip='never')
    p20.drop_tip()

    # 25-26--- distribution of vol from hsp plate row H across vdpf2 plate
    # cols in slot 4 (hsp H12 --> hdpf2 H12-A12, hsp G12 --> vdpf2 A11-H11...)
    source10 = hsp.rows()[7]
    destination10_sets = hdpf2.columns()
    p20.pick_up_tip()
    for s, d_set in zip(source10, destination10_sets):
        p20.transfer(vol19, s, d_set, blowout_location='destination well',
                     new_tip='never')
    p20.drop_tip()
