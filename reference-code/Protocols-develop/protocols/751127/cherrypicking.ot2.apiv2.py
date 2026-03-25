from opentrons.types import Point, Location

metadata = {
    'protocolName': 'Cherrypicking from Coordinates',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [transfer_csv] = get_values(  # noqa: F821
        "transfer_csv")

    tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '3',
                                  '20µl tiprack')]
    pipettes = [ctx.load_instrument('p20_single_gen2', mount,
                                    tip_racks=tiprack20)
                for mount in ['right', 'left']]

    # load labware
    transfer_info = [[val.strip().lower() for val in line.split(',')[1:]]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    src_a = Location(Point(
        float(transfer_info[0][0]), float(transfer_info[0][1]),
        float(transfer_info[0][2])), None)
    src_b = Location(Point(
        float(transfer_info[1][0]), float(transfer_info[1][1]),
        float(transfer_info[1][2])), None)
    if False:

        for line in transfer_info[2:]:
            dest = Location(
                Point(float(line[0]), float(line[1]), float(line[2])), None)
            vol = float(line[3])
            [p.pick_up_tip() for p in pipettes]
            [pip.home() for pip in pipettes]
            for src, p in zip([src_a, src_b], pipettes):
                p.aspirate(vol, src)
                p.home()
                p.dispense(vol, dest)
                p.home()
            [p.drop_tip() for p in pipettes]
