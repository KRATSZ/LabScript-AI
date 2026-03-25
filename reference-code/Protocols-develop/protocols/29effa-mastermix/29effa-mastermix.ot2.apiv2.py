metadata = {
    'protocolName': 'Lyra Direct Covid-19 Mastermix Distribution',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [p20mnt, num_wells] = get_values(  # noqa: F821
     'p20mnt', 'num_wells')

    # load labware and pipette
    tempdeck = protocol.load_module('temperature module gen2', '3')
    plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul')
    tempdeck.set_temperature(3)

    tips = [protocol.load_labware('opentrons_96_filtertiprack_20ul', '2')]
    tuberack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '6')
    p20 = protocol.load_instrument('p20_single_gen2', p20mnt, tip_racks=tips)

    # variables
    wells = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2',
             'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3', 'D3', 'E3', 'F3',
             'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5',
             'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5', 'A6', 'B6', 'C6', 'D6',
             'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7',
             'H7', 'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9',
             'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10',
             'E10', 'F10', 'G10', 'H10', 'A11', 'B11', 'C11', 'D11', 'E11',
             'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12',
             'G12', 'H12'][:num_wells]

    mastermix = tuberack['D1']

    # transfer to wells
    p20.pick_up_tip()

    for well in wells:
        p20.aspirate(15, mastermix)
        p20.dispense(15, plate[well])
        p20.blow_out()

    p20.drop_tip()

    protocol.comment('Protocol Complete!')
