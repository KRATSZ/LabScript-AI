metadata = {
    'protocolName': 'Protein Crystallization',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    tempdeck1 = ctx.load_module('temperature module gen2', '1')
    tempdeck2 = ctx.load_module('temperature module gen2', '4')
    tempdeck1.set_temperature(4)
    tempdeck2.set_temperature(4)

    tubeblock = tempdeck2.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_snapcap')
    crystallization_plate = tempdeck1.load_labware(
        'greinerbioone_192_wellplate_crystallization')
    deepwell_plate = ctx.load_labware('eppendorf_96_wellplate_500ul', '5')
    tiprack_s = [ctx.load_labware('opentrons_96_tiprack_300ul', '3')]
    tiprack_m = [ctx.load_labware('opentrons_96_tiprack_300ul', '6')]

    p300 = ctx.load_instrument(
        'p300_single_gen2', 'right', tip_racks=tiprack_s)
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tiprack_m)

    def slow_descend(pip, loc):
        pip.default_speed /= 16
        pip.move_to(loc)
        pip.default_speed *= 16

    def slow_withdraw(pip, well):
        pip.default_speed /= 16
        ctx.delay(seconds=2.0)
        pip.move_to(well.top(1))
        pip.default_speed *= 16

    small_wells = [
        well for col in crystallization_plate.columns() for well in col[::2]]
    big_wells = [
        well for col in crystallization_plate.columns() for well in col[1::2]]

    # distribute
    p300.pick_up_tip()
    p300.aspirate(210, tubeblock.wells()[0].bottom(2))
    slow_withdraw(p300, tubeblock.wells()[0])
    for well in small_wells:
        p300.move_to(well.top())
        slow_descend(p300, well.bottom(0.2))
        p300.dispense(2, well.bottom(0.2))
        slow_withdraw(p300, well)
    p300.drop_tip()

    for source, well_big, well_small in zip(
            deepwell_plate.rows()[0],
            big_wells,
            small_wells):
        m300.pick_up_tip()
        m300.aspirate(82, source.bottom(2))
        slow_withdraw(m300, source)
        m300.move_to(well_big.top())
        slow_descend(m300, well_big.bottom(1))
        m300.dispense(78, well_big.bottom(1))
        slow_withdraw(m300, well_big)
        m300.move_to(well_small.top())
        slow_descend(m300, well_small.bottom(0.2))
        m300.dispense(2, well_small.bottom(0.2))
        slow_withdraw(m300, well_small)
        m300.drop_tip()
