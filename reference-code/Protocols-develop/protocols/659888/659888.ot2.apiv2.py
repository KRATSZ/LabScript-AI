metadata = {
    'protocolName': 'Dispensing Diluted Phage to Agar Plates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_plates, vol, num_col, num_row, p20_mount] = get_values(  # noqa: F821
        "num_plates", "vol", "num_col", "num_row", "p20_mount")

    if not 1 <= num_col <= 12:
        raise Exception("Enter a column number 1-12")
    if not 1 <= num_row <= 8:
        raise Exception("Enter a row number 1-12")
    if not 1 <= num_plates <= 9:
        raise Exception("Enter a plate number 1-12")

    num_col = int(num_col)
    num_row = int(num_row)
    num_plates = int(num_plates)
    vol = int(vol)

    # load labware
    agar1 = ctx.load_labware('127x85_agar_plate1', '1')
    agar2 = ctx.load_labware('127x85_agar_plate2', '2')
    agar3 = ctx.load_labware('127x85_agar_plate3', '3')
    agar4 = ctx.load_labware('127x85_agar_plate4', '4')
    agar5 = ctx.load_labware('127x85_agar_plate5', '5')
    agar6 = ctx.load_labware('127x85_agar_plate6', '6')
    agar7 = ctx.load_labware('127x85_agar_plate7', '7')
    agar8 = ctx.load_labware('127x85_agar_plate8', '8')
    agar9 = ctx.load_labware('127x85_agar_plate9', '9')
    dilution_plate = ctx.load_labware('corning_96_wellplate_360ul_flat', '11')
    tiprack = ctx.load_labware('opentrons_96_filtertiprack_20ul', '10')

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=[tiprack])
    m20.flow_rate.aspirate = 0.5*m20.flow_rate.aspirate
    m20.flow_rate.dispense = 0.5*m20.flow_rate.dispense

    # multi as single channel
    num_chan = num_row
    tips_ordered = [
                    tip
                    for row in tiprack.rows()[
                     len(tiprack.rows())-num_chan::-1*num_chan]
                    for tip in row]

    tip_count = 0

    def pick_up():
        nonlocal tip_count
        m20.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # PROTOCOL

    plates = [agar1, agar2, agar3, agar4, agar5,
              agar6, agar7, agar8, agar9][:num_plates]
    for col_ctr in range(num_col):
        pick_up()
        m20.distribute(vol,
                       dilution_plate.rows()[0][col_ctr],
                       [plate.rows()[0][col_ctr] for plate in plates],
                       new_tip='never')
        m20.drop_tip()
        ctx.comment('\n\n\n\n')
