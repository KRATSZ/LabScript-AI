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
    small_tips = protocol.load_labware('generic_96_tiprack_20ul', '1')
    big_tips = protocol.load_labware('generic_96_tiprack_200ul', '2')
    tuberack = protocol.load_labware('custom_96_tubeholder_500ul', '3')
    pip = protocol.load_instrument(pip_type, pip_mnt)

    def single_trans(start_letter, vol, tip):
        init_well = start_letter + '1'  # start letter should be str
        tips = small_tips if vol < 20 else big_tips
        pip.pick_up_tip(tips.wells_by_name()[tip])
        for i in range(2, 5):
            pip.aspirate(vol, tuberack[init_well].bottom(10))
            if tt_asp == 'yes':
                pip.move_to(tuberack[init_well].top(-5))
                pip.touch_tip()
            pip.dispense(vol, tuberack[start_letter+str(i)].top(-10))
            if tt_disp == 'yes':
                pip.touch_tip()
        pip.drop_tip()

    def multi_trans(start_col, vol, tip):
        tips = small_tips if vol < 20 else big_tips
        pip.pick_up_tip(tips.wells_by_name()[tip])
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
    twell = ['A1', 'A1', 'A2']

    if pip_type == 'p300_single':
        for ltr, v, t in zip('ABC', vols, twell):
            single_trans(ltr, v, t)
    else:
        for col, v, t in zip([1, 5, 9], vols, twell):
            multi_trans(col, v, t)
