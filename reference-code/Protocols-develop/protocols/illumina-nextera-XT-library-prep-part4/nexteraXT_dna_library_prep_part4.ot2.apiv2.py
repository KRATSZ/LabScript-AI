metadata = {
    'protocolName': 'Illumina Nextera XT NGS Prep 4: Pool Libraries',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.2'
    }


def run(protocol):
    [pip_type, pip_mount, samps, pools, pool_vol] = get_values(  # noqa: F821
        'pip_type', 'pip_mount', 'samps', 'pools', 'pool_vol')

    total_tips = samps * pools
    total_tr = total_tips // 96 + (1 if total_tips % 96 > 0 else 0)
    tip_size = pip_type.split('_')[0][1:]
    tip_size = '300' if tip_size == '50' else tip_size
    tip_name = 'opentrons_96_tiprack_'+tip_size+'ul'
    tips = [protocol.load_labware(tip_name, str(slot))
            for slot in range(3, 3+total_tr)]

    in_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '1', 'Load Plate'
    )
    tuberack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '2',
        'Tube Rack with 2mL Tube(s)'
    )

    pip = protocol.load_instrument(pip_type, pip_mount, tip_racks=tips)

    if samps <= 24:
        input = [well for col in in_plate.columns()[:6]
                 for well in col[:4]][:samps]
    else:
        input = [well for well in in_plate.wells()][:samps]

    # Transfer each library to pooling tube(s)
    for tube in tuberack.wells()[:pools]:
        pip.transfer(pool_vol, input, tube, new_tip='always')
