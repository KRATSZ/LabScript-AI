import math

metadata = {
    'protocolName': 'Version Update - Master RBC Transfer',
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
    plate = protocol.load_labware('omegaquant_96_wellplate_1000ul', '2')
    trough_1 = protocol.load_labware(
                        'electronmicroscopysciences_1_reservoir_100000ul', '3')
    trough_2 = protocol.load_labware(
                        'electronmicroscopysciences_1_reservoir_100000ul', '5')
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', '4')
    tiprack_50 = protocol.load_labware('tiprack_200ul_extended', '6')
    sample_trays = [protocol.load_labware('generic_24_tuberack_2000ul', slot)
                    for slot in ['7', '8', '10', '11']]
    # instruments setup
    p50 = protocol.load_instrument('p50_single', 'right',
                                   tip_racks=[tiprack_50])
    m300 = protocol.load_instrument('p300_multi',
                                    'left', tip_racks=[tiprack_300])
    # Reagent setup and transfer
    bf3 = trough_1['A1']
    wistd = trough_2['A1']
    # protocol
    if number_of_samples >= 12:
        plate_loc = [col for col in plate.rows()[0]]
    else:
        plate_loc = [col for col in plate.rows()[0]][:num_columns]
    samples = [well for tray in sample_trays for well in tray.wells()]
    outputs = [well for row in plate.rows() for well in row]
    # transfer blood from tube to 96-well plate
    for index in range(number_of_samples):
        p50.pick_up_tip(presses=4, increment=.2)
        p50.aspirate(25, samples[index].bottom(4))
        protocol.delay(seconds=3)
        p50.dispense(25, outputs[index].bottom(5))
        p50.blow_out()
        p50.touch_tip(v_offset=-25)
        protocol.delay(seconds=1)
        p50.drop_tip()
    # transfer 14% BF3-MeOH to wells
    m300.pick_up_tip(tiprack_300.rows()[0][tip_start_column])
    m300.mix(3, 300, bf3)
    m300.blow_out(bf3)
    for dest in plate_loc:
        m300.transfer(250, bf3, dest.top(), blow_out=True, new_tip='never')
    m300.drop_tip()
    # transfer WISTD to wells
    m300.pick_up_tip()
    m300.mix(3, 300, wistd)
    m300.blow_out(wistd)
    for dest in plate_loc:
        m300.transfer(250, wistd, dest.top(),
                      blow_out=True, new_tip='never')
    m300.drop_tip()
