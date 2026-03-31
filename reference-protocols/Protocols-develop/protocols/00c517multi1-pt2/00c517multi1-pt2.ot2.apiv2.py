import math

metadata = {
    'protocolName': 'VIB UGENT - Multi-channel Workflow Part 2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.15'
}


def run(ctx):

    [num_samp, m300_mount] = get_values(  # noqa: F821
        "num_samp", "m300_mount")

    # m300_mount = 'left'
    # num_samp = 96

    # labware
    c_18_tiprack = ctx.load_labware('agilent_96_c18omix_200ul', 1)
    agilent_1200 = ctx.load_labware('agilent_96_wellplate_1200ul', 2)

    waste_res = ctx.load_labware('nest_1_reservoir_195ml', 5)
    wash_buff_res = ctx.load_labware('nest_12_reservoir_15ml', 10)  # up to number of columns of sample  # noqa: E501
    reagent_plate = ctx.load_labware('nest_12_reservoir_15ml', 4)
    agilent_500 = [ctx.load_labware('agilent_96_wellplate_500ul', slot)
                   for slot in [7, 8, 9]]

    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in [6, 11]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips300)

    # mapping
    # trypsin = reagent_plate.rows()[0][0]
    acn = reagent_plate.rows()[0][0]
    equil_buffer = reagent_plate.rows()[0][1:3]
    eb = reagent_plate.rows()[0][3:5]
    waste = waste_res['A1']
    wash_buff_plate = agilent_500[0]
    elution_buff_plates = agilent_500[1:3]

    num_col = math.ceil(num_samp/8)
    sample_cols = agilent_1200.rows()[0][:num_col]

    tip_ctr = 0

    def pick_up_c18():
        nonlocal tip_ctr
        m300.pick_up_tip(c_18_tiprack.rows()[0][tip_ctr])
        tip_ctr += 1

    ctx.pause('''

    Place the following labware on deck:
    Opentrons tip rack with C18 OMIX tips on slot 1,
    Agilent plate (round wells, 1200 µl) containing dried peptides on slot 2,
    a 12 column reservoir containing 12 ml 2%ACN 0.1% TFA (column 1),
    20 ml equilibration buffer (column 2, 3), and 10mL elution buffer
    in columns 4, 5
    a 12 column reservoir containing 8mL wash buffer in each column up to
    the number of sample columns
    and 20 ml elution buffer (column 8) in slot 4,
    a one well reservoir on slot 5 (for waste),
    a 300 µl tiprack on slot 6
    and 3 96-well plates (Agilent 500 µl) in slots 7, 8 & 9.


    ''')

    # protocol
    ctx.comment('\n---------------43 - ADD ACN----------------\n\n')
    for col in sample_cols:
        m300.pick_up_tip()
        m300.aspirate(100, acn)
        m300.dispense(100, col)
        m300.mix(5, 80, col)
        m300.drop_tip()

    ctx.pause('''
    Add sample to lunatic chip manually to measure peptide concentration
    ''')

    ctx.comment('\n---------------46 - ADDING WASH BUFFER----------------\n\n')
    m300.pick_up_tip()
    for wash_well, col in zip(wash_buff_res.rows()[0],
                              wash_buff_plate.rows()[0][:num_col]):
        m300.transfer(400, wash_well, col, new_tip='never')
    m300.drop_tip()

    ctx.comment('\n-------------46 - ADDING ELUTION BUFFER--------------\n\n')
    m300.pick_up_tip()
    for eb_well, plate in zip(eb, elution_buff_plates):
        for col in plate.rows()[0][:num_col]:
            m300.aspirate(100, eb_well)
            m300.dispense(100, col)
    m300.drop_tip()

    ctx.comment('\n-------------46 - WASH STEPS--------------\n\n')
    for i, (wash_buff_res_col,
            wash_buff_col,
            eb1_col,
            eb2_col,
            sample_col) in enumerate(
               zip(wash_buff_res.rows()[0],
                   wash_buff_plate.rows()[0],
                   elution_buff_plates[0].rows()[0][:num_col],
                   elution_buff_plates[0].rows()[0][:num_col],
                   sample_cols,
                   )):
        pick_up_c18()
        for _ in range(3):
            m300.aspirate(100, equil_buffer[0 if i < 6 else 1], rate=0.2)
            m300.dispense(100, waste.top())

        for _ in range(5):
            m300.aspirate(100, wash_buff_res_col)
            m300.dispense(100, waste.top(), rate=0.2)

        m300.mix(20, 100, sample_col, rate=0.2)
        m300.aspirate(100, sample_col)
        m300.dispense(100, waste.top())

        for _ in range(3):
            m300.aspirate(100, wash_buff_col)
            m300.dispense(100, waste.top())

        m300.mix(10, 100, eb1_col, rate=0.2)
        m300.mix(10, 100, eb2_col, rate=0.2)
        m300.aspirate(100, eb2_col)
        m300.dispense(100, eb1_col)

        m300.drop_tip()

        ctx.comment('\n\n\n')
