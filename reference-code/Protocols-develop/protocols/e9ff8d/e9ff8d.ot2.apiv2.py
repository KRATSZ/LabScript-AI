# flake8: noqa

metadata = {
    'protocolName': '3.1 & 3.2 Incubation Recovery & Pre-Amplification PCR',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    [num_samp, tip_rack, p300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_rack", "p300_mount")

    if not 1 <= num_samp <= 8:
        raise Exception("Enter a sample number between 1-8")

    # labware
    mag_mod = ctx.load_module('magnetic module', 10)

    temp_mod_reag = ctx.load_module('temperature module', 6)
    dummy_plate = temp_mod_reag.load_labware('eppendorf_96_aluminumblock_200ul',
                                             "DUMMY PLATE")
    print(mag_mod, dummy_plate)
    temp_mod = ctx.load_module('temperature module gen2', 9)
    pre_amp_rack = temp_mod.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap',
                                         "PREAMP RACK")
    recov_rack = ctx.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap', 3,
                                  "RECOVERY AGENT RACK")

    strip_tube_plate = ctx.load_labware('eppendorf_96_aluminumblock_200ul', 1,
                                        "SAMPLE PLATE")
    trash_res = ctx.load_labware('nest_12_reservoir_15ml', 2)
    tipracks = [ctx.load_labware(tip_rack, slot)
                for slot in [7]]

    # pipettes
    p300 = ctx.load_instrument('p300_single_gen2',
                               p300_mount,
                               tip_racks=tipracks)
    temp_mod.set_temperature(4)

    # mapping
    samples = strip_tube_plate.columns()[0][:num_samp]
    recovery_agent = recov_rack.wells()[0]
    pre_amp_mix = pre_amp_rack.wells()[0]
    trash = trash_res.wells()[11]

    ctx.comment('\n\n~~~~~~~~~~~~~~~~ADDING RECOVERY AGENT~~~~~~~~~~~~~~~~\n')
    preairgap = 20
    # ADD AIRGAP
    for sample in samples:
        p300.pick_up_tip()
        p300.aspirate(preairgap, recovery_agent.top())
        p300.mix(1, 130, recovery_agent)

        p300.aspirate(125, recovery_agent)
        p300.move_to(recovery_agent.top())
        p300.aspirate(preairgap, recovery_agent.top(), rate=0.05)
        ctx.delay(seconds=3)
        p300.touch_tip(v_offset=-3)
        p300.dispense(preairgap+125+preairgap, sample.top(z=-5), rate=0.2)
        p300.blow_out()
        p300.drop_tip()

    ctx.delay(minutes=2)
    ctx.pause('''
    Ensure the solution developed into a biphasic mixture, then select
    "Resume" in the app.
    ''')

    ctx.comment('\n\n~~~~~~~~~~~~~~~REMOVING RECOVERY AGENT~~~~~~~~~~~~~~~\n')
    for sample in samples:
        p300.pick_up_tip()
        p300.aspirate(125, sample, rate=0.1)
        p300.air_gap(preairgap)
        p300.dispense(125, trash)
        p300.drop_tip()

    ctx.pause("""Proceed directly to Pre-Amplification PCR.
                 No cleanup step is required.""")

    ctx.comment('\n\n~~~~~~~~~~~~~~~~ADDING PRE-AMP MIX~~~~~~~~~~~~~~~~\n')
    for sample in samples:
        p300.pick_up_tip()
        p300.aspirate(35, pre_amp_mix)
        p300.dispense(35, sample, rate=0.2)
        p300.blow_out()
        p300.touch_tip()
        p300.air_gap(20)
        p300.drop_tip()

    ctx.comment("""Pre-Amp mix is added.
                 Transfer all solution to PCR strip tube.
                 Cap firmly and invert 8x to mix. Centrifuge briefly.
                 Incubate in a thermal cycler according to 3.2.D of the SOP""")
