import math

metadata = {
    'protocolName': 'Version Update - Adding BTM to DBS',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):

    [number_of_samples, tip_start_column] = get_values(  # noqa: F821
        "number_of_samples", "tip_start_column")

    number_of_samples = int(number_of_samples)
    tip_start_column = int(tip_start_column)
    num_columns = math.ceil(number_of_samples/8)

    if not 1 <= number_of_samples <= 96:
        raise Exception("Enter a sample number between 1-96")
    if not 1 <= tip_start_column <= 12:
        raise Exception("Enter a column number between 1-12")

    # labware setup
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    trough = protocol.load_labware(
                        'electronmicroscopysciences_1_reservoir_100000ul', '1')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '4')

    # instrument setup
    m300 = protocol.load_instrument('p300_multi', 'left', tip_racks=[tiprack])

    # reagent setup
    source = trough['A1']

    # protocol
    if number_of_samples >= 12:
        plate_loc = [col for col in plate.rows()[0]]

    else:
        plate_loc = [col for col in plate.rows()[0]][:num_columns]

    m300.pick_up_tip(tiprack.rows()[0][tip_start_column], presses=4)
    m300.mix(3, 300, source)
    m300.blow_out(source)

    for dest in plate_loc:
        m300.transfer(250, source, dest.top(), blow_out=True, new_tip='never')
    m300.drop_tip()
