# metadata
metadata = {
    'protocolName': 'NGS Prep Part 3/3: Library Pooling',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [input_csv, vol_water, p10_mount, p300_mount] = get_values(  # noqa: F821
        "input_csv", "vol_water", "p10_mount", "p300_mount")

    # load modules and labware
    ctx.load_module('magdeck', '1')
    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '2',
        '2ml reagent rack'
    )
    tiprack10 = [
        ctx.load_labware(
            'opentrons_96_filtertiprack_10ul', '3', '10ul filter tips')]
    tempdeck = ctx.load_module('tempdeck', '4')
    tubeblock = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_snapcap'
    )
    tempdeck.set_temperature(4)
    tiprack200 = [
        ctx.load_labware(
            'opentrons_96_filtertiprack_200ul', '6', '200ul filter tips')]
    elution_plate = ctx.load_labware(
        'eppendorftwin.tec_96_wellplate_150ul', '9', 'elution plate')

    # pipettes
    p10 = ctx.load_instrument(
        'p10_single', mount=p10_mount, tip_racks=tiprack10)
    p300 = ctx.load_instrument(
        'p300_single', mount=p300_mount, tip_racks=tiprack200)

    # reagent setup
    water = tuberack.wells()[0]
    pool = tubeblock.wells()[0]

    # parse
    t_data = [
        [elution_plate.wells_by_name()[
            t.split(',')[0].strip().upper()], float(t.split(',')[1])]
        for t in input_csv.splitlines()[1:]
    ]

    # pre-transfer water
    p300.transfer(vol_water, water, pool.bottom(5), blow_out=True)

    # transer .csv-specified volume of sample to the pooling tube
    for trans in t_data:
        vol, src = [trans[1], trans[0]]
        v_asp = 10 - vol if 10 - vol < 10 else 0
        p10.pick_up_tip()
        p10.aspirate(vol, src)
        p10.touch_tip(src)
        p10.aspirate(v_asp, pool.bottom(2))
        p10.dispense(10, pool.bottom(2))
        p10.blow_out(pool.bottom(5))
        p10.drop_tip()
