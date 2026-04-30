"""Protocol."""
from opentrons.types import Point
from opentrons import protocol_api


metadata = {
    'protocolName': 'Ilumina DNA Prep Part 3 - Clean up Libraries',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):
    """Protocol."""
    [num_samp, plate_A_start_col, plate_B_start_col,
     plate_C_start_col, tip_park_start_col, asp_height,
     length_from_side, m20_mount, m300_mount] = get_values(  # noqa: F821
      "num_samp", "plate_A_start_col", "plate_B_start_col",
      "plate_C_start_col", "tip_park_start_col", "asp_height",
      "length_from_side", "m20_mount", "m300_mount")

    if not 0 <= plate_A_start_col and plate_B_start_col \
            and plate_C_start_col and tip_park_start_col <= 12:
        raise Exception("Enter a start column between 1-12")

    num_samp = int(num_samp)
    num_col = int(num_samp/8)
    plate_A_start_col = int(plate_A_start_col) - 1
    plate_B_start_col = int(plate_B_start_col) - 1
    plate_C_start_col = int(plate_C_start_col) - 1
    tip_park_start_col = int(tip_park_start_col) - 1

    # load labware
    mag_module = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_module.load_labware('biorad_96_wellplate_200ul_pcr')
    plate_a = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '2')
    plate_b = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '3')
    plate_c = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '4')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5')
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['6']]
    tiprack = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['7', '8', '9', '10']]
    park_rack = ctx.load_labware('opentrons_96_filtertiprack_200ul', '11')

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tiprack20)

    switch = True
    drop_count = 0
    drop_threshold = 120

    def _drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        if pip.type == 'multi':
            drop_count += 8
        else:
            drop_count += 1
        if drop_count >= drop_threshold:
            m300.home()
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()  # home before continuing with protocol
            drop_count = 0

    def pick_up300():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all 200ul tip racks")
            m300.reset_tipracks()
            m300.pick_up_tip()

    def remove_supernatant(vol, index, loc, trash=False, pip=m300):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            pip.dispense(vol, waste)
            pip.blow_out(waste.top())

    def mix_at_beads(vol, index, loc):
        side = 1 if index % 2 == 0 else -1
        aspirate_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        dispense_loc = loc.bottom(z=asp_height+4).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        for _ in range(12):
            m300.aspirate(vol, aspirate_loc)
            m300.dispense(vol, dispense_loc)
        m300.blow_out(loc.top())

    # reagents
    rsb_buffer = reservoir.wells()[3]
    ethanol = reservoir.wells()[4:7]
    diluted_magbeads = reservoir.wells()[7]
    waste = reservoir.wells()[11]

    # engage, incubate, remove supernatant, user replaces
    # plate with plate b
    mag_module.engage()
    ctx.delay(minutes=5)
    for i, (s_col, d_col) in enumerate(zip(mag_plate.rows()[0][:num_col],
                                       plate_a.rows()[0][plate_A_start_col:
                                                         plate_A_start_col
                                                         + num_col]
                                           )):
        pick_up300()
        remove_supernatant(22.5, i, s_col)
        m300.dispense(22.5, d_col)
        m300.blow_out(d_col.top())
        _drop(m300)
    mag_module.disengage()
    ctx.pause('''Remove plate on magnetic module and replace with newly
    populated Plate A. Ensure Plate B is on the deck populated with magnetic
    beads. If needed, empty trash.''')

    # pre-mix diluted beads, add to plate A
    pick_up300()
    m300.mix(20, 200, diluted_magbeads)
    _drop(m300)

    for col in plate_a.rows()[0][plate_A_start_col:plate_A_start_col+num_col]:
        pick_up300()
        m300.aspirate(42.5, diluted_magbeads)
        m300.dispense(42.5, col)
        m300.mix(10, 50, col)
        m300.blow_out(col.top())
        _drop(m300)

    # incubate, engage, remove supernatant to plate B
    ctx.delay(minutes=5)
    mag_module.engage()
    ctx.delay(minutes=5)
    for i, (s_col, d_col) in enumerate(zip(
                                mag_plate.rows()[0][plate_A_start_col:
                                                    plate_A_start_col
                                                    + num_col],
                                       plate_b.rows()[0][plate_B_start_col:
                                                         plate_B_start_col
                                                         + num_col]
                                       )):
        pick_up300()
        remove_supernatant(62.5, i, s_col)
        m300.dispense(62.5, d_col)
        m300.mix(10, 55, d_col)
        m300.blow_out(d_col.top())
        _drop(m300)
    ctx.delay(minutes=5)
    mag_module.disengage()

    ctx.pause('''Remove Plate A on magnetic module and replace with newly
    populated Plate B. If needed, empty trash.''')

    # engage magnet, remove supernatant
    mag_module.engage()
    ctx.delay(minutes=5)
    for i, s_col in enumerate(
                                mag_plate.rows()[0][plate_B_start_col:
                                                    plate_B_start_col
                                                    + num_col]):
        pick_up300()
        remove_supernatant(65, i, s_col, trash=True)
        _drop(m300)
    ctx.delay(minutes=5)

    # two ethanol washes
    for wash in range(2):
        pick_up300()
        for eth, sample in zip(ethanol*num_col,
                               mag_plate.rows()[0][
                                                    plate_B_start_col:
                                                    plate_B_start_col
                                                    + num_col
                                                    ]):
            m300.aspirate(200, eth)
            m300.dispense(200, sample.top())
            ctx.delay(seconds=1.5)
            m300.blow_out(sample.top())
        _drop(m300)
        ctx.delay(seconds=30)
        for i, sample in enumerate(mag_plate.rows()[0][
                                                         plate_B_start_col:
                                                         plate_B_start_col
                                                         + num_col
                                                         ]):
            m300.pick_up_tip(park_rack.rows()[0][i+tip_park_start_col])
            remove_supernatant(200, i, sample, trash=True)
            if wash == 0:
                m300.return_tip()
            else:
                _drop(m300)

    # remove excess with p20
    for i, sample in enumerate(mag_plate.rows()[0][
                                                     plate_B_start_col:
                                                     plate_B_start_col
                                                     + num_col
                                                     ]):
        m20.pick_up_tip()
        remove_supernatant(20, i, sample, trash=True, pip=m20)
        _drop(m20)

    # delay, add rsb
    ctx.delay(minutes=5)
    ctx.pause('''Prepare plate for addition of RSB. Empty trash if needed''')

    pick_up300()
    for sample in mag_plate.rows()[0][plate_B_start_col:plate_B_start_col
                                      + num_col]:
        m300.aspirate(32, rsb_buffer)
        m300.dispense(200, sample.top())
        m300.blow_out(sample.top())
    _drop(m300)

    # resuspend beads
    for i, sample in enumerate(mag_plate.rows()[0][
                                                     plate_B_start_col:
                                                     plate_B_start_col
                                                     + num_col
                                                     ]):
        pick_up300()
        mix_at_beads(25, i, sample)
        _drop(m300)

    ctx.delay(minutes=2)
    mag_module.engage()
    ctx.delay(minutes=3)

    # transfer elute to plate_c
    for i, (s_col, d_col) in enumerate(zip(
                                mag_plate.rows()[0][plate_B_start_col:
                                                    plate_B_start_col
                                                    + num_col],
                                       plate_c.rows()[0][plate_C_start_col:
                                                         plate_C_start_col
                                                         + num_col]
                                       )):
        pick_up300()
        remove_supernatant(30, i, s_col)
        m300.dispense(30, d_col)
        m300.blow_out(d_col.top())
        _drop(m300)
