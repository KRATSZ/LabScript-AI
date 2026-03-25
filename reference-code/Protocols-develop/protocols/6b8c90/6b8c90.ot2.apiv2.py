metadata = {
    'protocolName': '48 MCT to 1mL Vial',
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
            'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap_acrylic',
            s) for s in ['2', '5']
            ]
    mctSamps = [well for plate in mct for well in plate.wells()][:num_samps]

    v1ml = [
        protocol.load_labware(
            'custom1mltesttube_24_wellplate_5000ul',
            s) for s in ['3', '6']
            ]

    vials = [well for plate in v1ml for well in plate.wells()][:num_samps]

    for src, dest in zip(mctSamps, vials):
        p300.pick_up_tip()
        p300.aspirate(300, src.bottom(10))
        p300.dispense(300, dest.bottom(20))
        p300.blow_out()
        p300.touch_tip(dest, v_offset=-2)
        p300.drop_tip()

    protocol.comment('Protocol complete!')
