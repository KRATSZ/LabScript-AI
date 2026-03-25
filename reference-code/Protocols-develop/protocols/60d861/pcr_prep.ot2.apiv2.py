import math

metadata = {
    'protocolName': 'CYP Induction, Part 1/3: Wash ',
    'author': 'Nick <ndiehl@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    num_samples, m300_mount = get_values(  # noqa: F821
        'num_samples', 'm300_mount')

    wash_rack = ctx.load_labware('opentrons_96_tiprack_300ul', '2')
    solution_rack = ctx.load_labware('opentrons_96_tiprack_300ul', '3')
    plate = ctx.load_labware('thermofishermicroamp_96_wellplate_200ul',
                             '5', 'catcher plate')
    wash_buff = ctx.load_labware('nest_1_reservoir_195ml', '7',
                                 'wash').wells()[0]
    waste = ctx.load_labware(
        'nest_1_reservoir_195ml', '8', 'waste').wells()[0].top()
    elution = ctx.load_labware(
        'nest_1_reservoir_195ml', '9', 'elution').wells()[0]

    num_cols = math.ceil(num_samples/8)
    samples = plate.rows()[0][:num_cols]
    wash_tips = wash_rack.rows()[0][:num_cols]
    wash_buffer_tip = solution_rack.rows()[0][0]
    elution_buffer_tip = solution_rack.rows()[0][1]

    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[solution_rack])

    def remove_supernatant():
        # discard initial volume
        for s, tip in zip(samples, wash_tips):
            m300.pick_up_tip(tip)
            m300.transfer(100, s, waste, air_gap=20, new_tip='never')
            m300.drop_tip(tip)

    def wash():
        # transfer 100ul (reverse pipetting)
        m300.pick_up_tip(wash_buffer_tip)
        m300.aspirate(20, wash_buff)
        for s in samples:
            m300.aspirate(100, wash_buff)
            m300.dispense(100, s.top())
        m300.dispense(20, wash_buff.top())
        m300.drop_tip(wash_buffer_tip)

        # incubate
        ctx.delay(minutes=1, msg='Incubating the plate for 1 minute at room \
    temperature')

        remove_supernatant()

    remove_supernatant()
    for _ in range(3):
        wash()

    ctx.pause('Manually completely aspirate any remaining Wash Buffer.')

    # elute
    m300.pick_up_tip(elution_buffer_tip)
    m300.aspirate(20, elution)
    for s in samples:
        m300.aspirate(80, elution)
        m300.dispense(80, s.top())
    m300.drop_tip()
