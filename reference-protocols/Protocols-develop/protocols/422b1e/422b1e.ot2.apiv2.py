metadata = {
    'protocolName': 'Titration Procedure',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}


def run(protocol):
    # load labware and pipettes
    p1000tips = protocol.load_labware('opentrons_96_tiprack_1000ul', '11')
    p1000 = protocol.load_instrument(
        'p1000_single_gen2', 'right', tip_racks=[p1000tips])

    dest_beaker = protocol.load_labware('custom_beaker', '4')
    waste_beaker = protocol.load_labware('custom_beaker', '8')
    tube_rack = protocol.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '9')
    tubes = [t for x in tube_rack.rows() for t in x]

    # create beaker height definitions
    # the number represents mm from defined bottom
    dest_ht = dest_beaker['A1'].bottom(1)
    waste_ht = waste_beaker['A1'].bottom(1)

    wait_time = 5  # this is how long the protocol will delay (min)

    # pick up tip
    p1000.pick_up_tip()  # this will always pick up tip from A1; can be changed

    for tube in tubes:
        for _ in range(2):
            p1000.aspirate(1000, tube)
            p1000.dispense(1000, dest_ht)
        protocol.comment('Delaying %s minutes' % wait_time)
        protocol.delay(minutes=wait_time)
        for _ in range(2):
            p1000.aspirate(1000, dest_ht)
            p1000.dispense(1000, waste_ht)

    p1000.drop_tip()
