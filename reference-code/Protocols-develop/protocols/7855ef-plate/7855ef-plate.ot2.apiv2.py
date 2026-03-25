"""OPENTRONS."""
import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Agriseq Library Prep Part 1 - DNA transfer (96)',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(protocol):
    """PROTOCOL."""
    [num_samp, m20_mount, overage_percent] = get_values(  # noqa: F821
        "num_samp", "m20_mount", "overage_percent")

    if not 1 <= num_samp <= 288:
        raise Exception("Enter a sample number between 1-288")

    num_col = math.ceil(num_samp/8)
    rxn_plate_num = math.ceil(num_col/12)
    tip_counter = 0

    # load labware
    sample_plates = [protocol.load_labware(
                    'fisherscientific_96_wellplate_200ul',
                     str(slot), label='Sample Plate')
                     for slot in [1, 2, 3][:rxn_plate_num]]
    reaction_plates = [protocol.load_labware('customendura_96_wellplate_200ul',
                                             slot,
                       label='Reaction Plate')
                       for slot in ['4', '5', '6'][:rxn_plate_num]]
    mmx_plate = protocol.load_labware('customendura_96_wellplate_200ul', '7',
                                      label='MMX Plate')
    tiprack20 = [protocol.load_labware('opentrons_96_filtertiprack_20ul',
                                       str(slot))
                 for slot in [8, 9, 10, 11]]

    # load instruments
    m20 = protocol.load_instrument('p20_multi_gen2', m20_mount,
                                   tip_racks=tiprack20)

    tips = [col for tipbox in tiprack20 for col in tipbox.rows()[0]]

    overage_coef = (overage_percent/100)+1
    v_naught = 7*num_col*overage_coef
    # starting height minus 2.5mm, using % isn't enough
    h_naught = (1.92*(v_naught)**(1/3))-2.5
    h = h_naught

    def adjust_height(vol):
        nonlocal v_naught
        nonlocal h
        # below if/else needed to avoid complex number error
        if v_naught - vol > 0:
            v_naught = v_naught - vol
        else:
            v_naught = 0
        h = (1.92*(v_naught)**(1/3))-2.5
        if h < 3:
            h = 1

    def touchtip(pip, well):
        protocol.max_speeds['X'] = 10
        knock_loc = well.top(z=-2).move(
                    Point(x=-(well.diameter/2.5)))
        knock_loc2 = well.top(z=-2).move(
                Point(x=(well.diameter/2.5)))
        pip.move_to(knock_loc)
        pip.move_to(knock_loc2)
        del protocol.max_speeds['X']

    def pick_up():
        nonlocal tip_counter
        if tip_counter == 48:
            protocol.home()
            protocol.pause('Replace 20 ul tip racks on Slots 8, 9, 10, and 11')
            m20.reset_tipracks()
            tip_counter = 0
            pick_up()
        else:
            m20.pick_up_tip(tips[tip_counter])
            tip_counter += 1

    sample_plate_cols = [col for plate in sample_plates
                         for col in plate.rows()[0]][:num_col]
    reaction_plate_cols = [col for plate in reaction_plates
                           for col in plate.rows()[0]][:num_col]

    # load reagents
    amplify_mix = mmx_plate.rows()[0][0]

    # add amplification mix
    airgap = 2
    pick_up()
    for col in reaction_plate_cols:
        m20.flow_rate.aspirate = 1.5
        m20.flow_rate.dispense = 1.5
        m20.flow_rate.blow_out = 1.5
        m20.aspirate(7, amplify_mix.bottom(h))
        m20.move_to(amplify_mix.top(-2))
        protocol.delay(seconds=2)
        m20.touch_tip(v_offset=-2)
        m20.move_to(amplify_mix.top(-2))
        m20.aspirate(airgap, amplify_mix.top())
        m20.dispense(airgap, col.top())
        protocol.delay(seconds=2)
        m20.dispense(7, col)
        m20.blow_out(col.top(z=-2))
        m20.touch_tip(v_offset=-2)
        m20.move_to(col.top(-2))
        adjust_height(7)
    m20.return_tip()

    m20.flow_rate.aspirate = 7.6
    m20.flow_rate.dispense = 7.6
    m20.flow_rate.blow_out = 7.6
    # add DNA
    for s, d in zip(sample_plate_cols, reaction_plate_cols):
        pick_up()
        m20.aspirate(3, s)
        m20.aspirate(airgap, s.top(-1))
        touchtip(m20, s)
        m20.dispense(airgap, d.top())
        m20.dispense(3, d)
        m20.mix(2, 5, d)
        m20.blow_out()
        m20.touch_tip()
        m20.return_tip()

    # for c in protocol.commands():
    #     print(c)
    protocol.home()
    protocol.pause('''Protocol method complete. Please remove reaction plates
                   from deck and proceed with PCR and centrifuge steps.
                   Return reaction plates back to deck and continue to
                   Part 2 - Pre-ligation.''')
