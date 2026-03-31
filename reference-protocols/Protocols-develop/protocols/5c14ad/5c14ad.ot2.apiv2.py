metadata = {
    'protocolName': 'Lysis Pre-Fill (Salmonella/Listeria)',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(protocol):
    [lysis, pip_type, pip_mnt, no_plates, tip_no] = get_values(  # noqa: F821
        'lysis', 'pip_type', 'pip_mnt', 'no_plates', 'tip_no')

    # load labware
    tips = protocol.load_labware('generic_96_tiprack_200ul', '1', 'Tips')
    res = protocol.load_labware('nest_1_reservoir_195ml', '2', 'Reservoir')
    p300 = protocol.load_instrument(pip_type, pip_mnt)

    plates = []
    plate_start = 3
    for i in range(no_plates):
        plates.append(
            protocol.load_labware(
                'custom_96_tubeholder_500ul',
                str(plate_start),
                'Plate '+str(i+1)
                )
            )
        plate_start += 1

    # create wells/columns for pipette type
    for x in range(len(plates)):
        if pip_type == 'p300_single':
            plates[x] = plates[x].wells()
        else:
            plates[x] = plates[x].rows()[0]

    # pick up tip
    tip_spot = 'A'+str(tip_no)
    p300.pick_up_tip(tips[tip_spot])

    # transfer according to lysis
    vol = int(lysis)

    pip_vol = 0

    for plate in plates:
        for w in plate:
            if pip_vol == 0:
                p300.aspirate(vol, res['A1'])
                pip_vol += vol
            p300.dispense(vol/2, w)
            pip_vol -= vol/2

    p300.drop_tip()
