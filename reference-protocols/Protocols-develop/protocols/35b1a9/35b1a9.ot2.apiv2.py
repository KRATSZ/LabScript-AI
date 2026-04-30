metadata = {
    'protocolName': 'Transfer BHI to Lysis Buffer',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(protocol):
    [pip_mnt, samp_no] = get_values(  # noqa: F821
        'pip_mnt', 'samp_no')

    # load labware
    tips = protocol.load_labware('generic_96_tiprack_20ul', '1')
    src = protocol.load_labware('custom_96_tubeholder_500ul', '2')
    dest = protocol.load_labware('custom_96_tubeholder_500ul', '3')
    pip = protocol.load_instrument('p300_multi', pip_mnt, tip_racks=[tips])

    row_no = samp_no//8
    rows_samp = row_no if samp_no % 8 == 0 else row_no + 1

    src_rows = src.rows()[0][:rows_samp]
    dest_rows = dest.rows()[0][:rows_samp]

    for s, d in zip(src_rows, dest_rows):
        pip.transfer(10, s.bottom(20), d.bottom(20), air_gap=2)
