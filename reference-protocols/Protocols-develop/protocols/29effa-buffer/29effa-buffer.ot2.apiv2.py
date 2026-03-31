import math

metadata = {
    'protocolName': 'Lyra Direct Covid-19 Buffer Distribution',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [p300mnt, num_wells] = get_values(  # noqa: F821
     'p300mnt', 'num_wells')

    # load labware and pipette
    tips = [protocol.load_labware('opentrons_96_tiprack_300ul', '1')]
    m300 = protocol.load_instrument('p300_multi_gen2', p300mnt, tip_racks=tips)

    plate = protocol.load_labware('eppendorf_96_wellplate_1000ul', '4')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '7')

    # variables
    buffers = [well for well in reservoir.wells()[:4] for _ in range(3)]
    num_cols = math.ceil(num_wells/8)
    wells = plate.rows()[0][:num_cols]

    # transfers
    m300.pick_up_tip()

    for buffer, well in zip(buffers, wells):
        for _ in range(2):
            m300.aspirate(200, buffer)
            m300.dispense(200, well)
        m300.blow_out(well.bottom(1))

    m300.drop_tip()

    protocol.comment('Protocol Complete!')
