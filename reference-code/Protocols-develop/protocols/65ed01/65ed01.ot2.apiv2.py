from opentrons.types import Point


metadata = {
    'protocolName': 'Nucleic Acid Purification with Magnetic Beads',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [length_from_side, p300_mount] = get_values(  # noqa: F821
        "length_from_side", "p300_mount")

    if not 1 <= length_from_side <= 4.05:
        raise Exception("Enter a number between 1 and 4.05")

    # load labware
    mag_deck = ctx.load_module('magnetic module gen2', '6')
    pcr_alum = ctx.load_labware(
                'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '1')
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_200ul',
                                 slot, f'Tip Box {slot}')
                for slot in ['2', '3']]
    ydp_plate = mag_deck.load_labware('ydp962_2sc_96_wellplate_2200ul')
    reservoir = ctx.load_labware('nest_1_reservoir_195ml', '11')

    # load instruments
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tipracks)

    # functions for protocol

    # transfer_col() takes a source and destination column along with a list of
    # volumes to transfer. The function also takes in a list for the aspiration
    # and dispense height respectively, for each transfer volume
    def transfer_col(source_col, dest_col, transfer_vols,
                     asp_heights, disp_heights):
        for i in range(len(transfer_vols)):
            p300.aspirate(transfer_vols[i],
                          ydp_plate[source_col].bottom(
                                asp_heights[i]))
            p300.dispense(transfer_vols[i],
                          ydp_plate[dest_col].bottom(
                                disp_heights[i]))

    # change_speeds() globally changes the aspiration and dispense flow rate
    # in uL/sec
    def change_speeds(asp_speed, disp_speed):
        p300.flow_rate.aspirate = asp_speed
        p300.flow_rate.dispense = disp_speed

    # mix_height() takes in the number of mixes as well as aspiration and
    # dispense height to peform a custom mix
    def mix_height(num_mix, vol, column, asp_height, disp_height):
        for i in range(0, num_mix):
            p300.aspirate(vol, ydp_plate[column].bottom(asp_height))
            p300.dispense(vol, ydp_plate[column].bottom(disp_height))

    # remove_supernat() takes in a list of transfer volumes and column number -
    # the function aspirates from column in ydp plate on the side of the well
    # opposite magnetic beads. Disposes in A1 of nest reservoir. Aspiration
    # position of tips from ydp plate and dispense position at nest reservoir
    # can also be specified.
    def remove_supernat(transfer_vols, column, asp_height=2, disp_height=27):
        col_index = column - 1
        side = -1 if col_index % 2 == 0 else 1
        col = ydp_plate.rows()[0][col_index]
        aspirate_loc = col.bottom(asp_height).move(
                Point(x=(col.length/2-length_from_side)*side))
        dest = ['A1' for i in range(len(transfer_vols))]
        p300.move_to(col.center())
        p300.transfer(transfer_vols, aspirate_loc,
                      [reservoir[well].top(disp_height) for well in dest],
                      new_tip='never')

    # NOTE - numbers in parenthesis in comment headers below correspond
    # to the respective steps in the protocol designer file

    # add lysis buffer in sample (1-3)
    p300.pick_up_tip()
    change_speeds(50, 200)
    mix_height(1, 150, 'A4', asp_height=2, disp_height=0.5)

    asp_heights = [2, 0.5]
    disp_heights = [2, 0.5]
    transfer_col('A4', 'A3', [150, 150],
                 asp_heights, disp_heights)
    change_speeds(150, 300)
    p300.mix(20, 150, ydp_plate['A3'].bottom(2.5))
    p300.drop_tip()

    # add lysis buffer in sample from column 10 to column 9 (4-7), delay 3 min
    p300.pick_up_tip()
    change_speeds(50, 300)
    mix_height(1, 150, 'A10', asp_height=2, disp_height=1.5)

    asp_heights = [2, 2]
    disp_heights = [1.5, 1.5]
    transfer_col('A10', 'A9', [150, 150],
                 asp_heights, disp_heights)
    change_speeds(150, 300)
    p300.mix(20, 150, ydp_plate['A9'].bottom(2))
    p300.drop_tip()
    ctx.delay(minutes=3)

    # add lysate to beads from column 3 into column 1 (8-11)
    p300.pick_up_tip()
    change_speeds(50, 300)
    mix_height(1, 200, 'A3', asp_height=2, disp_height=2.5)

    asp_heights = [2, 2, 2]
    disp_heights = [2.5, 2.5, 2.5]
    transfer_col('A3', 'A1', [200, 200, 100],
                 asp_heights, disp_heights)
    mix_height(12, 200, 'A1', asp_height=2, disp_height=0.5)
    p300.drop_tip()

    # add lysate to beads from column 9 into column 7 (12-15)
    p300.pick_up_tip()
    mix_height(1, 200, 'A9', asp_height=2, disp_height=2.5)

    asp_heights = [2, 2, 2]
    disp_heights = [2.5, 2.5, 2.5]
    transfer_col('A9', 'A7', [200, 200, 100],
                 asp_heights, disp_heights)
    mix_height(12, 200, 'A7', asp_height=2, disp_height=0.5)
    p300.drop_tip()

    # add isoproponal from column 2 into column 1 (16-18)
    p300.pick_up_tip()
    mix_height(1, 200, 'A2', asp_height=2, disp_height=0.5)

    asp_heights = [2, 2]
    disp_heights = [0.5, 0.5]
    transfer_col('A2', 'A1', [200, 200],
                 asp_heights, disp_heights)
    mix_height(12, 200, 'A1', asp_height=2, disp_height=0.5)
    p300.drop_tip()

    # add isoproponal from column 8 to 7 (19-21)
    p300.pick_up_tip()
    mix_height(1, 200, 'A8', asp_height=3, disp_height=0.5)

    asp_heights = [3, 2]
    disp_heights = [0.5, 0.5]
    transfer_col('A8', 'A7', [200, 200],
                 asp_heights, disp_heights)
    mix_height(12, 200, 'A7', asp_height=2, disp_height=0.5)
    p300.drop_tip()

    # delay and engage magnetic module
    ctx.delay(minutes=3)
    mag_deck.engage(height_from_base=6)
    ctx.delay(minutes=1.5)

    # remove supernatant from column 1, 7, disengage (25 - 30)
    change_speeds(25, 300)
    p300.pick_up_tip()
    remove_supernat([200, 200, 200, 200], 1)
    change_speeds(15, 94)
    remove_supernat([130, 20], 1)
    p300.drop_tip()

    # remove supernatant from column 7 (31-37)
    p300.pick_up_tip()
    change_speeds(25, 300)
    remove_supernat([200], 7, asp_height=4)
    remove_supernat([200, 200, 200], 7, asp_height=3)
    remove_supernat([130, 20], 7, asp_height=2)
    p300.drop_tip()
    mag_deck.disengage()

    # 1st wash column 1 (38-40)
    p300.pick_up_tip()
    change_speeds(50, 300)
    p300.mix(1, 150, ydp_plate['A5'])
    asp_heights = [2, 2]
    disp_heights = [0.5, 2]
    transfer_col('A5', 'A1', [150, 150],
                 asp_heights, disp_heights)
    change_speeds(80, 300)
    mix_height(20, 150, 'A1', asp_height=2, disp_height=1)
    p300.drop_tip()

    # 1st wash column 7 (41-45)
    p300.pick_up_tip()
    change_speeds(50, 94)
    mix_height(1, 150, 'A11', asp_height=2, disp_height=0.5)
    asp_heights = [2, 2]
    disp_heights = [0.5, 0.5]
    transfer_col('A11', 'A7', [150, 150],
                 asp_heights, disp_heights)
    change_speeds(80, 300)
    mix_height(20, 150, 'A7', asp_height=2, disp_height=1)
    p300.drop_tip()
    mag_deck.engage(height_from_base=6)
    ctx.delay(minutes=1)

    # remove supernatant from column 1 and 7 (44-50)
    p300.pick_up_tip()
    change_speeds(25, 300)
    remove_supernat([150, 150], 1, asp_height=2, disp_height=10)
    p300.drop_tip()
    p300.pick_up_tip()
    change_speeds(25, 94)
    remove_supernat([200], 7, asp_height=4, disp_height=10)
    remove_supernat([100], 7, asp_height=2, disp_height=27)
    p300.drop_tip()
    mag_deck.disengage()

    # 2nd wash column 1, remove supernatant column 1 (51-59)
    p300.pick_up_tip()
    change_speeds(50, 300)
    mix_height(1, 150, 'A5', asp_height=2, disp_height=0.5)
    asp_heights = [2, 2]
    disp_heights = [0.5, 0.5]
    transfer_col('A5', 'A1', [150, 150],
                 asp_heights, disp_heights)
    change_speeds(80, 300)
    mix_height(20, 150, 'A1', asp_height=2, disp_height=1)
    p300.drop_tip()

    mag_deck.engage(height_from_base=6)
    ctx.delay(minutes=1.5)
    p300.pick_up_tip()
    change_speeds(25, 94)
    remove_supernat([200, 100, 30], 1, asp_height=2, disp_height=10)
    p300.drop_tip()
    mag_deck.disengage()

    # 2nd wash column 7, remove supernatant column 7 (60-69)
    p300.pick_up_tip()
    change_speeds(50, 300)
    mix_height(1, 150, 'A11', asp_height=2, disp_height=0.5)
    asp_heights = [2, 2]
    disp_heights = [0.5, 0.5]
    transfer_col('A11', 'A7', [150, 150],
                 asp_heights, disp_heights)
    change_speeds(80, 300)
    mix_height(20, 150, 'A7', asp_height=2, disp_height=1)
    p300.drop_tip()

    mag_deck.engage(height_from_base=6)
    ctx.delay(minutes=1.5)
    p300.pick_up_tip()
    change_speeds(25, 300)
    remove_supernat([200], 7, asp_height=4, disp_height=27)
    remove_supernat([100], 7, asp_height=3, disp_height=10)
    remove_supernat([30], 7)
    p300.drop_tip()
    mag_deck.disengage()
    ctx.delay(minutes=15)

    # removal extra supernatant col 1 and 7 (70-73)
    mag_deck.engage(height_from_base=6)
    p300.pick_up_tip()
    change_speeds(25, 94)
    remove_supernat([20], 1)
    p300.drop_tip()
    p300.pick_up_tip()
    change_speeds(25, 300)
    remove_supernat([20], 7)
    p300.drop_tip()
    mag_deck.disengage()

    # add, mix EB in col 1 and 7 (74-79)
    p300.pick_up_tip()
    change_speeds(24, 100)
    mix_height(1, 50, 'A6', asp_height=1.4, disp_height=0.5)
    asp_heights = [1.4]
    disp_heights = [0.5]
    transfer_col('A6', 'A1', [50],
                 asp_heights, disp_heights)
    change_speeds(50, 100)
    mix_height(1, 50, 'A1', asp_height=1, disp_height=2)
    mix_height(15, 25, 'A1', asp_height=1, disp_height=2)
    p300.drop_tip()

    p300.pick_up_tip()
    change_speeds(24, 100)
    mix_height(1, 50, 'A12', asp_height=2, disp_height=4)
    asp_heights = [2]
    disp_heights = [4]
    transfer_col('A12', 'A7', [50],
                 asp_heights, disp_heights)
    change_speeds(50, 100)
    mix_height(1, 50, 'A7', asp_height=1, disp_height=3)
    mix_height(15, 25, 'A7', asp_height=1, disp_height=3)
    p300.drop_tip()
    mag_deck.engage(height_from_base=6)
    ctx.delay(minutes=2)

    # transfer elute from column 1 and 7 to new Plate (79-81)

    change_speeds(25, 94)
    source = [ydp_plate.rows()[0][0], ydp_plate.rows()[0][6]]
    dest = [pcr_alum.rows()[0][0], pcr_alum.rows()[0][6]]

    for s, d in zip(source, dest):
        p300.pick_up_tip()
        asp_height = 1
        disp_height = 3
        p300.aspirate(40, s.bottom(asp_height))
        p300.dispense(40, d.bottom(disp_height))
        asp_height = 2
        disp_height = 4
        p300.drop_tip()
