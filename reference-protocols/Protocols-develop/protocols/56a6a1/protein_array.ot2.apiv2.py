metadata = {
    'protocolName': 'Protein Array',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [number_of_slides_to_process, sample_addition,
        p300_mount] = get_values(  # noqa: F821
            'number_of_slides_to_process', 'sample_addition', 'p300_mount')

    # checks
    if number_of_slides_to_process > 4 or number_of_slides_to_process < 1:
        raise Exception('Invalid number of slides to process. Please input a \
number between 1 and 4.')

    # load modules and labware
    res_12 = ctx.load_labware(
        'usascientific_12_reservoir_22ml', '3', 'reagent reservoir')
    shake_plate = ctx.load_labware(
        'teleshake1536_64_slides_100ul', '4', 'Teleshake with slides mounted')
    liquid_trash = ctx.load_labware(
        'agilent_1_reservoir_290ml', '6', 'liquid trash').wells()[0].top()
    tip_trash = ctx.loaded_labwares[12].wells()[0]

    # reagents
    super_g_blocking_buffer = res_12.wells()[0]
    antibody_2 = res_12.wells()[1]
    pbst = res_12.wells()[2:6]

    # pipettes
    if (
        number_of_slides_to_process > 2
        and sample_addition == 'automatically add samples from PCR plate'
    ):
        tip_slots = ['7', '8', '9']
    else:
        tip_slots = ['7', '8']
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in tip_slots]
    m300 = ctx.load_instrument(
        'p300_multi', mount=p300_mount, tip_racks=tips300)

    # setup slide wells
    aspirate_locs = [
        well.top()
        for well in shake_plate.rows()[0][:number_of_slides_to_process*2]
    ]
    dispense_locs = [
        well.top(4)
        for well in shake_plate.rows()[0][:number_of_slides_to_process*2]
    ]

    def vacuum():
        m300.flow_rate.aspirate = 300
        if not m300.hw_pipette['has_tip']:
            m300.pick_up_tip()
        for i in range(len(aspirate_locs)//2):
            set_a = aspirate_locs[i*2:i*2+2]
            set_d = dispense_locs[i*2:i*2+2]
            m300.aspirate(150, set_a[0])
            m300.move_to(set_d[0])
            m300.move_to(set_d[1])
            m300.aspirate(150, set_a[1])
            m300.dispense(300, liquid_trash)
            m300.blow_out(liquid_trash)
        m300.drop_tip(tip_trash)
        m300.flow_rate.aspirate = 150

    # distribute blocking buffer
    m300.distribute(
        100, super_g_blocking_buffer, dispense_locs, disposal_vol=0)
    m300.move_to(res_12.wells()[-1].top(10))

    ctx.pause("Shake for 30 minutes at room temperature on TeleShake before \
resuming.")

    # completely transfer out buffer (replacement for vacuum system)
    vacuum()

    # PBST washes
    for wash in range(2):
        m300.pick_up_tip()
        m300.distribute(
            100, pbst[0], dispense_locs, disposal_vol=0, new_tip='never')
        m300.move_to(res_12.wells()[-1].top(10))
        ctx.comment('Incubating 5 minutes.')
        ctx.delay(minutes=5)
        vacuum()

    if sample_addition == 'manually add samples':
        pause_str = 'Manually add samples to slides. Incubate the samples by \
gentle agitation for 1 hour using TeleShake before resuming.'
    else:
        sample_plate = ctx.load_labware(
            'biorad_96_wellplate_200ul_pcr', '10', 'sample plate')
        samples = sample_plate.rows('A')[:number_of_slides_to_process*2]
        m300.drop_tip(tip_trash.top(10))
        m300.transfer(100, samples, dispense_locs, new_tip='always')
        pause_str = 'Incubate the samples by gentle agitation for 1 hour \
using TeleShake before resuming.'
    m300.move_to(res_12.wells()[-1].top(10))
    ctx.pause(pause_str)

    # completely transfer out liquid
    vacuum()

    # wash sequence
    def wash(
            wash_ind,
            num_initial_pbst,
            final_aspirate,
            sg_source=super_g_blocking_buffer,
            num_final_pbst=1
    ):
        for i in range(num_initial_pbst):
            m300.pick_up_tip()
            m300.distribute(
                100,
                pbst[wash_ind],
                dispense_locs,
                disposal_vol=0,
                new_tip='never'
            )
            m300.move_to(res_12.wells()[-1].top(10))
            ctx.comment('Incubating 5 minutes.')
            ctx.delay(minutes=5)
            vacuum()

        m300.pick_up_tip()
        m300.distribute(
            100,
            sg_source,
            dispense_locs,
            disposal_vol=0,
            new_tip='never'
        )
        m300.move_to(res_12.wells()[-1].top(10))
        ctx.comment('Incubating 5 minutes.')
        ctx.delay(minutes=5)
        vacuum()

        for i in range(num_final_pbst):
            m300.pick_up_tip()
            m300.distribute(
                100,
                pbst[wash_ind],
                dispense_locs,
                disposal_vol=0,
                new_tip='never'
            )
            m300.move_to(res_12.wells()[-1].top(10))
            ctx.comment('Incubating 5 minutes.')
            ctx.delay(minutes=5)
            if final_aspirate:
                vacuum()
            if m300.hw_pipette['has_tip']:
                m300.drop_tip(tip_trash)

    wash(
        wash_ind=1,
        num_initial_pbst=1,
        final_aspirate=True,
        sg_source=res_12.wells_by_name()['A7'],
        num_final_pbst=1
    )

    ctx.pause('Prepare 1:1000 secondary antibody solution (2 ml total volume \
per slide) in PBST and place in channel 2 of the 12-channel reagent reservoir \
(slot 3).')

    m300.pick_up_tip()
    m300.distribute(
        100,
        antibody_2,
        dispense_locs,
        disposal_vol=0,
        new_tip='never'
    )
    m300.move_to(res_12.wells()[-1].top(10))

    ctx.pause('Incubate the samples by gentle agitation for 1 hour using \
TeleShake before resuming.')

    vacuum()

    for i in range(3):
        m300.pick_up_tip()
        m300.distribute(
            100,
            pbst[i//2+2],
            dispense_locs,
            disposal_vol=0,
            new_tip='never'
        )
        m300.move_to(res_12.wells()[-1].top(10))
        ctx.comment('Incubating 5 minutes.')
        ctx.delay(minutes=5)
        if i < 2:
            vacuum()

    m300.move_to(res_12.wells()[-1].top(10))
    ctx.comment('Incubating 5 minutes.')
    ctx.delay(minutes=5)
    m300.drop_tip(tip_trash)

    ctx.comment('Take off slides from FastFrame and place into 50 ml \
conical tube filled with 45 ml PBS, and wash by agitating on TeleShake for 5 \
minutes. Briefly rinse the slides 2 times using a 50 ml conical tube with \
ddH2O. Spin at 300 rpm using Beckman-Coulter Avant J-E Centrifuge at RT for 4 \
minutes. Scan the slides with GenePix 4400 A.')
