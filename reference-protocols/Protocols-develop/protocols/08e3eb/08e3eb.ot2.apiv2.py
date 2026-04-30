metadata = {
    'protocolName': 'Custom Plate Filling',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [start_tip, run_number] = get_values(  # noqa: F821
        'start_tip', 'run_number')

    # load labware and pipettes
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', '10')

    m50 = protocol.load_instrument('p50_multi', 'left')

    reservoir = protocol.load_labware('agilent_48_reservoir_5000ul', '11')

    plates = [
        protocol.load_labware(
            'microamp_96well_200ul',
            str(slot)) for slot in range(1, 10)]

    dest1 = [plate[x] for plate in plates for x in ['A1', 'A5', 'A9']]
    dest2 = [plate[x] for plate in plates for x in ['A2', 'A6', 'A10']]
    dest3 = [plate[x] for plate in plates for x in ['A3', 'A7', 'A11']]
    dest4 = [plate[x] for plate in plates for x in ['A4', 'A8', 'A12']]

    start_tip = int(start_tip)

    destinations = [dest1, dest2, dest3, dest4]
    sources = [reservoir[x] for x in ['A1', 'A2', 'A3', 'A4']]
    tips = [tips300['A'+str(t)] for t in range(start_tip, start_tip+4)]

    for x in range(run_number):
        for tip, src, dest in zip(tips, sources, destinations):
            m50.pick_up_tip(tip)
            m50vol = 0
            for d in dest:
                if m50vol < 10:
                    m50.dispense(m50vol, src)
                    m50.aspirate(50, src)
                    m50vol = 50
                m50.dispense(6, d)
                m50vol -= 6
            m50.dispense(m50vol, src)
            m50.blow_out()
            m50.return_tip() if x == run_number-1 else m50.drop_tip()
        m50.home()
        for i in range(6):
            protocol.set_rail_lights(not protocol.rail_lights_on)
            protocol.delay(seconds=1)
        if x == run_number-1:
            protocol.comment('Protocol complete!')
        else:
            pause_msg = 'Plates filled. Please replace plates and click RESUME'
            protocol.pause(pause_msg)
