from opentrons.types import Mount

metadata = {
    'protocolName': 'Lipid Quantification',
    'author': 'Nick <ndiehl@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_sample_columns, mount_m20, mount_m300] = get_values(  # noqa: F821
        'num_sample_columns', 'mount_m20', 'mount_m300')

    # labware
    plate = ctx.load_labware('abgene_96_wellplate_2200ul', '4')
    tubeblock = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap', '5')
    reservoir = ctx.load_labware(
        'eppendorf_7_reservoir_30000ul', '11',
        'triton (channel 1) and triglyceride (channel 1)')
    tipracks20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '8')]
    tipracks300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '3')]
    tiprack20_s = ctx.load_labware('opentrons_96_tiprack_20ul', '10')

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', mount_m20,
                              tip_racks=tipracks20)
    m300 = ctx.load_instrument('p300_multi_gen2', mount_m300,
                               tip_racks=tipracks300)

    # reagents
    triton = reservoir.rows()[0][0]
    triglyceride = reservoir.rows()[0][1]
    offset_triglyceride = -41
    standards = tubeblock.wells()[:5]
    standards_dests_sets = [
        row[:3] for row in plate.rows()[1:6]]
    triton_dests = plate.rows()[0][:3+num_sample_columns]
    triglyceride_dests = triton_dests

    def slow_withdraw(pip, well, delay_seconds=2.0):
        pip.default_speed /= 16
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top(5))
        pip.default_speed *= 16

    tips_single = tiprack20_s.wells()
    default_current = 0.6
    mount = Mount.LEFT if m20.mount == 'left' else Mount.RIGHT

    # offset tip pickup
    def pick_up_single():
        ctx._hw_manager.hardware._attached_instruments[
            mount].update_config_item(
                'pick_up_current', default_current/8)
        tip = tips_single.pop()
        m20.pick_up_tip(tip)
        ctx._hw_manager.hardware._attached_instruments[
            mount].update_config_item(
                'pick_up_current', default_current)

    # transfer standards
    vol_standard = 3
    if standards[0].depth > tips_single[0].depth - 5:  # account for overlap
        h_asp = tips_single[0].depth - 5
    else:
        h_asp = standards[0].depth - 5
    if plate.wells()[0].depth > tips_single[0].depth - 5:
        h_disp = tips_single[0].depth - 5
    else:
        h_disp = plate.wells()[0].depth - 5

    for s, dest_set in zip(standards, standards_dests_sets):
        for d in dest_set:
            pick_up_single()
            m20.aspirate(vol_standard, s.top(-1*h_asp))
            slow_withdraw(m20, s)
            m20.dispense(vol_standard, d.top(-1*h_disp))
            m20.drop_tip()

    ctx.pause('Remove silicone mats from pre-plated sample wells.')

    # transfer triton
    vol_triton = 10.0
    for d in triton_dests:
        m20.pick_up_tip()
        m20.move_to(triton.top(5))
        m20.aspirate(vol_triton, triton.bottom(5))
        slow_withdraw(m20, triton)
        m20.dispense(vol_triton, d.top(-1*h_disp))
        slow_withdraw(m20, d)
        m20.drop_tip()

    ctx.pause('Cover plate, shake 2 minutes @ 900 r.p.m., incubate 1 hour \
@ 37C, and 20 minutes @ room temperature.')

    # transfer triglyceride
    vol_triglyceride = 300.0
    for d in triglyceride_dests:
        m300.pick_up_tip()
        m300.move_to(triglyceride.top(5))
        m300.aspirate(
            vol_triglyceride, triglyceride.bottom(5-offset_triglyceride))
        slow_withdraw(m300, triglyceride)
        m300.dispense(vol_triglyceride, d.bottom(5))
        slow_withdraw(m300, d)
        m300.drop_tip()
