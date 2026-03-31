import math
from opentrons.types import Point


metadata = {
    'protocolName': 'Agriseq Library Prep Part 3 - Barcoding',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(protocol):
    [num_samp, m20_mount,
     overage_percent, tip_disp, skip_code] = get_values(  # noqa: F821
        "num_samp", "m20_mount", "overage_percent", "tip_disp", "skip_code")

    if not 1 <= num_samp <= 384:
        raise Exception("Enter a sample number between 1-384")

    num_col = math.ceil(num_samp/8)
    num_plates = math.ceil(num_col/12)

    tip_counter = 0
    dropped_tip = 0

    # load labware
    barcode_plate = [protocol.load_labware('customendura_96_wellplate_200ul',
                                           str(slot),
                                           label=f'Ion Barcode Plate {slot}')
                     for slot in [1, 2, 3, 4][:num_plates]]
    reaction_plate = protocol.load_labware('microamp_384_wellplate_100ul',
                                           '5', label='Reaction Plate')
    mmx_plate = protocol.load_labware('customendura_96_wellplate_200ul', '6',
                                      label='MMX Plate')
    tiprack20 = [protocol.load_labware('opentrons_96_filtertiprack_20ul',
                 str(slot))
                 for slot in [7, 8, 9, 10]]

    # load instruments
    m20 = protocol.load_instrument('p20_multi_gen2', m20_mount,
                                   tip_racks=tiprack20)

    tips = [col for tipbox in tiprack20 for col in tipbox.rows()[0]]

    def pick_up():
        nonlocal tip_counter
        nonlocal dropped_tip
        if tip_counter == 48:
            protocol.home()
            for _ in range(10):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                protocol.delay(seconds=0.2)
            protocol.pause('Replace 20 ul tip racks')
            m20.reset_tipracks()
            tip_counter = 0
            dropped_tip = 0
            pick_up()
        else:
            m20.pick_up_tip(tips[tip_counter])
            tip_counter += 1

    def touchtip(pip, well):
        knock_loc = well.top(z=-1).move(
                    Point(x=-(well.diameter/2.25)))
        knock_loc2 = well.top(z=-1).move(
                    Point(x=(well.diameter/2.25)))
        pip.move_to(knock_loc)
        pip.move_to(knock_loc2)

    def trash_tip():
        nonlocal tip_counter
        nonlocal dropped_tip
        if tip_counter < 13:
            m20.drop_tip()
        else:
            m20.drop_tip(tips[dropped_tip])
            dropped_tip += 1

    protocol.comment(
        f'This protocol is for {num_samp} samples. \
        Please prepare reagents accordingly'
    )

    # Height Tracking

    overage_coef = (overage_percent/100)+1

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
    barcode_rxn_mix = mmx_plate['A4']
    barcode_rxn_mix.liq_vol = 3 * num_col * overage_coef

    reaction_plate_cols = [col for j in range(2) for i in range(2)
                           for col in reaction_plate.rows()[i][j::2]][:num_col]
    barcode_plate_cols = [col for plate in barcode_plate
                          for col in plate.rows()[0]]

    # add barcode adapter
    airgap = 3
    if not skip_code:
        for s, d in zip(barcode_plate_cols, reaction_plate_cols):
            pick_up()
            m20.aspirate(1, s)
            touchtip(m20, s)
            m20.air_gap(airgap)
            m20.dispense(airgap, d.top())
            m20.dispense(1, d)
            m20.mix(2, 8, d)
            m20.blow_out()
            touchtip(m20, d)
            m20.return_tip() if tip_disp else trash_tip()

    # add barcode reaction mix
    for col in reaction_plate_cols:
        m20.flow_rate.aspirate = 1.5
        m20.flow_rate.dispense = 1.5
        m20.flow_rate.blow_out = 1.5
        pick_up()
        barcode_rxn_mix.liq_vol -= 3
        ht = liq_height(barcode_rxn_mix)
        m20.aspirate(3, barcode_rxn_mix.bottom(ht))
        m20.move_to(barcode_rxn_mix.top(-2))
        protocol.delay(seconds=2)
        touchtip(m20, barcode_rxn_mix)
        m20.move_to(barcode_rxn_mix.top(-2))
        m20.aspirate(airgap, barcode_rxn_mix.top())
        m20.dispense(airgap, col.top())
        protocol.delay(seconds=2)
        m20.dispense(3, col)
        m20.flow_rate.aspirate = 3
        m20.flow_rate.dispense = 3
        m20.mix(2, 8, col)
        m20.blow_out(col.top(z=-2))
        touchtip(m20, col)
        m20.move_to(col.top(-2))
        m20.return_tip() if tip_disp else trash_tip()

    protocol.comment('''Barcoding sample libraries complete. Store at -20C after
                   centrifuge and PCR steps if needed as a break point''')
