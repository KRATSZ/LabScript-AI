from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'Extraction with Mag-Bind TotalPure NGS kit',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [num_samp, num_mag_beads_tubes, mag_bead_mix_resuspend_vol,
     mag_bead_mix_resuspend_reps, rr1, rr2, rr3, tr1, tr2, tr3, tr4, tr5,
        tr6, tr7, tr8, tr9, tr10,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        'num_samp', 'num_mag_beads_tubes', 'mag_bead_mix_resuspend_vol',
        'mag_bead_mix_resuspend_reps',
        'rr1', 'rr2', 'rr3', 'tr1',
        'tr2', 'tr3', 'tr4', 'tr5',
        'tr6', 'tr7', 'tr8', 'tr9', 'tr10', 'p20_mount', 'p300_mount')

    if not 1 <= num_samp <= 24:
        raise Exception("Enter a sample number between 1-24")

    # load labware
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep', 'MAG PLATE')

    temp_mod_samp = ctx.load_module('temperature module gen2', '3')
    samples = temp_mod_samp.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap', 'SAMPLES')

    temp_mod_reagent = ctx.load_module('temperature module gen2', '6')
    cool_reagents = temp_mod_reagent.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap', 'COOL REAGENTS')

    hot_reagents = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2',
        'HOT REAGENTS')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', '9')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '5')

    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                  for slot in ['8', '11']]
    tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
                 for slot in ['7', '10']]
    final_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '4',
        'FINAL RACK')

    # load p300ette
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tiprack300)

    def pick_up300():
        try:
            p300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all 300ul tip racks. Empty trash if needed.")
            p300.reset_tipracks()
            p300.pick_up_tip()

    # load reagents
    temp_mod_samp.set_temperature(37)
    temp_mod_reagent.set_temperature(4)
    ethanol = reservoir.wells()[0]
    water = reservoir.wells()[1]
    waste = waste_res.wells()[0]

    room_temp_reag = hot_reagents.wells()[:3]
    room_temp_reag_vols = [rr1, rr2, rr3]

    cool_reag = cool_reagents.wells()[:6]
    cool_reag_vols = [tr1, tr2, tr3, tr4, tr5, tr6]

    cool_reag_visc = cool_reagents.wells()[6:9]
    cool_reag_visc_vols = [tr7, tr8, tr9]

    cool_reag_visc_post = cool_reagents.wells()[9]
    cool_reag_visc_post_vol = tr10

    # add cold reagents
    ctx.comment('\n\n Add Room Temp Reagents \n\n')
    for reagent, reagent_vol in zip(room_temp_reag, room_temp_reag_vols):
        p20.pick_up_tip()
        for dest in samples.wells()[:num_samp]:
            p20.aspirate(reagent_vol, reagent)
            p20.dispense(reagent_vol, dest.top(z=-3))
            p20.blow_out()
        p20.drop_tip()
    ctx.comment('\n\n\n')

    # add room temp non viscous reagents
    ctx.comment('\n\n Add Cool Temp Non Viscous Reagents \n\n')
    for reagent, reagent_vol in zip(cool_reag, cool_reag_vols):
        p20.pick_up_tip()
        for dest in samples.wells()[:num_samp]:
            p20.aspirate(reagent_vol, reagent)
            p20.dispense(reagent_vol, dest.top(z=-3))
            p20.blow_out()
        p20.drop_tip()
    ctx.comment('\n\n\n')

    # add room temp viscous reagents
    ctx.comment('\n\n Add Cool Temp Viscous Reagents \n\n')
    p20.flow_rate.aspirate = 3.78
    p20.flow_rate.dispense = 3.78
    for reagent, reagent_vol in zip(cool_reag_visc,
                                    cool_reag_visc_vols):
        for dest in samples.wells()[:num_samp]:
            p20.pick_up_tip()
            p20.aspirate(reagent_vol, reagent)
            ctx.delay(seconds=1)
            p20.dispense(reagent_vol, dest)
            p20.blow_out()
            p20.touch_tip()
            p20.drop_tip()
    p20.flow_rate.aspirate = 7.56
    p20.flow_rate.dispense = 7.56

    # mix every 30 minutes for two hours
    ctx.comment('\n\n Mix Every 30 Minutes for Two Hours \n\n')
    for _ in range(4):
        for sample in samples.wells()[:num_samp]:
            pick_up300()
            p300.mix(10, 50, sample)
            p300.drop_tip()
        ctx.delay(minutes=30)
        ctx.comment('\n')

    # add final viscous reagent
    ctx.comment('\n\n Add Final Viscous Reagent \n\n')
    p20.flow_rate.aspirate = 3.78
    p20.flow_rate.dispense = 3.78
    for dest in samples.wells()[:num_samp]:
        p20.pick_up_tip()
        p20.aspirate(cool_reag_visc_post_vol, cool_reag_visc_post)
        ctx.delay(seconds=1)
        p20.dispense(reagent_vol, dest)
        p20.blow_out()
        p20.touch_tip()
        p20.drop_tip()
    p20.flow_rate.aspirate = 7.56
    p20.flow_rate.dispense = 7.56

    # transfer samples to mag plate
    ctx.comment('\n\n Transfer Samples to Mag Plate \n\n')
    for s, d in zip(samples.wells()[:num_samp], mag_plate.wells()):
        pick_up300()
        p300.mix(10, 100, s)
        p300.aspirate(105, s)
        p300.dispense(105, d)
        p300.drop_tip()

    # add magbeads
    ctx.comment('\n\n Adding MagBeads \n\n')
    mag_bead_tubes = hot_reagents.columns()[5][:num_mag_beads_tubes]
    for mag_beads, sample in zip(mag_bead_tubes*num_samp,
                                 mag_plate.wells()[:num_samp]):
        pick_up300()
        p300.mix(mag_bead_mix_resuspend_reps,
                 mag_bead_mix_resuspend_vol,
                 mag_beads)
        p300.aspirate(100, mag_beads)
        p300.dispense(100, sample)
        p300.mix(10, 50, sample)
        p300.blow_out()
        p300.touch_tip()
        p300.drop_tip()

    ctx.comment('\n\n Apply Magnet \n\n')
    ctx.delay(minutes=5)
    mag_mod.engage()
    ctx.delay(minutes=5)

    ctx.comment('\n\n Removing Supernatant \n\n')
    for i, sample in enumerate(mag_plate.wells()[:num_samp]):
        side = -1 if i % 2 == 0 else 1
        asp_loc = sample.bottom().move(
                    Point(x=(sample.length/2-1.5)*side))
        pick_up300()
        p300.move_to(sample.center())
        p300.aspirate(205, asp_loc)
        p300.dispense(205, waste)
        p300.drop_tip()
    mag_mod.disengage()

    ctx.comment('\n\n Two Washes \n\n')
    for _ in range(2):
        for i, sample in enumerate(mag_plate.wells()[:num_samp]):
            pick_up300()
            p300.aspirate(200, ethanol)
            p300.dispense(200, sample)
            p300.mix(10, 50, sample)
            p300.drop_tip()
        ctx.delay(minutes=1)
        mag_mod.engage()
        ctx.delay(minutes=5)
        for i, sample in enumerate(mag_plate.wells()[:num_samp]):
            side = -1 if i % 2 == 0 else 1
            asp_loc = sample.bottom().move(
                        Point(x=(sample.length/2-1.5)*side))
            pick_up300()
            p300.aspirate(200, asp_loc)
            p300.dispense(200, waste)
            p300.drop_tip()
        mag_mod.disengage()
        ctx.comment('\n')
    ctx.delay(minutes=15)

    ctx.comment('\n\n Adding Water \n\n')
    for sample in mag_plate.wells()[:num_samp]:
        pick_up300()
        p300.aspirate(200, water)
        p300.dispense(200, sample)
        p300.mix(20, 50, sample)
        p300.drop_tip()

    ctx.delay(minutes=5)
    mag_mod.engage()
    ctx.delay(minutes=5)
    for i, (s, d) in enumerate(zip(mag_plate.wells()[:num_samp],
                                   final_rack.wells())):
        side = -1 if i % 2 == 0 else 1
        asp_loc = s.bottom().move(
                    Point(x=(s.length/2-1.5)*side))
        pick_up300()
        p300.aspirate(200, asp_loc)
        p300.dispense(200, d)
        p300.drop_tip()
    mag_mod.disengage()
