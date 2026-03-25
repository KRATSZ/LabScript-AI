metadata = {
    'protocolName': 'Single-/Multi-Channel Calibration',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(protocol):
    [pip_type, pip_mnt, tt_asp, tt_disp] = get_values(  # noqa: F821
        'pip_type', 'pip_mnt', 'tt_asp', 'tt_disp')

    # load labware
    tips = protocol.load_labware('opentrons_96_filtertiprack_200ul', '1')
    tuberack = protocol.load_labware('custom_96_tubeholder_500ul', '3')
    pip = protocol.load_instrument(pip_type, pip_mnt, tip_racks=[tips])

    def single_trans(start_letter, vol):
        init_well = start_letter + '1'  # start letter should be str
        pip.pick_up_tip()
        for i in range(2, 5):
            pip.aspirate(vol, tuberack[init_well].bottom(10))
            if tt_asp == 'yes':
                pip.move_to(tuberack[init_well].top(-5))
                pip.touch_tip()
            pip.dispense(vol, tuberack[start_letter+str(i)].top(-10))
            if tt_disp == 'yes':
                pip.touch_tip()
        pip.drop_tip()

    def multi_trans(start_col, vol):
        pip.pick_up_tip()
        for i in range(start_col+1, start_col+4):
            pip.aspirate(vol, tuberack['A'+str(start_col)].bottom(10))
            if tt_asp == 'yes':
                pip.move_to(tuberack['A'+str(start_col)].top(-5))
                pip.touch_tip()
            pip.dispense(vol, tuberack['A'+str(i)].top(-10))
            if tt_asp == 'yes':
                pip.touch_tip()
        pip.drop_tip()

    vols = [5, 50, 200]

    if pip_type == 'p300_single':
        for ltr, v in zip('ABC', vols):
            single_trans(ltr, v)
    else:
        for col, v in zip([1, 5, 9], vols):
            multi_trans(col, v)
