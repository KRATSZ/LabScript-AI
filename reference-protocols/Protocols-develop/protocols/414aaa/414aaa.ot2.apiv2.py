import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Reagent Preparation for Kingfisher Extraction',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, m300_mount] = get_values(  # noqa: F821
        "num_samp", "m300_mount")

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a sample number between 1-96")

    num_col = math.ceil(num_samp/8)

    # labware
    reag_reservoir = ctx.load_labware('nest_12_reservoir_15ml', 1)
    ethanol_res = ctx.load_labware('nest_1_reservoir_195ml', 2)
    wash_buffer_res = ctx.load_labware('nest_1_reservoir_195ml', 3)
    reagent_plate = ctx.load_labware('kingfisher_96_wellplate_2000ul', 5, label='Deepwell Plate')  # noqa: E501

    sample_plate = ctx.load_labware('kingfisher_96_wellplate_2000ul', 4, label='Deepwell Plate')  # noqa: E501
    ethanol_plates = [ctx.load_labware('kingfisher_96_wellplate_2000ul', slot, label='Deepwell Plate')  # noqa: E501
                      for slot in [7, 8]]
    wash_buffer_plates = [ctx.load_labware('kingfisher_96_wellplate_2000ul',
                          slot)
                          for slot in [10, 11]]

    elution_plate = ctx.load_labware('kingfisher_96_wellplate_2000ul', 6, label='Deepwell Plate')  # noqa: E501
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [9]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    def pick_up():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks.")
            m300.reset_tipracks()
            pick_up()

    # mapping
    binding_buffer = reag_reservoir.wells()[:4][:math.ceil(num_col/3)]*12
    ethanol = ethanol_res.wells()[0]
    wash_buffer = wash_buffer_res.wells()[0]
    binding_bead = reagent_plate.rows()[0][0]
    elution_buffer = reagent_plate.rows()[0][-1]

    # protocol
    ctx.comment('\n---------------ADDING ETHANOL TO PLATES---------------\n\n')
    pick_up()
    for plate in ethanol_plates:
        for col in plate.rows()[0][:num_col]:
            m300.transfer(1000, ethanol, col, new_tip='never')
        ctx.comment('\n')
    m300.drop_tip()

    ctx.comment('\n------------ADDING WASH BUFFER TO PLATES--------------\n\n')
    pick_up()
    for plate in wash_buffer_plates:
        for col in plate.rows()[0][:num_col]:
            m300.transfer(1000, wash_buffer, col, new_tip='never')
        ctx.comment('\n')
    m300.drop_tip()

    ctx.comment('\n---------ADDING BINDING SOLUTION TO PLATES---------\n\n')
    for s, d in zip(binding_buffer, sample_plate.rows()[0][:num_col]):
        pick_up()
        m300.transfer(550, s, d, new_tip='never')
        m300.mix(5, 200, d)
        m300.drop_tip()
    ctx.comment('\n')

    ctx.comment('\n---------ADDING BINDING BEADS TO PLATES---------\n\n')
    for col in sample_plate.rows()[0][:num_col]:
        pick_up()
        m300.mix(5, 200, binding_bead)
        m300.transfer(50, binding_bead, d, new_tip='never')
        m300.mix(10, 200, col)
        m300.drop_tip()
        ctx.comment('\n')

    ctx.comment('\n---------ADDING ELUTION TO PLATES---------\n\n')
    pick_up()
    for col in elution_plate.rows()[0][:num_col]:
        m300.transfer(50, elution_buffer, col, new_tip='never')
    ctx.comment('\n')
    m300.drop_tip()
