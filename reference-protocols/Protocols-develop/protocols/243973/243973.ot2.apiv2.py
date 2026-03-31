import smtplib
import ssl

metadata = {
    'protocolName': 'Protein Normalizaton with Email Notifications',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt300, mnt20, numPlates, t_csv, em, pw] = get_values(  # noqa: F821
     'mnt300', 'mnt20', 'numPlates', 't_csv', 'em', 'pw')

    # load labware
    t300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '10')]
    t20 = [protocol.load_labware('opentrons_96_tiprack_20ul', '11')]

    m300 = protocol.load_instrument('p300_multi_gen2', mnt300, tip_racks=t300)
    m20 = protocol.load_instrument('p20_multi_gen2', mnt20, tip_racks=t20)

    rsvr = protocol.load_labware('nest_12_reservoir_15ml', '9').wells()[0]
    proteinPlate = protocol.load_labware(
        'greinerbioone_96_wellplate_200ul_650161', '8')

    plateDict = {}
    plates = [
        protocol.load_labware(
            'greinerbioone_96_wellplate_200ul_650161', s) for s in range(1, 8)
        ][:numPlates]

    for i in range(numPlates):
        plateDict[str(i+1)] = plates[i]

    # Create variables based on data
    if numPlates < 1 or numPlates > 7:
        raise Exception('The number of plates should be between 1-7.')

    dil300 = []
    dil20 = []
    transfer_info = [
        line.split(',')
        for line in t_csv.splitlines() if line
    ][1:]
    for data in transfer_info:
        if float(data[4].strip()) > 20:
            dil300.append([d.strip() for d in [data[1], data[2], data[4]]])
        elif float(data[4]) > 0:
            dil20.append([d.strip() for d in [data[1], data[2], data[4]]])
        else:
            continue

    vol300 = []
    vol20 = []

    for data in transfer_info:
        if float(data[3].strip()) > 20:
            vol300.append([d.strip() for d in data[:4]])
        elif float(data[3].strip()) > 0:
            vol20.append([d.strip() for d in data[:4]])
        else:
            continue

    # transfer dilutents
    protocol.comment('Beginning protocol. Transferring diluents...\n')
    protocol.set_rail_lights(True)
    if dil300:
        m300.pick_up_tip()
        for d in dil300:
            m300.transfer(
                float(d[2]), rsvr, plateDict[d[0]][d[1]], new_tip='never')
        m300.drop_tip()

    if dil20:
        m20.pick_up_tip()
        for d in dil20:
            m20.transfer(
                float(d[2]), rsvr, plateDict[d[0]][d[1]], new_tip='never')
        m20.drop_tip()

    # inform user that this step is done
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "OTProtocolStatus@gmail.com"
    message = """Subject: OT-2 ~~ Step 1 complete\n\n
    Step 1 complete. Please add protein plate to deck."""

    context = ssl.create_default_context()
    if not protocol.is_simulating() and pw != '********':
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, pw)
            server.sendmail(sender_email, em, message)

    protocol.set_rail_lights(False)
    protocol.pause('Please add protein plate to deck.')
    protocol.set_rail_lights(True)

    # transfer proteins
    if vol300:
        for d in vol300:
            m300.transfer(
                float(d[3]), proteinPlate[d[0]],
                plateDict[d[1]][d[2]], mix_after=(4, 50)
                )

    if vol20:
        for d in vol20:
            m20.transfer(
                float(d[3]), proteinPlate[d[0]],
                plateDict[d[1]][d[2]], mix_after=(4, 20)
                )

    if not protocol.is_simulating() and pw != '********':
        message = """Subject: OT-2 ~~ Protocol complete\n\n
        Protocol is now complete!"""
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, pw)
            server.sendmail(sender_email, em, message)
    protocol.comment('Protocol complete!')
    protocol.set_rail_lights(False)
