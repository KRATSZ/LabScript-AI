metadata = {
    'protocolName': 'DNA Normalization with Custom Labware',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def transpose_matrix(m):
    return [[r[i] for r in reversed(m)] for i in range(len(m[0]))]


def flatten_matrix(m):
    return [cell for row in m for cell in row]


def well_csv_to_list(csv_string):
    """
    Takes a csv string and flattens it to a list, re-ordering to match
    Opentrons well order convention (A1, B1, C1, ..., A2, B2, B2, ...)
    """
    data = [
        line.split(',')
        for line in reversed(csv_string.split('\n')) if line.strip()
        if line
    ]
    if len(data[0]) > len(data):
        # row length > column length ==> "landscape", so transpose
        return flatten_matrix(transpose_matrix(data))
    # "portrait"
    return flatten_matrix(data)


def run(protocol):
    [volumes_csv, p10mnt] = get_values(  # noqa: F821
        'volumes_csv', 'p10mnt')

    # load labware and pipettes

    ax_plate = protocol.load_labware('axygen_96_wellplate', '2')
    res = protocol.load_labware('nest_12_reservoir_15ml', '1')
    tips10 = [protocol.load_labware('opentrons_96_tiprack_10ul', '3')]
    p10 = protocol.load_instrument('p10_single', p10mnt, tip_racks=tips10)

    # create volumes list
    volumes = [float(cell) for cell in well_csv_to_list(volumes_csv)]

    p10.transfer(
        volumes, res['A1'],
        [well.top() for well in ax_plate.wells()[:len(volumes)]])
