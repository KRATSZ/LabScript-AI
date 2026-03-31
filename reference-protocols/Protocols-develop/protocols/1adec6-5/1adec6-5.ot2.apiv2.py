metadata = {
    'protocolName': 'Custom Supernatant Removal and PrestoBlue test [5/7]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt300, cellHt, transfer2] = get_values(  # noqa: F821
     'mnt300', 'cellHt', 'transfer2')

    # load labware
    tips = [
        protocol.load_labware('opentrons_96_tiprack_300ul', '7')
        ]

    m300 = protocol.load_instrument('p300_multi_gen2', mnt300, tip_racks=tips)
    srcPlate = protocol.load_labware('spl_96_wellplate_200ul_flat', '1')
    destPlate = protocol.load_labware('spl_96_wellplate_200ul_flat', '4')
    if transfer2:
        destPlate2 = protocol.load_labware('spl_96_wellplate_200ul_flat', '5')
        dest2Wells = destPlate2.rows()[0][:10]
    rsvr = protocol.load_labware('nest_12_reservoir_15ml', '6')

    # Variables
    pbs = rsvr['A2']
    srcWells = srcPlate.rows()[0][:10]
    destWells = destPlate.rows()[0][:10]

    # Transfer 220uL supernatant from src to dest
    m300.flow_rate.aspirate = 30
    for idx, (src, dest) in enumerate(zip(srcWells, destWells)):
        m300.pick_up_tip()
        m300.transfer(
            220, src.bottom(cellHt), dest, air_gap=20, new_tip='never')
        if transfer2:
            m300.transfer(
                110, dest, dest2Wells[idx], air_gap=20, new_tip='never')
        m300.drop_tip()

    # Transfer 100uL PBS to src wells
    m300.flow_rate.aspirate = 50
    m300.pick_up_tip()
    for well in srcWells:
        m300.transfer(100, pbs, well.top(-2), air_gap=20, new_tip='never')
    m300.drop_tip()
