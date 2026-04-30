metadata = {
    'protocolName': '48 Samples to MCT',
    'author': 'Chaz <chaz@opentrons.com>',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt300, num_samps] = get_values(  # noqa: F821
     'mnt300', 'num_samps')

    # load labware
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '7')
    p300 = protocol.load_instrument('p300_single', mnt300, tip_racks=[tips])

    mct = [
        protocol.load_labware(
            'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
            s) for s in ['2', '5']
            ]
    mctSamps = [well for plate in mct for well in plate.wells()][:num_samps]

    v5ml = [
        protocol.load_labware(
            'custom5mltesttube_24_wellplate_5000ul',
            s) for s in ['1', '4']
            ]

    vials = [well for plate in v5ml for well in plate.wells()][:num_samps]

    for src, dest in zip(vials, mctSamps):
        p300.pick_up_tip()
        p300.aspirate(100, src.bottom(40))
        p300.dispense(100, dest.bottom(20))
        p300.blow_out()
        p300.touch_tip(dest, v_offset=-2)
        p300.drop_tip()

    protocol.comment('Protocol complete!')
