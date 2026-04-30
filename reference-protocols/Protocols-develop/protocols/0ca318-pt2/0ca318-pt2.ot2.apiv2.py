import math
from opentrons import protocol_api

metadata = {
    'protocolName': 'Magnetic Bead Purification + PCR',
    'author': 'Rami <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, mag_height, p300_mount, m300_mount] = get_values(  # noqa: F821
        "num_samp", "mag_height", "p300_mount", "m300_mount")

    # load modules
    pcr_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 4)  # noqa: E501
    mag_mod = ctx.load_module('magnetic module gen2', 1)
    mag_mod.disengage()
    mag_plate = mag_mod.load_labware('thermo_96_wellplate_800ul')

    # load labware
    reag_plate = ctx.load_labware('thermo_96_wellplate_800ul', 5)
    final_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 3)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 2)

    tips_single = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                   for slot in [6]]

    tips_multi = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in [7, 8, 9]]

    # load pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips_single)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips_multi)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(f"Replace empty tip rack for {pip}")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # mapping
    num_full_cols = num_samp // 8
    remainder_wells = num_samp % 8
    last_col_pcr = pcr_plate.columns()[num_full_cols][:remainder_wells]
    last_col_mag = mag_plate.columns()[num_full_cols][:remainder_wells]
    last_col_final_plate = mag_plate.columns()[num_full_cols]
    leftover = False if num_samp / 8 == 0 else True

    beads = reag_plate.rows()[0][0]
    tris = reag_plate.rows()[0][1]
    num_ethanol_wells = math.ceil(num_samp/24)
    ethanol = reservoir.wells()[:num_ethanol_wells]*24
    trash = reservoir.wells()[8:]*24

    ctx.comment('\n\n--------Transferring Sample to Mag Plate----------\n')
    for s, d in zip(pcr_plate.rows()[0][:num_full_cols], mag_plate.rows()[0]):
        pick_up(m300)
        m300.aspirate(25, s)
        m300.dispense(25, d)
        m300.drop_tip()

    # leftover
    if leftover:
        for s, d in zip(last_col_pcr, last_col_mag):
            pick_up(p300)
            p300.aspirate(25, s)
            p300.dispense(25, d)
            p300.drop_tip()

    ctx.comment('\n\n--------Transferring Beads to Mag Plate----------\n')
    for i, d in enumerate(mag_plate.rows()[0][:num_full_cols]):
        pick_up(m300)
        m300.mix(15 if i == 0 else 3, 200, beads, rate=0.8)
        m300.aspirate(20, beads, rate=0.75)
        m300.dispense(20, d, rate=0.75)
        m300.mix(10, 45, d)
        m300.blow_out()
        m300.drop_tip()
        ctx.comment('\n')

    # leftover
    if leftover:
        for d in last_col_mag:
            pick_up(p300)
            p300.mix(15 if i == 0 else 3, 200, beads, rate=0.8)
            p300.aspirate(20, beads, rate=0.75)
            p300.dispense(20, d, rate=0.75)
            p300.mix(10, 45, d)
            p300.blow_out()
            p300.drop_tip()
            ctx.comment('\n')

    ctx.delay(minutes=5)

    mag_mod.engage(height_from_base=mag_height)

    ctx.comment('\n\n-------------REMOVE SUPER-------------\n')
    for col in mag_plate.rows()[0][:num_full_cols]:
        pick_up(m300)
        m300.aspirate(50, col, rate=0.15)
        m300.aspirate(10, col.bottom(z=0.5), rate=0.05)
        m300.dispense(50, trash[0])
        m300.drop_tip()

    if leftover:
        for well in last_col_mag:
            pick_up(p300)
            p300.aspirate(50, well, rate=0.15)
            p300.aspirate(10, well.bottom(z=0.5), rate=0.05)
            p300.dispense(60, trash[1])
            p300.drop_tip()

    ctx.comment('\n\n-------------TWO WASHES-------------\n')
    eth_ctr = 0

    for _ in range(2):

        pick_up(m300)
        for col in mag_plate.rows()[0][:num_full_cols]:
            m300.aspirate(200, ethanol[eth_ctr])
            m300.dispense(200, col.top())
            eth_ctr += 1
        m300.drop_tip()

        if leftover:
            pick_up(m300)
            for well in last_col_mag:
                m300.aspirate(200, ethanol[eth_ctr])
                m300.dispense(200, col.top())
            m300.drop_tip()

        mag_mod.engage(height_from_base=mag_height)
        ctx.delay(seconds=60)

        ctx.comment('\n\n-------------REMOVE SUPER-------------\n')
        for col, trash_well in zip(mag_plate.rows()[0][:num_full_cols], trash):
            pick_up(m300)
            m300.aspirate(200, col, rate=0.15)
            m300.dispense(200, trash_well)
            m300.aspirate(20, col.bottom(z=0.4), rate=0.05)
            m300.dispense(20, trash_well)
            m300.drop_tip()

        if leftover:
            for well in last_col_mag:
                pick_up(p300)
                p300.aspirate(200, well, rate=0.15)
                p300.dispense(200, trash[2])
                p300.aspirate(20, well.bottom(z=0.4), rate=0.05)
                p300.dispense(20, trash[3])
                p300.drop_tip()

    ctx.delay(minutes=10)
    mag_mod.disengage()

    ctx.comment('\n\n--------Transferring Tris to Mag Plate----------\n')
    for i, d in enumerate(mag_plate.rows()[0][:num_full_cols]):
        pick_up(m300)
        m300.aspirate(52.5, tris)
        m300.dispense(52.5, d)
        m300.mix(10, 52.5, d)
        m300.blow_out()
        m300.drop_tip()
        ctx.comment('\n')

    # leftover
    if leftover:
        for d in last_col_mag:
            pick_up(p300)
            p300.aspirate(52.5, tris)
            p300.dispense(52.5, d)
            p300.mix(10, 52.5, d)
            p300.blow_out()
            p300.drop_tip()
            ctx.comment('\n')

    ctx.delay(minutes=2)
    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=2)

    ctx.comment('\n\n--------Transferring Sample to Mag Plate----------\n')
    for s, d in zip(mag_plate.rows()[0][:num_full_cols],
                    final_plate.rows()[0]):
        pick_up(m300)
        m300.aspirate(50, s)
        m300.dispense(50, d)
        m300.drop_tip()

    # leftover
    if leftover:
        for s, d in zip(last_col_mag, last_col_final_plate):
            pick_up(p300)
            p300.aspirate(50, s)
            p300.dispense(50, d)
            p300.drop_tip()
