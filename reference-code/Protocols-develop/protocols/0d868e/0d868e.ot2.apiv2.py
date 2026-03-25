from opentrons import types
metadata = {
    'protocolName': 'Ilumina TruSeq Stranded mRNA - Part 1',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, p300_mount] = get_values(  # noqa: F821
        "num_samp", "p300_mount")

    # module
    temp_mod = ctx.load_module('temperature module gen2', 3)
    sample_plate = temp_mod.load_labware('froggabio_96_wellplate_300ul')
    temp_mod.set_temperature(4)
    mag_mod = ctx.load_module('magnetic module gen2', 10)
    mag_plate = mag_mod.load_labware('froggabio_96_wellplate_300ul')

    # labware
    reag_plate = ctx.load_labware('froggabio_96_wellplate_300ul', 1)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 2)
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [7, 8, 9]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', p300_mount, tip_racks=tips)

    ctx.max_speeds['Z'] = 125
    ctx.max_speeds['A'] = 125
    supernatant_headspeed_modulator = 10
    mag_height = 2

    def remove_super(vol):
        ctx.comment('\n-------------REMOVING SUPERNATANT--------------\n\n')
        for i, dest in enumerate(samples):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip()
            m300.move_to(dest.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol, dest.bottom().move(types.Point(x=side,
                          y=0, z=1)),
                          rate=0.1)
            ctx.delay(seconds=1)
            m300.move_to(dest.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, waste)
            m300.blow_out()
            m300.air_gap(50)
            m300.drop_tip()

    # mapping
    num_col = int(num_samp/8)
    samples = sample_plate.rows()[0][:num_col]
    rpb = reag_plate.rows()[0][0]
    bwb = reag_plate.rows()[0][1:7][:num_col*2]
    elb = reag_plate.rows()[0][7]
    bbb = reag_plate.rows()[0][8]
    fpf = reag_plate.rows()[0][9]
    waste = reservoir.wells()[-1]

    # protocol
    ctx.comment('\n---------------ADDING RPB----------------\n\n')
    for col in samples:
        m300.pick_up_tip()
        m300.aspirate(50, rpb)
        m300.dispense(50, col)
        m300.mix(6, 75, col)
        m300.drop_tip()

    ctx.pause('''
    Seal plate with Microseal 'B' adhesive seal.
    Incubate as follows.
    [LS] Place on the thermal cycler and run the mRNA Denaturation program.
    Each well contains 100 μl.
    Incubate for 5 minutes on bench.
    [LS] Centrifuge at 280 × g for 1 minute. Remove adhesive seal.
    Place plate back on magnetic module on OT-2.
    and select "Resume" on the Opentrons app.
    The protocol will incubate for 5 minutes then proceed in the protocol
    to engage magnet. Plate should NOT be on the temperature module any longer.
    ''')
    temp_mod.set_temperature(25)
    samples = mag_plate.rows()[0][:num_col]

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=5)

    remove_super(100)

    mag_mod.disengage()

    ctx.comment('\n---------------ADDING BWB----------------\n\n')
    for s_col, d_col in zip(bwb[:num_col], samples):
        m300.pick_up_tip()
        m300.aspirate(200, s_col)
        m300.dispense(200, d_col)
        m300.mix(6, 75, d_col)
        m300.drop_tip()

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=5)

    remove_super(200)

    mag_mod.disengage()

    ctx.comment('\n---------------ADDING ELB----------------\n\n')
    for col in samples:
        m300.pick_up_tip()
        m300.aspirate(50, elb)
        m300.dispense(50, col)
        m300.mix(6, 75, col)
        m300.drop_tip()

    ctx.pause('''
    Seal plate with Microseal 'B' adhesive seal.
    [LS] Centrifuge at 280 × g for 1 minute.
    Incubate as follows.
    [LS] Place on the thermal cycler and run the mRNA Elution 1 program.
    Each well contains 50 μl.
    Remove adhesive seal.
    Place plate back on magnetic module for BBB addition.
    ''')

    ctx.comment('\n---------------ADDING BBB----------------\n\n')
    for col in samples:
        m300.pick_up_tip()
        m300.aspirate(50, bbb)
        m300.dispense(50, col)
        m300.mix(6, 75, col)
        m300.drop_tip()

    ctx.pause('''
    Seal the RBP plate with a Microseal 'B' adhesive seal before running
    the mRNA denaturation program.
    Centrifuge briefly then remove the adhesive seal.
    Place plate back on magnetic module.
    Protocol will incubate for 5 minutes then engage''')

    samples = mag_plate.rows()[0][:num_col]

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=5)

    remove_super(100)

    mag_mod.disengage()

    ctx.comment('\n---------------ADDING BWB----------------\n\n')
    for s_col, d_col in zip(bwb[num_col:], samples):
        m300.pick_up_tip()
        m300.aspirate(200, s_col)
        m300.dispense(200, d_col)
        m300.mix(6, 75, d_col)
        m300.drop_tip()

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=5)

    remove_super(200)

    mag_mod.disengage()

    ctx.comment('\n---------------ADDING FPF----------------\n\n')
    for col in samples:
        m300.pick_up_tip()
        m300.aspirate(20, fpf)
        m300.dispense(20, col)
        m300.mix(3, 20, col)
        m300.blow_out(col.top(z=-3))
        m300.touch_tip()
        m300.drop_tip()

    ctx.pause('''
    Seal plate with Microseal 'B' adhesive seal.
    [LS] Centrifuge at 280 × g for 1 minute.
    Place on the thermal cycler and run the Elution 2 - Frag - Prime program.
    Each well contains 19.5 μl.
    Remove adhesive seal.
    ''')
