"""OPENTRONS."""
from opentrons import types
import math

metadata = {
    'protocolName': 'Protocol Title',
    'author': 'AUTHOR NAME <authoremail@company.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx):
    """PROTOCOL."""
    [
     num_samples
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples")
    # define all custom variables above here with descriptions:

    # number of samples
    num_cols = math.ceil(num_samples/8)
    vol_beads = num_cols*15

    # "True" for park tips, "False" for discard tips

    # load modules/labware
    temp_1 = ctx.load_module('tempdeck', '1')
    thermo_tubes = temp_1.load_labware('opentrons_96_aluminumblock_generic_pcr'
                                       '_strip_200ul')
    # can change to whatever plate works better for next off-deck step
    supernate_final = ctx.load_labware('customabnest_96_wellplate_200ul', '2')
    mag_module = ctx.load_module('magnetic module gen2', '4')
    midi_plate_2 = mag_module.load_labware('nest_96_wellplate_2ml_deep')
    reagent_resv = ctx.load_labware('nest_12_reservoir_15ml', '5')
    liquid_trash = ctx.load_labware('nest_1_reservoir_195ml', '6')

    # load tipracks
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['7']]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['8', '9', '10', '11']]

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tiprack200)

    # reagents
    '''includes reagents used in other steps for housekeeping purposes'''
    # master_mix = thermo_tubes.rows()[0][0]
    # nf_water = thermo_tubes.rows()[0][2]
    # tsb = thermo_tubes.rows()[0][4]
    ipb = thermo_tubes.rows()[0][0]
    rsb = thermo_tubes.rows()[0][2]
    etoh = reagent_resv.wells()[11]
    source_midi_plate_2 = midi_plate_2.rows()[0][:num_cols]
    final_plate_dest = midi_plate_2.rows()[0][6:6+num_cols]
    supernate_final_dest = supernate_final.rows()[0][:num_cols]
    # hard code variables
    z_mod_value = 5
    a_mod_value = 5
    # MIDI_plate_mag_height = 9

    def bead_mixing(well, pip, mvol, top=5, bottom=1,
                    asp_speed_mod=5, disp_speed_mod=5, reps=10):
        vol = mvol * .9

        pip.move_to(well.center())
        pip.flow_rate.aspirate *= asp_speed_mod
        pip.flow_rate.dispense *= disp_speed_mod
        for _ in range(reps):
            pip.aspirate(vol, well.bottom(bottom))
            pip.dispense(vol, well.bottom(top))
            pip.aspirate(vol, well.bottom(top))
            pip.dispense(vol, well.bottom(bottom))
            pip.flow_rate.aspirate /= asp_speed_mod
            pip.flow_rate.dispense /= disp_speed_mod
        ctx.comment('\n\n')
    # protocol

    mag_module.engage()
    ctx.delay(minutes=5)
# transfer 15ul IPB to each empty well in mag module plate
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING IPB~~~~~~~~~~~~~~~~\n')
    m20.pick_up_tip()
    vol_mix_beads = vol_beads if vol_beads < 20 else 22
    for i, dest in enumerate(final_plate_dest):
        if i % 2 == 0:
            bead_mixing(ipb, m20, vol_mix_beads, top=3, asp_speed_mod=1,
                        disp_speed_mod=1)
        m20.flow_rate.aspirate /= 4
        m20.flow_rate.dispense /= 4
        m20.flow_rate.blow_out /= 4
        m20.aspirate(15, ipb)
        m20.move_to(ipb.top(-2))
        ctx.delay(seconds=2)
        m20.touch_tip(v_offset=-2)
        m20.move_to(ipb.top(-2))
        m20.aspirate(3, ipb.top(-2))
        m20.dispense(3, dest.top())
        m20.dispense(15, dest)
        m20.flow_rate.aspirate *= 4
        m20.flow_rate.dispense *= 4
        m20.flow_rate.blow_out *= 4
    m20.drop_tip()

# Transfer 125ul supernatant from mag plate left to mag plate right w/10x mix
    ctx.comment('\n\n~~~~~~~~~~~~~~~MOVING SUPERNATANT~~~~~~~~~~~~~~~~\n')
    mag_module.engage()
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    num_times = 1
    for source, dest in zip(source_midi_plate_2, final_plate_dest):
        side = 1 if num_times % 2 == 0 else -1
        m300.flow_rate.aspirate /= 5
        m300.pick_up_tip()
        m300.move_to(source.top())
        ctx.max_speeds['Z'] /= z_mod_value
        ctx.max_speeds['A'] /= a_mod_value
        m300.aspirate(
                      125, source.bottom().move(types.Point(x=side,
                                                            y=0, z=0.5)))
        m300.move_to(source.top(-2))
        ctx.max_speeds['Z'] *= z_mod_value
        ctx.max_speeds['A'] *= a_mod_value
        ctx.delay(seconds=2)
        m300.touch_tip(v_offset=-2)
        m300.move_to(source.top(-2))
        m300.aspirate(10, source.top(-2))
        m300.dispense(10, dest.top(-2))
        m300.dispense(125, dest)
        m300.flow_rate.aspirate *= 5
        m300.flow_rate.dispense /= 2
        m300.flow_rate.aspirate /= 2
        m300.mix(10, 120)
        m300.flow_rate.dispense *= 2
        m300.flow_rate.aspirate *= 2
        m300.drop_tip()
        num_times += 1
    mag_module.disengage()
    # Incubate 5 minutes
    ctx.comment('\n\n~~~~~~~~~~~~~~~INCUBATING W/IPB~~~~~~~~~~~~~~~~\n')
    ctx.delay(minutes=5)
    # Mag stand engage for 5 minutes
    # discard supernatant
    mag_module.engage()
    ctx.delay(minutes=5)
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    num_times = 1
    ctx.comment('\n\n~~~~~~~~~~~~~~~DISCARDING SUPERNATANT~~~~~~~~~~~~~~~~\n')
    for source in final_plate_dest:
        side = 1 if num_times % 2 == 0 else -1
        m300.flow_rate.aspirate /= 5
        m300.pick_up_tip()
        ctx.max_speeds['Z'] /= z_mod_value
        ctx.max_speeds['A'] /= a_mod_value
        m300.aspirate(
            45, source.bottom().move(types.Point(x=side,
                                                 y=0, z=0.5)))
        ctx.max_speeds['Z'] *= z_mod_value
        ctx.max_speeds['A'] *= a_mod_value
        m300.dispense(45, liquid_trash.wells()[0])
        m300.drop_tip()
        m300.flow_rate.aspirate *= 5
        num_times += 1
    mag_module.disengage()
# wash twice: Add 200ul EtOH (let's try 100), wait 30 secs, discard supernatant
    ctx.comment('\n\n~~~~~~~~~~~~~~~WASHING WITH ETOH~~~~~~~~~~~~~~~~\n')
    for _ in range(2):
        for dest in final_plate_dest:
            m300.pick_up_tip()
            m300.aspirate(100, etoh)
            m300.aspirate(10, etoh.top())
            m300.dispense(10, dest.top())
            m300.dispense(100, dest)
            m300.drop_tip()
        ctx.delay(seconds=30)
        # discard supernatant
        mag_module.engage()
        ctx.delay(minutes=5)
        ctx.max_speeds['Z'] = 50
        ctx.max_speeds['A'] = 50
        num_times = 1
        for source in final_plate_dest:
            side = 1 if num_times % 2 == 0 else -1
            m300.flow_rate.aspirate /= 5
            m300.pick_up_tip()
            ctx.max_speeds['Z'] /= z_mod_value
            ctx.max_speeds['A'] /= a_mod_value
            m300.aspirate(
                100, source.bottom().move(types.Point(x=side,
                                                      y=0, z=0.5)))
            ctx.max_speeds['Z'] *= z_mod_value
            ctx.max_speeds['A'] *= a_mod_value
            m300.dispense(100, liquid_trash.wells()[0])
            m300.drop_tip()
            m300.flow_rate.aspirate *= 5
            num_times += 1

# remove remaining EtOH w/20ul pipette
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    num_times = 1
    ctx.comment('\n\n~~~~~~~~~~~~~~~REMOVING REMAINING ETOH~~~~~~~~~~~~~~~~\n')
    for source in final_plate_dest:
        side = 1 if num_times % 2 == 0 else -1
        m20.flow_rate.aspirate /= 5
        m20.pick_up_tip()
        m20.move_to(source.top())
        ctx.max_speeds['Z'] /= z_mod_value
        ctx.max_speeds['A'] /= a_mod_value
        m20.aspirate(
            15, source.bottom().move(types.Point(x=side,
                                                 y=0, z=0.5)))
        m20.move_to(source.top())
        m20.aspirate(3, source.top())
        ctx.max_speeds['Z'] *= z_mod_value
        ctx.max_speeds['A'] *= a_mod_value
        m20.dispense(15, liquid_trash.wells()[0])
        m20.drop_tip()
        m20.flow_rate.aspirate *= 5
        num_times += 1
# Air dry 5 minutes
    ctx.comment('\n\n~~~~~~~~~~~~~~~AIR DRYING~~~~~~~~~~~~~~~~\n')
    ctx.delay(minutes=5)
# disengage mag stand
    mag_module.disengage()
# add 32ul RSB, mix to resuspend
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING RSB~~~~~~~~~~~~~~~~\n')
    for dest in final_plate_dest:
        m300.pick_up_tip()
        m300.aspirate(32, rsb)
        m300.dispense(32, dest)
        m300.mix(10, 40)
        m300.drop_tip()
# Wait 2 minutes
    ctx.delay(minutes=2)
# engage mag stand 2 minutes
    mag_module.engage()
    ctx.delay(minutes=2)
# transfer 30 ul supernatant from MIDI plate 2 to new 96 well pcr plate
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    num_times = 1
    ctx.comment('\n\n~~~~~~~~~~~~~~TRANSFERRING SUPERNATANT~~~~~~~~~~~~~~~~\n')
    for source, dest in zip(final_plate_dest, supernate_final_dest):
        side = 1 if num_times % 2 == 0 else -1
        m300.flow_rate.aspirate /= 5
        m300.pick_up_tip()
        ctx.max_speeds['Z'] /= z_mod_value
        ctx.max_speeds['A'] /= a_mod_value
        m300.aspirate(
            30, source.bottom().move(types.Point(x=side,
                                                 y=0, z=0.5)))
        ctx.max_speeds['Z'] *= z_mod_value
        ctx.max_speeds['A'] *= a_mod_value
        m300.dispense(30, dest)
        m300.drop_tip()
        m300.flow_rate.aspirate *= 5
        num_times += 1

    # for c in ctx.commands():
    #     print(c)
