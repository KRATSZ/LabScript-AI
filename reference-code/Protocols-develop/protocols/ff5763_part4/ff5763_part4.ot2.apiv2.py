"""OPENTRONS."""
import math
from opentrons import types

metadata = {
    'protocolName': 'Illumina DNA Prep Part 4, Clean Up Libraries First Half',
    'author': 'Opentrons <protocols@opentrons.com>',
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

    # define allcustom variables above here with descriptions:

    # number of samples
    num_cols = math.ceil(num_samples/8)

    # "True" for park tips, "False" for discard tips

    # load modules/labware
    temp_1 = ctx.load_module('tempdeck', '1')
    mag_module = ctx.load_module('magnetic module gen2', '4')
    # will be custom_from_maurice
    thermo_tubes = temp_1.load_labware('opentrons_96_aluminumblock_generic_pcr'
                                       '_strip_200ul')
    sample_plate = ctx.load_labware('customabnest_96_wellplate_200ul', '2')
    midi_plate_2 = ctx.load_labware('nest_96_wellplate_2ml_deep', '3')
    midi_plate_1 = mag_module.load_labware('nest_96_wellplate_2ml_deep')
    reagent_resv = ctx.load_labware('nest_12_reservoir_15ml', '5')
    liquid_trash = ctx.load_labware('nest_1_reservoir_195ml', '6')

    # load tipracks
    # tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
    #              for slot in ['7', '8']]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['7', '8']]

    # load instrument
    # m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tiprack200)

    # reagents
    '''includes reagents used in other steps for housekeeping purposes'''
    # master_mix = thermo_tubes.rows()[0][0]
    nf_water = thermo_tubes.rows()[0][0]
    # tsb = thermo_tubes.rows()[0][4]
    ipb = thermo_tubes.rows()[0][2]
    sample_dest_ab = sample_plate.rows()[0][6:6+num_cols]
    sample_dest_MIDI_1 = midi_plate_1.rows()[0][6:6+num_cols]
    sample_dest_MIDI_2 = midi_plate_2.rows()[0][:num_cols]

    # hard code variables
    vol_supernatant = 50
    supernatant_headspeed_modulator = 5
    airgap_nfwater = 10

    def bead_mixing(well, pip, mvol, top=5, bottom=1,
                    asp_speed_mod=5, disp_speed_mod=5, reps=10):
        """bead_mixing."""
        """
        'bead_mixing ' will mix liquid that contains beads. This is done by
        aspirating from the middle of the well & dispensing from the bottom to
        mix the beads with the other liquids as much as possible. Aspiration &
        dispensing will also be reversed to ensure proper mixing.
        param well: The current well that the mixing will occur in.
        param pip: The pipet that is currently attached/ being used.
        param mvol: The volume that is transferred before the mixing steps.
        param asp/disp_speed_mod: The speed modulation for aspirations and
        dispenses. 0.5 will divide default volume in half, 2 will double it.
        param reps: The number of mix repetitions that should occur. Note~
        During each mix rep, there are 2 cycles of aspirating from bottom,
        dispensing at the top and 2 cycles of aspirating from middle,
        dispensing at the bottom
        """
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

    # move samples to Deep Well Plate on Mag Module
    ctx.comment('\n\n~~~~~~~~~~~~~~MOVING SAMPLES TO MAGNETS~~~~~~~~~~~~~~~\n')
    for source, dest in zip(sample_dest_ab, sample_dest_MIDI_1):
        m300.pick_up_tip()
        m300.aspirate(70, source)
        m300.dispense(70, dest)
        m300.drop_tip()

    # move supernatant to Deep Well Plate, toss customab at this point, used up

    mag_module.engage()
    ctx.delay(minutes=5)
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    num_times = 1
    ctx.comment('\n\n~~~~~~~~~~~~~~~MOVING SUPERNATANT~~~~~~~~~~~~~~~~\n')
    for source, dest in zip(sample_dest_MIDI_1, sample_dest_MIDI_2):
        side = 1 if num_times % 2 == 0 else -1
        m300.pick_up_tip()
        m300.flow_rate.aspirate /= 5
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m300.aspirate(
            vol_supernatant, source.bottom().move(types.Point(x=side,
                                                              y=0, z=0.5)))
        m300.move_to(source.top())
        m300.flow_rate.aspirate *= 5
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m300.dispense(vol_supernatant, dest)
        m300.drop_tip()
        num_times += 1
    mag_module.disengage()

    # add 40ul NFW to MIDI plate 1
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING NFW~~~~~~~~~~~~~~~~\n')
    for dest in sample_dest_MIDI_2:
        m300.pick_up_tip()
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4
        m300.aspirate(40, nf_water)
        m300.move_to(nf_water.top())
        m300.aspirate(airgap_nfwater, nf_water.top(2))
        m300.dispense(airgap_nfwater, dest.top())
        m300.dispense(40, dest)
        m300.flow_rate.aspirate *= 4
        m300.flow_rate.dispense *= 4
        m300.drop_tip()
    # add 45ul IPB to MIDI plate 2 and mix 10x
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING IPB~~~~~~~~~~~~~~~~\n')
    for i, dest in enumerate(sample_dest_MIDI_2):
        m300.pick_up_tip()
        if i % 2 == 0:
            bead_mixing(dest, m300, 45, asp_speed_mod=1,
                        disp_speed_mod=1)
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4
        m300.aspirate(45, ipb)
        m300.dispense(45, dest)
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        m300.mix(10, 100)
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        m300.drop_tip()
    # Incubate 5 minutes
    m300.move_to(reagent_resv.wells()[0].top(3))
    m300.move_to(liquid_trash.wells()[0].top(3))
    ctx.delay(minutes=5)
    ctx.comment('\n\n')
    ctx.comment('''First half of library cleanup completed. Please dispose'''
                ''' of AB Gene plate in slot 2 and now empty Deep Well Plate'''
                ''' on magnetic module. Deep Well Plate in slot 3 should be '''
                '''moved to magnetic module''')

    # for c in ctx.commands():
    #     print(c)
