metadata = {
    'protocolName': 'Transfer Small Molecules - CSV Input [4/7]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [pip, mnt20, mnt300, transferCSV] = get_values(  # noqa: F821
     'pip', 'mnt20', 'mnt300', 'transferCSV')

    # Load Labware
    tips = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', s) for s in [4, 5, 7, 8, 10, 11]
            ]

    p20 = protocol.load_instrument(pip, mnt20, tip_racks=tips)

    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '3')]
    m300 = protocol.load_instrument(
        'p300_multi_gen2', mnt300, tip_racks=tips300)

    srcPlate = protocol.load_labware('thermofast_96_wellplate_200ul', '1')
    destPlate = protocol.load_labware('spl_96_wellplate_200ul_flat', '2')

    # Parse CSV; Each line should be --> Src Well, Vol, Dest Well
    data = [r.split(',') for r in transferCSV.strip().splitlines() if r][1:]

    # Make transfers based on CSV and create dest columns to mix
    destSet = set()
    for line in data:
        src, vol, dest = line
        p20.transfer(
            float(vol), srcPlate[src], destPlate[dest],
            mix_before=(3, 15))
        destSet.add(int(dest[1:]))

    destList = sorted(destSet)
    destList = [x-1 for x in destList]

    # mix cells in wells
    for i, col in enumerate(destList):
        dest = destPlate.rows()[0][col]
        m300.pick_up_tip()
        m300.mix(4, 200, dest)
        m300.drop_tip(tips300[0].rows()[0][i-1]) if i != 0 else m300.drop_tip()
