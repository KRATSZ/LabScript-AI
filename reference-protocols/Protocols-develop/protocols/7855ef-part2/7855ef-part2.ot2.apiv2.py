import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Agriseq Library Prep Part 2 - Pre-ligation',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(protocol):
    [num_samp, m20_mount,
     overage_percent, tip_disp] = get_values(  # noqa: F821
        "num_samp", "m20_mount", "overage_percent", "tip_disp")

    if not 1 <= num_samp <= 384:
        raise Exception("Enter a sample number between 1-384")

    num_col = math.ceil(num_samp/8)
    num_tip = math.ceil(num_col/12)

    tip_counter = 0
    dropped_tip = 0

    # load labware
    reaction_plate = protocol.load_labware('microamp_384_wellplate_100ul',
                                           '5', label='Reaction Plate')
    mmx_plate = protocol.load_labware('customendura_96_wellplate_200ul', '6',
                                      label='MMX Plate')
    tiprack20 = [protocol.load_labware('opentrons_96_filtertiprack_20ul',
                 str(slot))
                 for slot in [7, 8, 9, 10][:num_tip]]

    # load instruments
    m20 = protocol.load_instrument('p20_multi_gen2', m20_mount,
                                   tip_racks=tiprack20)

    tips = [col for tipbox in tiprack20 for col in tipbox.rows()[0]]

    def pick_up():
        nonlocal tip_counter
        if tip_counter == 48:
            protocol.home()
            protocol.pause('Replace 20 ul tip racks')
            m20.reset_tipracks()
            tip_counter = 0
            pick_up()

        else:
            m20.pick_up_tip(tips[tip_counter])
            tip_counter += 1

    def trash_tip():
        nonlocal tip_counter
        nonlocal dropped_tip
        if tip_counter < 13:
            m20.drop_tip()
        else:
            m20.drop_tip(tips[dropped_tip])
            dropped_tip += 1

    def touchtip(pip, well):
        knock_loc = well.top(z=-1).move(
                    Point(x=-(well.diameter/2.25)))
        knock_loc2 = well.top(z=-1).move(
                    Point(x=(well.diameter/2.25)))
        pip.move_to(knock_loc)
        pip.move_to(knock_loc2)

    protocol.comment(
        f'This protocol is for {num_samp} samples. \
        Please prepare reagents accordingly'
    )
    # Height Tracking

    overage_coef = (overage_percent/100)+1
    v_naught = 2*num_col*overage_coef
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

    # load reagents
    pre_ligation_mix = mmx_plate.rows()[0][2]
    reaction_plate_cols = [col for j in range(2) for i in range(2)
                           for col in reaction_plate.rows()[i][j::2]][:num_col]

    # add amplification mix
    airgap = 2
    for col in reaction_plate_cols:
        pick_up()
        m20.flow_rate.aspirate = 1.5
        m20.flow_rate.dispense = 1.5
        m20.flow_rate.blow_out = 1.5
        m20.aspirate(2, pre_ligation_mix.bottom(h))
        m20.move_to(pre_ligation_mix.top(-2))
        protocol.delay(seconds=2)
        touchtip(m20, pre_ligation_mix)
        m20.move_to(pre_ligation_mix.top(-2))
        m20.aspirate(airgap, pre_ligation_mix.top(-2))
        m20.dispense(airgap, col.top())
        m20.dispense(2, col)
        m20.flow_rate.aspirate = 3
        m20.flow_rate.dispense = 3
        m20.mix(2, 8, col)
        m20.blow_out(col.top(z=-2))
        touchtip(m20, col)
        m20.move_to(col.top(-2))
        m20.return_tip() if tip_disp else trash_tip()
        adjust_height(2)
        protocol.comment('\n')

    protocol.comment('''Protocol complete - remove reaction plates from
                   deck and prepare Barcode Reaction Mix for Part 3. ''')
