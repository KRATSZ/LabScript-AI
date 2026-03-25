metadata = {
    'protocolName': 'Cerillo Plate Reader Protocol',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [csv_stock, csv_buff, dilute_stock, sol_vol,
        p300_mount, m300_mount] = get_values(  # noqa: F821
        "csv_stock", "csv_buff", "dilute_stock", "sol_vol",
            "p300_mount", "m300_mount")

#     csv_stock = """
# x,1,2,3,4,5,6,7,8,9,10,11,12
# A,x,20,20,20,20,20,20,20,20,20,20,20
# B,X,40,40,40,40,40,40,40,40,40,40,40
# C,x,29,29,29,29,29,29,29,29,29,29,29
# D,40,40,40,40,40,40,40,40,40,40,40,40
# E,29,29,29,29,29,29,29,29,29,29,29,29
# F,40,40,40,40,40,40,40,40,40,40,40,40
# G,29,29,29,29,29,29,29,29,29,29,29,29
# H,40,40,40,40,40,40,40,40,40,40,40,40
#     """
#
#     csv_buff = """
# x,1,2,3,4,5,6,7,8,9,10,11,12
# A,20,40,34,20,22,44,89,90,92,29,84,29
# B,74,29,49,72,49,32,89,29,88,44,22,40
# C,20,40,34,20,22,44,89,90,92,29,84,29
# D,74,29,49,72,49,32,89,29,88,44,22,40
# E,20,40,34,20,22,44,89,90,92,29,84,29
# F,74,29,49,72,49,32,89,29,88,44,22,40
# G,20,40,34,20,22,44,89,90,92,29,84,29
# H,74,29,49,72,49,32,89,29,88,44,22,40
#     """

    # labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 5)
    plate_reader = ctx.load_labware('cerillo_stratus_armadillo_flatbottom_200ul', 1)  # noqa: E501
    deepwell = ctx.load_labware('nest_96_wellplate_2ml_deep', 3)
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [7, 8, 9]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=tips)

    csv_lines_stock = [[val.strip() for val in line.split(',')][1:]
                       for line in csv_stock.splitlines()
                       if line.split(',')[0].strip()][1:]

    csv_lines_buff = [[val.strip() for val in line.split(',')][1:]
                      for line in csv_buff.splitlines()
                      if line.split(',')[0].strip()][1:]

    # mapping
    stock_solution = reservoir.wells()[0]
    buffer = reservoir.wells()[1]
    cells = reservoir.wells()[-1]

    if dilute_stock:

        # protocol
        ctx.comment('\n---------------ADDING BUFFER TO PLATE-------------\n\n')
        p300.pick_up_tip()
        for line, row in zip(csv_lines_buff, deepwell.rows()):
            for well_vol, well_name in zip(line, row):
                if well_vol.lower() == 'x':
                    continue
                well_vol = int(well_vol)
                dest_well = well_name
                p300.aspirate(well_vol, buffer)
                p300.dispense(well_vol, dest_well)
        p300.drop_tip()

        ctx.comment('\n---------------ADDING STOCK TO PLATE--------------\n\n')
        p300.pick_up_tip()
        for line, row in zip(csv_lines_stock, deepwell.rows()):
            for well_vol, well_name in zip(line, row):
                if well_vol.lower() == 'x':
                    continue
                well_vol = int(well_vol)
                dest_well = well_name
                p300.aspirate(well_vol, stock_solution)
                p300.dispense(well_vol, dest_well.top())
        p300.drop_tip()

        ctx.comment('\n-------------Mixing solution and stock------------\n\n')
        for s, d in zip(deepwell.rows()[0], plate_reader.rows()[0]):
            m300.pick_up_tip()
            m300.mix(5, 50, s)
            m300.aspirate(sol_vol, s)
            m300.dispense(sol_vol, d)
            m300.drop_tip()

    else:
        ctx.comment('\n-----------Transferring solution to reader-------\n\n')
        for s, d in zip(deepwell.rows()[0], plate_reader.rows()[0]):
            m300.pick_up_tip()
            m300.aspirate(sol_vol, s)
            m300.dispense(sol_vol, d)
            m300.drop_tip()

    ctx.comment('\n-------------Transferring cells to reader-------------\n\n')
    m300.pick_up_tip()
    m300.mix(20, 200, cells)
    for col in plate_reader.rows()[0]:
        m300.aspirate(180, cells)
        m300.dispense(180, col)
        m300.mix(3, 150, col)
    m300.drop_tip()
