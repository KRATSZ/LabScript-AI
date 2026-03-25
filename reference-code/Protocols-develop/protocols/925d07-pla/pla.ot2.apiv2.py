metadata = {
    'protocolName': 'Plasmid Luciferase Assay',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}

V141_PLASMID_DISPENSE_HEIGHT = 0.5  # mm above bottom
LIPOFECTAMINE_2000_DISPENSE_HEIGHT = 0.5  # mm above bottom


def run(ctx):

    # labware
    plate384 = ctx.load_labware('corning_384_wellplate_112ul_flat', '1')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4')
    plate96 = ctx.load_labware('corning_96_wellplate_360ul_flat', '5')
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['7', '8', '9']]

    # pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks20)

    # reagent
    v141_plasmid = reservoir.rows()[0][0]
    lipofectamine_2000 = reservoir.rows()[0][1]
    sirna = plate96.rows()[0]

    quadruplicate_sets = [
        [well for col in plate384.columns()[i*2:(i+1)*2] for well in col[:2]]
        for i in range(12)]

    ctx.comment('\n\n\n\n\nV141 PLASMID TRANSFERS\n\n\n\n\n')

    m20.pick_up_tip()
    for set in quadruplicate_sets:
        m20.aspirate(19, v141_plasmid.bottom(4))
        m20.touch_tip(v141_plasmid, v_offset=18.9-v141_plasmid.depth)
        m20.air_gap(1)
        m20.dispense(1, set[0].top(-1))
        for well in set:
            m20.dispense(4, well.bottom(V141_PLASMID_DISPENSE_HEIGHT))
            # m20.touch_tip(well, v_offset=6.4-well.depth)
        m20.dispense(m20.current_volume, v141_plasmid.bottom(4))
    m20.drop_tip()

    ctx.comment('\n\n\n\n\nSiRNA TRANSFERS\n\n\n\n\n')

    for source, set in zip(sirna, quadruplicate_sets):
        m20.pick_up_tip()
        m20.aspirate(19, source.bottom(1))
        m20.air_gap(1)
        m20.dispense(1, set[0].top(-1))
        for well in set:
            m20.dispense(4, well.bottom(1))
            # m20.touch_tip(well, v_offset=10.43-well.depth)
        m20.drop_tip()

    ctx.comment('\n\n\n\n\nLIPOFECTAMINE 2000 TRANSFERS\n\n\n\n\n')

    for set in quadruplicate_sets:
        m20.pick_up_tip()
        m20.aspirate(19, lipofectamine_2000.bottom(4))
        m20.touch_tip(lipofectamine_2000,
                      v_offset=18.9-lipofectamine_2000.depth)
        m20.air_gap(1)
        m20.dispense(1, set[0].top(-1))
        for well in set:
            m20.dispense(4, well.bottom(LIPOFECTAMINE_2000_DISPENSE_HEIGHT))
            # m20.touch_tip(well, v_offset=10.43-well.depth)
        m20.aspirate(5, set[-1].top())  # air gap on way to trash
        m20.drop_tip()
