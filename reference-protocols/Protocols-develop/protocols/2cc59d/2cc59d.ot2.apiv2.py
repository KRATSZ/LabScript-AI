import math

metadata = {
    'protocolName': 'SuperScript III: qRT-PCR Prep with CSV File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "p20_mount", "p300_mount")

    # load labware
    temp_mod = ctx.load_module('temperature module gen2', 9)
    temp_plate = temp_mod.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul', "Starting")  # noqa: E501
    print(temp_plate)
    res12 = ctx.load_labware('nest_12_reservoir_15ml', 3)
    res = ctx.load_labware('nest_1_reservoir_195ml', 11)
    greiner_plate = ctx.load_labware('greiner_96_wellplate_200ul', 2)
    costar_plate = ctx.load_labware('costar_96_wellplate_200ul', 1)
    tuberacks = [ctx.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', slot) for slot in [7, 8]]  # noqa: E501
    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                  for slot in [4, 5, 6]]
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', 10)]

    # load pipette
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tiprack300)

    # load reagents

    sample_dilution_buff = res12.wells()[0]
    rbd = res12.wells()[1]
    pos_ctrl = tuberacks[0].rows()[0][1]
    neg_ctrl = tuberacks[0].rows()[0][2]
    cal_stock = tuberacks[0].rows()[0][0]
    tmb = res12.wells()[2]
    stop_sol = res12.wells()[3]
    patient_samples = [tube for rack in tuberacks
                       for row in rack.rows() for tube in row][3:3+num_samp]

    # num_cols = math.ceil((num_samp)/8) if num_samp > 6 else 1
    if num_samp <= 6:
        num_cols = 1
    elif num_samp > 6:
        num_cols = 1+math.ceil((num_samp-6)/8)
    odd_columns = greiner_plate.rows()[0][2:2+num_cols*2:2]
    even_columns = greiner_plate.rows()[0][3:3+num_cols*2:2]
    waste = res12.wells()[-1]

    tip_count = 0
    reg_tipcount = 2
    reg_tips = [col for rack in tiprack300[:2] for col in rack.rows()[0]]

    tips_ordered = [
        tip for rack in tiprack300
        for col in rack.columns()  # noqa: E501
        for tip in col[::-1]]

    def pick_up_less(num_tip):
        nonlocal tip_count
        p300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    def pick_up():
        nonlocal reg_tipcount
        if reg_tipcount == 23:
            ctx.pause("\nRefill Tipracks\n")
            p300.reset_tipracks()
            reg_tipcount = 0
        p300.pick_up_tip(reg_tips[reg_tipcount])
        reg_tipcount += 1

    ctx.comment('\n\nTRANSFERRING TO A1 OF GREINER PLATE\n')
    pick_up_less(1)
    p300.aspirate(270, sample_dilution_buff)
    p300.dispense(270, greiner_plate.wells()[0])
    p300.blow_out()
    p300.drop_tip()

    ctx.comment('\n\nTRANSFERRING BUFFER TO REST OF COLUMN\n')
    p300.pick_up_tip(tiprack300[0].wells()[0])
    p300.aspirate(150, sample_dilution_buff)
    p300.dispense(150, greiner_plate.wells()[1])
    p300.blow_out()
    p300.drop_tip()
    tip_count += 7

    ctx.comment('\n\nTRANSFERRING BUFFER TO ODD COLUMNS\n')
    pick_up()
    for col in odd_columns:
        p300.aspirate(126, sample_dilution_buff)
        p300.dispense(126, col)
        p300.blow_out()
    p300.drop_tip()

    ctx.comment('\n\nTRANSFERRING CALIBRATOR STOCK\n')
    pick_up_less(1)
    p300.aspirate(30, cal_stock)
    p300.dispense(30, greiner_plate.wells()[0])
    p300.mix(5, 300, greiner_plate.wells()[0])
    p300.drop_tip()

    ctx.comment('\n\nDILUTING DOWN THE COLUMN\n')
    for i, well in enumerate(greiner_plate.columns()[0][:6]):
        pick_up_less(1)
        p300.aspirate(150, well)
        p300.dispense(150, greiner_plate.columns()[0][i+1])
        p300.mix(5, 300, greiner_plate.columns()[0][i+1])
        p300.drop_tip()

    ctx.comment('\n\nTRANSFERRING CONTROLS\n')
    p20.pick_up_tip()
    p20.aspirate(14, pos_ctrl)
    p20.dispense(14, greiner_plate.wells_by_name()['G3'])
    p20.mix(3, 20, greiner_plate.wells_by_name()['G3'])
    p20.drop_tip()
    p20.pick_up_tip()
    p20.aspirate(14, neg_ctrl)
    p20.dispense(14, greiner_plate.wells_by_name()['H3'])
    p20.mix(3, 20, greiner_plate.wells_by_name()['H3'])
    p20.drop_tip()

    ctx.comment('\n\nTRANSFERRING PATIENT SAMPLES\n')
    sample_wells = [well for col in greiner_plate.columns()[2::2] for well in col]  # noqa: E501S
    ctr = 0
    for dest in sample_wells[:num_samp+2]:
        if dest == greiner_plate.wells_by_name()['G3'] or dest == greiner_plate.wells_by_name()['H3']:  # noqa: E501S
            continue
        p20.pick_up_tip()
        p20.aspirate(14, patient_samples[ctr])
        p20.dispense(14, dest)
        p20.blow_out()
        p20.drop_tip()
        ctr += 1
        ctx.comment('\n')

    ctx.comment('\n\nTRANSFERRING RBD\n')
    pick_up()
    p300.aspirate(120, rbd)
    p300.dispense(120, greiner_plate.rows()[0][1])

    ctx.comment('\n\nTRANSFERRING RBD TO EVEN COLUMNS\n')

    for col in even_columns:
        p300.aspirate(120, rbd)
        p300.dispense(120, col)
        p300.blow_out()
    p300.drop_tip()

    ctx.comment('\n\nTRANSFERRING INTO SUBSEQUENT COLUMN\n')
    pick_up()
    p300.aspirate(120, greiner_plate.rows()[0][0])
    p300.dispense(120, greiner_plate.rows()[0][1])
    p300.mix(2, 300, greiner_plate.rows()[0][1])
    p300.drop_tip()

    for i, col in enumerate(greiner_plate.rows()[0][2:2+num_cols*2:2]):
        pick_up()
        p300.aspirate(120, col)
        p300.dispense(120, greiner_plate.rows()[0][i*2+3])
        p300.mix(2, 300, greiner_plate.rows()[0][i*2+3])
        p300.drop_tip()

    ctx.pause('''Place Greiner plate on plate warmer at 37C for 30 minutes,
                 Then select "Resume" on the Opentrons App.''')

    ctx.comment('\n\nSPLITTING COLUMNS TO COSTAR PLATES\n')
    for i in range(num_cols+1 if num_cols < 6 else 0):
        pick_up()
        p300.aspirate(200, greiner_plate.rows()[0][i*2+1])
        p300.dispense(100, costar_plate.rows()[0][i*2])
        p300.dispense(100, costar_plate.rows()[0][i*2+1])
        p300.drop_tip()

    ctx.pause('''Place Costar plate on plate warmer at 37C for 30 minutes,
                 Then select "Resume" on the Opentrons App.''')

    ctx.comment('\n\nREMOVING 100ul TO WASTE\n')
    for col in costar_plate.rows()[0][:num_cols*2+2]:
        pick_up()
        p300.aspirate(100, col)
        p300.dispense(100, waste)
        p300.drop_tip()

    ctx.comment('\n\nWASHES\n')
    for _ in range(4):
        p300.pick_up_tip(reg_tips[reg_tipcount])
        for col in costar_plate.rows()[0][:num_cols*2+2]:
            p300.aspirate(260, res.wells()[0])
            p300.dispense(260, col.top())
        if _ < 3:
            p300.return_tip()
        else:
            p300.drop_tip()
            reg_tipcount += 1

        ctx.comment('\n\nDISCARDING WASH\n')
        for i, col in enumerate(costar_plate.rows()[0][:num_cols*2+2]):
            p300.pick_up_tip(tiprack300[2].rows()[0][i])
            p300.aspirate(260, col)
            p300.dispense(260, ctx.loaded_labwares[12].wells()[0])
            if _ < 3:
                p300.return_tip()
            else:
                p300.drop_tip()

    ctx.pause('''Washing complete. Add 10mL TMB to column 3 of the reservoir
                Select "Resume" on the Opentrons app to continue''')

    ctx.comment('\n\nADDING TMB\n')
    p300.pick_up_tip()
    for col in costar_plate.rows()[0][:num_cols*2+2]:
        p300.aspirate(100, tmb)
        p300.dispense(100, col.top())
        p300.blow_out()
    p300.drop_tip()

    ctx.pause('''Incubate Costar plate in the dark for 15 minutes at room
                temperature. Place 5mL stop solution in column 4
                of the reservoir.
                Select "Resume" on the Opentrons app to continue''')

    ctx.comment('\n\nADDING STOP SOLUTION\n')
    p300.pick_up_tip()
    for col in costar_plate.rows()[0][:num_cols*2+2]:
        p300.aspirate(50, stop_sol)
        p300.dispense(50, col.top())
        p300.blow_out()
    p300.drop_tip()
