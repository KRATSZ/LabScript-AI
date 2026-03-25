metadata = {
    'protocolName': 'Aliquoting',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""
    [vol_sirna, mount_p20, mount_p300] = get_values(  # noqa: F821
        'vol_sirna', 'mount_p20', 'mount_p300')

    input_order = """Row,Column,siRNA Sample #
A,1,2
A,2,14
A,3,6
A,4,16
A,5,1
A,6,Empty
A,7,12
A,8,17
A,9,13
A,10,18
A,11,8
A,12,Empty
B,1,16
B,2,17
B,3,19
B,4,6
B,5,15
B,6,Empty
B,7,5
B,8,7
B,9,2
B,10,20
B,11,10
B,12,Empty
C,1,18
C,2,10
C,3,4
C,4,11
C,5,8
C,6,Empty
C,7,7
C,8,5
C,9,14
C,10,9
C,11,15
C,12,Empty
D,1,4
D,2,16
D,3,12
D,4,10
D,5,5
D,6,Empty
D,7,11
D,8,2
D,9,18
D,10,3
D,11,17
D,12,Empty
E,1,1
E,2,20
E,3,7
E,4,13
E,5,14
E,6,Empty
E,7,8
E,8,15
E,9,19
E,10,9
E,11,6
E,12,Empty
F,1,17
F,2,3
F,3,2
F,4,19
F,5,13
F,6,Empty
F,7,16
F,8,20
F,9,6
F,10,1
F,11,12
F,12,Empty
G,1,3
G,2,1
G,3,12
G,4,18
G,5,14
G,6,Empty
G,7,8
G,8,4
G,9,13
G,10,9
G,11,11
G,12,Empty
H,1,20
H,2,15
H,3,19
H,4,4
H,5,11
H,6,Empty
H,7,7
H,8,9
H,9,5
H,10,3
H,11,10
H,12,Empty"""

    # load labware
    source_plate = ctx.load_labware('eppendorftwin.tec_96_wellplate_150ul',
                                    '1', 'source plate')
    dest_plate = ctx.load_labware('eppendorftwin.tec_96_wellplate_150ul',
                                  '2', 'destination plate')

    if vol_sirna > 4:
        tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', '4')]
        pip = ctx.load_instrument('p300_single_gen2', 'right',
                                  tip_racks=tiprack)
    else:
        tiprack = [ctx.load_labware('opentrons_96_tiprack_20ul', '4')]
        pip = ctx.load_instrument('p20_single_gen2', 'right',
                                  tip_racks=tiprack)

    # parse
    map = {}
    for line in input_order.splitlines()[1:]:
        content = line.split(',')
        if not content[2].lower().strip() == 'empty':
            source_ind = int(content[2]) - 1
            source = source_plate.wells()[source_ind]
            dest_name = ''.join(content[0:2])
            dest = dest_plate.wells_by_name()[dest_name]
            if source_ind not in map:
                map[source] = [dest]
            else:
                map[source].append(dest)

    if vol_sirna*4 + pip.min_volume <= pip.max_volume:
        disposal_vol = pip.min_volume
    else:
        disposal_vol = pip.max_volume - vol_sirna*4

    for source, dest_set in map.items():
        pip.distribute(vol_sirna, source, dest_set, disposal_vol=disposal_vol)
