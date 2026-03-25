"""OPENTRONS."""
import math
from opentrons import types
metadata = {
    'protocolName': 'Illumina DNA Prep Part 2, Post-Tagmentation Clean-up',
    'author': 'AUTHOR NAME <authoremail@company.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}

TEST_MODE = False


def run(ctx):
    """PROTOCOL."""
    [num_samples
     ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples")

    # define all custom variables above here with descriptions:

    # number of samples
    num_cols = math.ceil(num_samples/8)

    # "True" for park tips, "False" for discard tips

    # load modules/labware
    """Step 2 has the sample plate on the mag module in slot 4!"""
    temp_1 = ctx.load_module('tempdeck', '1')
    starting_tray = ctx.load_labware('customabnest_96_wellplate_200ul', '2')
    thermo_tubes = temp_1.load_labware('opentrons_96_aluminumblock_generic_pcr'
                                       '_strip_200ul')
    mag_module = ctx.load_module('magnetic module gen2', '4')
    sample_plate = mag_module.load_labware('nest_96_wellplate_2ml_deep')
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
    '''always have a tube in thermo_tubes.row[0] for calibration process'''
    '''includes reagents used in other steps for housekeeping purposes'''
    # master_mix_tag = thermo_tubes.rows()[0][0]
    # nf_water = thermo_tubes.rows()[0][2]
    tsb = thermo_tubes.rows()[0][0]
    twb = reagent_resv.rows()[0][0]
    # pcr_mix = reagent_resv.rows()[0][1]

    starting_dest = starting_tray.rows()[0][:num_cols]
    sample_dest = sample_plate.rows()[0][:num_cols]

    supernatant_headspeed_modulator = 5
    step5_vol_supernatant = 65
    step6_vol_supernatant = 105
    # nest_96_mag_engage_height = 10
    airgap_300 = 20
    airgap_20 = 5
    # protocol

    # Steps 1-2
    # Slowly add 10ul TSB (stop buffer) then slowly mix to suspend
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING TSB~~~~~~~~~~~~~~~~\n')
    for dest in starting_dest:
        m20.pick_up_tip()
        m20.flow_rate.aspirate /= 3
        m20.flow_rate.dispense /= 3
        m20.aspirate(10, tsb)
        m20.move_to(tsb.top(-2))
        ctx.delay(seconds=2)
        m20.touch_tip(v_offset=-2)
        m20.move_to(tsb.top(-2))
        m20.aspirate(airgap_20, tsb.top())
        m20.dispense(airgap_20, dest.top())
        m20.dispense(10, dest)
        m20.drop_tip()
        m20.flow_rate.aspirate *= 3
        m20.flow_rate.dispense *= 3
    ctx.comment('\n\n~~~~~~~~~~~~~~~MIXING~~~~~~~~~~~~~~~~\n')
    for dest in starting_dest:
        m300.pick_up_tip()
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4
        m300.mix(10, 55, dest)
        m300.flow_rate.aspirate *= 4
        m300.flow_rate.dispense *= 4
        m300.drop_tip()
    ctx.comment("\n\n")
    ctx.pause("""Please move sample plate from slot 2"""
              """ to off-deck thermocycler then return to slot 2."""
              """Click 'Resume' when set""")
    ctx.comment('\n\n')

    # Mid-protocol transfer to mag module
    ctx.comment('\n\n~~~~~~~~~~~~~MOVING SAMPLES FROM 2 TO 4~~~~~~~~~~~~~~~\n')
    for source, dest in zip(starting_dest, sample_dest):
        m300.pick_up_tip()
        m300.flow_rate.aspirate /= 3
        m300.flow_rate.dispense /= 3
        m300.aspirate(50, source)
        m300.move_to(source.top(-2))
        ctx.delay(seconds=2)
        m300.aspirate(airgap_300, source.top(-2))
        m300.move_to(dest.top(10))
        m300.move_to(dest.top(-2))
        m300.dispense(airgap_300, dest.top(-2))
        m300.dispense(50, dest)
        m300.blow_out(dest.top())
        m300.flow_rate.aspirate *= 3
        m300.flow_rate.dispense *= 3
        m300.drop_tip()

    # Step 4
    # Incubate on mag stand, 3 minutes
    ctx.comment('\n\n')
    ctx.comment('''incubate 3 minutes''')
    ctx.comment('\n\n')
    mag_module.engage()
    ctx.delay(minutes=3)

    # Step 5
    # Discard supernatant
    ctx.comment('\n\n~~~~~~~~~~~~~~~DISCARDING SUPERNATANT~~~~~~~~~~~~~~~~\n')
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    num_times = 1
    for source in sample_dest:
        side = 1 if num_times % 2 == 0 else -1
        m300.flow_rate.aspirate /= 5
        m300.flow_rate.dispense /= 5
        m300.pick_up_tip()
        m300.move_to(source.top(10))
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m300.aspirate(
            step5_vol_supernatant,
            source.bottom().move(types.Point(x=side,
                                             y=0, z=0.5)))
        m300.move_to(source.top())
        m300.aspirate(airgap_300, source.top())
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m300.flow_rate.aspirate *= 5
        m300.flow_rate.dispense *= 5
        m300.dispense(step5_vol_supernatant+airgap_300,
                      liquid_trash.wells()[0])
        m300.drop_tip()
        num_times += 1
    mag_module.disengage()

    # Step 6, TWB wash twice removing super each time
    ctx.comment('\n\n~~~~~~~~~~~~~TWB WASH AND SUPER REMOVAL~~~~~~~~~~~~~~\n')
    for _ in range(2):
        m300.flow_rate.aspirate /= 5
        m300.flow_rate.dispense /= 5
        for dest in sample_dest:
            m300.pick_up_tip()
            m300.aspirate(100, twb)
            m300.move_to(twb.top())
            m300.aspirate(airgap_300, twb.top())
            ctx.delay(seconds=2)
            m300.dispense(airgap_300, dest.top())
            m300.dispense(100, dest)
            m300.mix(3, 120)
            m300.drop_tip()
        m300.flow_rate.aspirate *= 5
        m300.flow_rate.dispense *= 5

        mag_module.engage()

        ctx.delay(minutes=3)
        # remove super
        ctx.max_speeds['Z'] = 50
        ctx.max_speeds['A'] = 50
        num_times = 1
        for source in sample_dest:
            side = 1 if num_times % 2 == 0 else -1
            m300.pick_up_tip()
            m300.move_to(source.top(10))
            m300.flow_rate.aspirate /= 5
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(
                step6_vol_supernatant,
                source.bottom().move(types.Point(x=side,
                                                 y=0, z=0.5)))
            m300.move_to(source.top())
            m300.aspirate(airgap_300, source.top())
            m300.flow_rate.aspirate *= 5
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(step6_vol_supernatant+airgap_300,
                          liquid_trash.wells()[0])
            # m300.return_tip()
            m300.drop_tip()
            num_times += 1
        mag_module.disengage()
    # Step 7, add twb and mix, leave TWB and incubate on mag stand until step 3
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING TWB AND MIXING~~~~~~~~~~~~~~~~\n')
    m300.flow_rate.aspirate /= 5
    m300.flow_rate.dispense /= 5
    for dest in sample_dest:
        m300.pick_up_tip()
        m300.aspirate(100, twb)
        m300.move_to(twb.top())
        m300.aspirate(airgap_300, twb.top())
        ctx.delay(seconds=2)
        m300.dispense(airgap_300, dest.top())
        m300.dispense(100, dest)
        m300.mix(3, 120)
        m300.drop_tip()
    m300.flow_rate.aspirate *= 5
    m300.flow_rate.dispense *= 5

    mag_module.engage()
    ctx.comment('\n\n')
    ctx.comment('''Clean up complete, please move on to part 3 of the'''
                ''' protocol, leaving the plate engaged on the'''
                ''' magnetic module''')

    # End part 2
