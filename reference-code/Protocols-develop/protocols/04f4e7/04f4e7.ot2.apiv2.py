"""PROTOCOL."""
import math
from opentrons.types import Point
metadata = {
    'protocolName': 'Cell Culture Nucleic Acid Purification',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """PROTOCOL."""

    [num_samp, slow_asp_rate, asp_height_1, asp_height, incubation_time,
     length_from_side, m300_mount] = get_values(  # noqa: F821
        "num_samp", "slow_asp_rate", "asp_height_1", "asp_height",
        "incubation_time", "length_from_side", "m300_mount")

    num_samp = int(num_samp)
    num_col = math.ceil(num_samp/8)

    # load labware
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    magplate = mag_mod.load_labware('biorad_96_wellplate_200ul_pcr')
    res12 = ctx.load_labware('nest_12_reservoir_15ml', '2')
    res = ctx.load_labware('nest_1_reservoir_195ml', '3')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', '6')
    samples = ctx.load_labware('nunc_96_wellplate_2000ul', '4')
    elution_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '5')
    tipracks = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                for slot in ['7', '8', '9', '10', '11']]

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks)

    def use_tiprack_on_slot(slot):
        m300.reset_tipracks()
        m300.starting_tip = tiprack_on_slot[slot].wells()[0]

    def remove_supernatant(vol, index, loc):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height).move(
                        Point(x=(loc.diameter/2-length_from_side)*side))
        m300.aspirate(vol, aspirate_loc)
        m300.dispense(vol, waste.top())
        m300.blow_out(waste.top())

    # protocol
    beads = res12.wells()[0]
    elution_buffer = res12.wells()[1]
    nuet_buffer = res12.wells()[2]
    used_beads = res12.wells()[4]
    waste = waste_res.wells()[0]
    pbs = res.wells()[0]

    tiprack_on_slot = {
                        '7': tipracks[0],
                        '8': tipracks[1],
                        '9': tipracks[2],
                        '10': tipracks[3],
                        '11': tipracks[4]
                        }

    # pre-mix mag beads, use tiprack on slot 8
    ctx.comment('~~~~~~~~~PRE-MIX MAGBEADS~~~~~~~~~~')
    use_tiprack_on_slot('8')
    m300.pick_up_tip()
    m300.mix(5, 300, beads)
    m300.blow_out()
    ctx.comment('\n\n\n')
    ctx.comment('~~~~~~~~~ADD MAGBEADS~~~~~~~~~~')
    for i, col in enumerate(samples.rows()[0][:num_col]):
        if i > 0:
            m300.pick_up_tip()
        m300.aspirate(50, beads)
        m300.dispense(50, col)
        m300.return_tip()
    ctx.comment('\n\n\n')

    # mix and incubate
    ctx.comment('~~~~~~~~~MIX AND INCUBATE 5X~~~~~~~~~~')
    for i in range(5):
        use_tiprack_on_slot('8')
        for col in samples.rows()[0][:num_col]:
            m300.pick_up_tip()
            m300.mix(5, 300, col.bottom(z=5), rate=1.6)
            m300.return_tip()
        ctx.delay(minutes=4 if i < 4 else 10)
        ctx.comment('\n\n\n')

    # slowly pipette out into waste,
    ctx.comment('~~~~~~~~~SLOWLY PIPETTE TOP OFF INTO WASTE~~~~~~~~~~')
    use_tiprack_on_slot('8')
    m300.flow_rate.aspirate = slow_asp_rate*m300.flow_rate.aspirate
    for col in samples.rows()[0][:num_col]:
        m300.pick_up_tip()
        for _ in range(3):
            m300.aspirate(300, col.bottom(z=asp_height_1))
            m300.dispense(300, waste.top())
            m300.blow_out()
        m300.return_tip()
    m300.flow_rate.aspirate = m300.flow_rate.aspirate/slow_asp_rate
    ctx.comment('\n\n\n')

    # mix again and move to mag plate
    ctx.comment('~~~~~~~~~MOVE SAMPLES TO MAGPLATE~~~~~~~~~~')
    use_tiprack_on_slot('8')
    for col, dest in zip(samples.rows()[0][:num_col],
                         magplate.rows()[0]):
        m300.pick_up_tip()
        m300.mix(5, 200, col)
        m300.aspirate(300, col)
        m300.dispense(300, dest)
        m300.blow_out()
        m300.return_tip()
    ctx.comment('\n\n\n')

    # remove supernatant
    ctx.comment('~~~~~~~~~REMOVE SUPERNATANT~~~~~~~~~~')
    mag_mod.engage()
    ctx.delay(minutes=incubation_time)
    use_tiprack_on_slot('8')
    for i, col in enumerate(magplate.rows()[0][:num_col]):
        m300.pick_up_tip()
        remove_supernatant(180, i, col)
        m300.drop_tip()
    mag_mod.disengage()
    ctx.comment('\n\n\n')

    # add pbs and remove supernatant 2x
    ctx.comment('~~~~~~~~~TWO WASHES WITH PBS~~~~~~~~~~')
    for wash in range(2):
        use_tiprack_on_slot('9')

        # add pbs
        ctx.comment(f'~~~~~~~~~ADD PBS WASH {wash+1}~~~~~~~~~~')
        m300.pick_up_tip(tipracks[2].wells_by_name()['A1'])
        for col in magplate.rows()[0][:num_col]:
            m300.aspirate(180, pbs)
            m300.dispense(180, col.top())
        if wash == 0:
            m300.return_tip()
        else:
            m300.drop_tip()

        for col in magplate.rows()[0][:num_col]:
            use_tiprack_on_slot('10')
            m300.pick_up_tip()
            m300.mix(2, 100, col)
            m300.blow_out()
            if wash == 0:
                m300.return_tip()
            else:
                m300.drop_tip()
        mag_mod.engage()
        ctx.delay(minutes=incubation_time)
        ctx.comment('\n\n\n')

        # remove supernatant
        ctx.comment(f'~~~~~~~~~REMOVE SUPERNATANT WASH {wash+1}~~~~~~~~~~')
        for i, col in enumerate(magplate.rows()[0][:num_col]):
            m300.pick_up_tip()
            remove_supernatant(180, i, col)
            if wash == 0:
                m300.return_tip()
            else:
                m300.drop_tip()
        mag_mod.disengage()
    ctx.comment('\n\n\n')

    # add elution buffer
    ctx.comment('~~~~~~~~~ADD ELUTION BUFFER~~~~~~~~~~')
    use_tiprack_on_slot('11')
    for col in magplate.rows()[0][:num_col]:
        m300.pick_up_tip()
        m300.aspirate(100, elution_buffer)
        m300.dispense(100, col)
        m300.mix(2, 50, col)
        m300.blow_out()
        m300.return_tip()
    ctx.comment('\n\n\n')

    # add nuetralization buffer
    ctx.comment('~~~~~~~~~ADD NUETRALIZATION BUFFER~~~~~~~~~~')
    use_tiprack_on_slot('7')
    for col in elution_plate.rows()[0][:num_col]:
        m300.pick_up_tip()
        m300.aspirate(50, nuet_buffer)
        m300.dispense(50, col)
        m300.blow_out()
        m300.drop_tip()
    mag_mod.engage()
    ctx.delay(minutes=incubation_time)
    ctx.comment('\n\n\n')

    # transfer to final elution plate
    ctx.comment('~~~~~~~~~TRANSFER TO FINAL ELUTION PLATE~~~~~~~~~~')
    use_tiprack_on_slot('11')
    for i, (source, dest) in enumerate(zip(magplate.rows()[0][:num_col],
                                           elution_plate.rows()[0])):

        side = -1 if i % 2 == 0 else 1
        aspirate_loc = source.bottom(z=asp_height).move(
                        Point(x=(source.diameter/2-length_from_side)*side))
        m300.pick_up_tip()
        m300.aspirate(100, aspirate_loc)
        m300.dispense(100, dest)
        m300.blow_out()
        m300.drop_tip()
    mag_mod.disengage()
    ctx.comment('\n\n\n')

    # add pbs
    ctx.comment('~~~~~~~~~ADD PBS AND RETRIEVE BEADS~~~~~~~~~~')
    use_tiprack_on_slot('7')
    m300.pick_up_tip()
    for col in magplate.rows()[0][:num_col]:
        m300.aspirate(50, pbs)
        m300.dispense(50, col)
        m300.aspirate(50, col)
        m300.dispense(50, used_beads)
        m300.blow_out()
    m300.drop_tip()
    ctx.comment('\n\n\n')
