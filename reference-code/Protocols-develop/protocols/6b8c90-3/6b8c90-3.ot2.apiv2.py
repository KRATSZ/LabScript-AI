metadata = {
    'protocolName': 'EtOH 48 Sample to 1mL Vial',
    'author': 'Chaz <chaz@opentrons.com>',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt50, num_samps] = get_values(  # noqa: F821
     'mnt50', 'num_samps')

    # load labware
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '7')
    p50 = protocol.load_instrument('p50_single', mnt50, tip_racks=[tips])

    v1ml = [
        protocol.load_labware(
            'custom1mltesttube_24_wellplate_5000ul',
            s) for s in ['2', '5']
            ]
    v1mls = [well for plate in v1ml for well in plate.wells()][:num_samps]

    v5ml = [
        protocol.load_labware(
            'custom5mltesttube_24_wellplate_5000ul',
            s) for s in ['1', '4']
            ]

    v5mls = [well for plate in v5ml for well in plate.wells()][:num_samps]

    for src, dest in zip(v5mls, v1mls):
        p50.pick_up_tip()
        p50.aspirate(50, src.bottom(40))
        p50.dispense(50, dest.bottom(20))
        p50.blow_out()
        p50.touch_tip(dest, v_offset=-2)
        p50.drop_tip()

    protocol.comment('Protocol complete!')
