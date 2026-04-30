metadata = {
    'protocolName': '96-well to 384-well transfer',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.4'
}


def run(protocol):
    [plate_cols, pip_mount] = get_values(  # noqa: F821
        'plate_cols', 'pip_mount')

    # load labware and pipettes
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '2')]

    m300 = protocol.load_instrument(
        'p300_multi', pip_mount, tip_racks=tips300)

    tempdeck = protocol.load_module('tempdeck', '4')

    tempplate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul')

    destplate = protocol.load_labware('greinerbioone_384_wellplate_100ul', '1')

    tempdeck.set_temperature(4)

    # transfer 30ul from source column to 3 corresponding columns

    src_cols = tempplate.rows()[0][:8]

    dest_cols = []
    for i in range(8):
        num1 = i*3+1
        num2 = i*3+4
        x = [destplate[plate_cols+str(i)] for i in range(num1, num2)]
        dest_cols.append(x)

    for src, dest in zip(src_cols, dest_cols):
        m300.pick_up_tip()
        m300.aspirate(90, src)
        for d in dest:
            m300.dispense(30, d)
        m300.drop_tip()
