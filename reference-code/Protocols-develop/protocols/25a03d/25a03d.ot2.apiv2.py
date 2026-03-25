from types import MethodType
metadata = {
    'protocolName': 'qPCR Prep in Triplicates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, final_plate_slot4, control_plate,
        asp_rate_global20, disp_rate_global20,
        asp_rate_global300, disp_rate_global300,
     p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "final_plate_slot4",
        "control_plate", "asp_rate_global20", "disp_rate_global20",
        "asp_rate_global300", "disp_rate_global300",
        "p20_mount", "p300_mount")

    num_samp = int(num_samp)

    # load labware
    final_plate = ctx.load_labware(final_plate_slot4, '4')
    mastermix_rack = ctx.load_labware(
                    'usalowbind_24_aluminumblock_2000ul', '1')
    dna_samples = ctx.load_labware(
                  'usastrips_96_aluminumblock_200ul', '7')
    control_plate = ctx.load_labware(control_plate, '9')

    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '11')]

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount,
                              tip_racks=tiprack20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tiprack200)

    m20.flow_rate.aspirate = asp_rate_global20*m20.flow_rate.aspirate
    m20.flow_rate.dispense = disp_rate_global20*m20.flow_rate.dispense
    p300.flow_rate.aspirate = asp_rate_global300*p300.flow_rate.aspirate
    p300.flow_rate.dispense = disp_rate_global300*p300.flow_rate.dispense

    def slow_tip_withdrawal(
     self, speed_limit, well_location):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        previous_limit = None
        if axis in ctx.max_speeds.keys():
            for key, value in ctx.max_speeds.items():
                if key == axis:
                    previous_limit = value
        ctx.max_speeds[axis] = speed_limit
        self.move_to(well_location.top())
        ctx.max_speeds[axis] = previous_limit

    # bind additional methods to pipettes
    for pipette_object in [m20, p300]:
        for method in [slow_tip_withdrawal]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # PROTOCOL
    num_cols = int(num_samp/8)
    final_wells = final_plate.rows()[0][::3]
    final_wells_single_chan = [well for col in final_plate.columns()[::3]
                               for well in col]

    # distribute mastermix
    ctx.comment('Distributing mastermix to sample wells')
    mastermix = mastermix_rack.wells()[0]
    p300.pick_up_tip()
    for i, well in enumerate(final_wells_single_chan[:num_samp]):
        if i % 8 == 0 and i > 0:
            p300.drop_tip()
            p300.pick_up_tip()
        p300.aspirate(48, mastermix, rate=0.75)
        ctx.delay(4)
        p300.dispense(24, mastermix, rate=0.75)
        p300.aspirate(24, mastermix, rate=0.75)
        ctx.delay(4)
        p300.slow_tip_withdrawal(10, mastermix)
        p300.touch_tip()
        p300.dispense(48, well.bottom(z=2), rate=0.6)
        ctx.delay(4)
        p300.blow_out(well.bottom(z=8))
    p300.drop_tip()
    ctx.comment('\n\n\n')

    # distribute mastermix to control
    p300.pick_up_tip()
    ctx.comment('Distributing mastermix to control')
    for well in final_wells_single_chan[24:]:
        p300.aspirate(48, mastermix, rate=0.75)
        ctx.delay(4)
        p300.dispense(24, mastermix, rate=0.75)
        p300.aspirate(24, mastermix, rate=0.75)
        ctx.delay(4)
        p300.slow_tip_withdrawal(10, mastermix)
        p300.touch_tip()
        p300.dispense(48, well.bottom(z=2), rate=0.6)
        ctx.delay(4)
        p300.blow_out(well.bottom(z=8))
    p300.drop_tip()
    ctx.comment('\n\n\n')

    # distribute sample to mastermix
    airgap = 3
    ctx.comment('Distributing sample to mastermix')
    for s_col, d_col in zip(dna_samples.rows()[0][:num_cols], final_wells):
        m20.pick_up_tip()
        m20.mix(3, 15, s_col, rate=0.6)
        m20.aspirate(12, s_col)
        m20.touch_tip()
        m20.air_gap(airgap)
        m20.dispense(airgap, d_col.top())
        m20.dispense(12, d_col.bottom(z=2))
        m20.blow_out(d_col.bottom(z=8))
        m20.touch_tip()
        m20.drop_tip()
    ctx.comment('\n\n\n')

    # add control
    ctx.comment('Adding control to mastermix')
    control = control_plate.rows()[0][-1]
    m20.pick_up_tip()
    m20.mix(3, 15, control, rate=0.6)
    m20.aspirate(12, control)
    m20.touch_tip()
    m20.air_gap(airgap)
    m20.dispense(airgap, final_wells[3].top())
    m20.dispense(12, final_wells[3].bottom(z=2))
    m20.blow_out(final_wells[3].bottom(z=8))
    m20.touch_tip()
    m20.drop_tip()
    ctx.comment('\n\n\n')

    ctx.comment('Moving sample to next well')
    for i, column in enumerate(final_wells[:num_cols]):
        m20.pick_up_tip()
        for _ in range(20):
            m20.aspirate(18, column.bottom(z=2))
            m20.dispense(18, column.bottom(z=8), rate=1.5)
        ctx.delay(4)
        m20.blow_out(column.bottom(z=8))

        m20.aspirate(20, column.bottom(z=2))
        m20.touch_tip()
        m20.dispense(20, final_plate.rows()[0][i*3+1].bottom(z=2))
        ctx.delay(4)
        m20.blow_out(final_plate.rows()[0][i*3+1].bottom(z=8))
        m20.touch_tip()

        m20.aspirate(20, column.bottom(z=2))
        m20.touch_tip()
        m20.dispense(20, final_plate.rows()[0][i*3+2].bottom(z=2))
        ctx.delay(4)
        m20.blow_out(final_plate.rows()[0][i*3+2].bottom(z=8))
        m20.touch_tip()

        m20.drop_tip()

    ctx.comment('Moving control to next well')
    m20.pick_up_tip()
    for _ in range(20):
        m20.aspirate(18, final_wells[3].bottom(z=2))
        m20.dispense(18, final_wells[3].bottom(z=8), rate=1.5)
    ctx.delay(4)
    m20.blow_out(final_wells[3].bottom(z=8))

    m20.aspirate(20, final_wells[3].bottom(z=2))
    m20.touch_tip()
    m20.dispense(20, final_plate.rows()[0][10].bottom(z=2))
    ctx.delay(4)
    m20.blow_out(final_plate.rows()[0][10].bottom(z=8))
    m20.touch_tip()

    m20.aspirate(20, final_wells[3].bottom(z=2))
    m20.touch_tip()
    m20.dispense(20, final_plate.rows()[0][11].bottom(z=2))
    ctx.delay(4)
    m20.blow_out(final_plate.rows()[0][11].bottom(z=8))
    m20.touch_tip()
    m20.drop_tip()
