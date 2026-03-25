import math
from opentrons.types import Point


metadata = {
    'protocolName': 'Agriseq Library Prep Part 1 - DNA transfer',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(protocol):

    [num_samp, m20_mount, overage_percent] = get_values(  # noqa: F821
        "num_samp", "m20_mount", "overage_percent")

    if not 1 <= num_samp <= 384:
        raise Exception("Enter a sample number between 1-384")

    num_col = math.ceil(num_samp/8)
    num_plate = math.ceil(num_col/12)
    num_tip = math.ceil((num_col+1)/12)

    tip_counter = 0
    dropped_tip = 0

    # load labware
    sample_plates = [
        protocol.load_labware(
            'fisherscientific_96_wellplate_200ul',
            str(slot),
            label=f'Sample Plate {slot}') for slot in [1, 2, 3, 4][:num_plate]]
    reaction_plate = protocol.load_labware(
                    'microamp_384_wellplate_100ul', '5',
                    label='Reaction Plate')
    mmx_plate = protocol.load_labware('customendura_96_wellplate_200ul', '6',
                                      label='MMX Plate')
    tiprack20 = [
        protocol.load_labware(
            'opentrons_96_filtertiprack_20ul',
            str(slot)) for slot in [7, 8, 9, 10, 11][:num_tip]]

    # load instruments
    m20 = protocol.load_instrument('p20_multi_gen2', m20_mount,
                                   tip_racks=tiprack20)

    tips = [col for tipbox in tiprack20 for col in tipbox.rows()[0]]

    # return liquid height in a well
    def liq_height(well):
        r1 = well.diameter / 2
        r2 = 0.6  # calculated manually
        h = (3 * well.liq_vol)/(math.pi*((r1**2) + (r1*r2) + (r2**2)))
        if h > 10:
            return 10
        elif h < 3:
            return 0.5
        else:
            return h

    # load reagents
    overage_coef = (overage_percent/100)+1

    n1 = num_col if num_samp <= 192 else 24
    v1 = 7*n1*overage_coef
    amplify_mix_1 = mmx_plate['A1']
    amplify_mix_1.liq_vol = v1

    n2 = num_col - 24 if num_samp > 192 else 0
    v2 = 7*n2*overage_coef
    amplify_mix_2 = mmx_plate['A2']
    amplify_mix_2.liq_vol = v2

    def touchtip(pip, well):
        knock_loc = well.top(z=-2).move(
                    Point(x=-(well.diameter/2.5)))
        knock_loc2 = well.top(z=-2).move(
                Point(x=(well.diameter/2.5)))
        pip.move_to(knock_loc)
        pip.move_to(knock_loc2)

    def pick_up():
        nonlocal tip_counter
        if tip_counter == 60:
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

    sample_plate_cols = [col for plate in sample_plates
                         for col in plate.rows()[0]][:num_col]
    reaction_plate_cols = [col for j in range(2) for i in range(2)
                           for col in reaction_plate.rows()[i][j::2]][:num_col]
    protocol.comment(
        f'This protocol is for {num_samp} samples. \
        Please prepare reagents accordingly'
    )
    # add amplification mix
    airgap = 2
    num = 0
    m20.flow_rate.aspirate = 1.5
    m20.flow_rate.dispense = 1.5
    m20.flow_rate.blow_out = 1.5
    pick_up()
    for col in reaction_plate_cols:
        if num >= 192:
            amplify_mix_well = amplify_mix_2
        else:
            amplify_mix_well = amplify_mix_1
        amplify_mix_well.liq_vol -= 7
        ht = liq_height(amplify_mix_well)
        m20.aspirate(7, amplify_mix_well.bottom(ht))
        m20.move_to(amplify_mix_well.top(-2))
        protocol.delay(seconds=2)
        touchtip(m20, amplify_mix_well)
        m20.move_to(amplify_mix_well.top(-2))
        m20.aspirate(airgap, amplify_mix_well.top())
        m20.dispense(airgap, col.top())
        protocol.delay(seconds=2)
        m20.dispense(7, col)
        m20.blow_out(col.top(z=-2))
        touchtip(m20, col)
        m20.move_to(col.top(-2))
        num += 8
    trash_tip()
    protocol.comment('\n\n\n\n')

    # add DNA
    m20.flow_rate.aspirate = 7.6
    m20.flow_rate.dispense = 7.6
    m20.flow_rate.blow_out = 7.6
    for s, d in zip(sample_plate_cols, reaction_plate_cols):
        pick_up()
        m20.aspirate(3, s)
        m20.aspirate(airgap, s.top(-1))
        touchtip(m20, s)
        m20.dispense(airgap, d.top())
        m20.dispense(3, d)
        m20.mix(2, 5, d)
        m20.blow_out()
        touchtip(m20, d)
        trash_tip()

    protocol.home()
    protocol.comment('''Protocol method complete. Please remove reaction plates
                   from deck and proceed with PCR and centrifuge steps.
                   Return reaction plates back to deck and continue to
                   Part 2 - Pre-ligation.''')
