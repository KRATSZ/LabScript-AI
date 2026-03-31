"""OPENTRONS."""
import math

metadata = {
    'protocolName': 'Illumina DNA Prep, Part 1 Tagmentation',
    'author': 'John C. Lynch <john.lynch@opentrons.com>',
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

    # "True" for park tips, "False" for discard tips

    # load modules/labware
    temp_1 = ctx.load_module('tempdeck', '1')
    thermo_tubes = temp_1.load_labware('opentrons_96_aluminumblock_generic_pcr'
                                       '_strip_200ul')
    sample_plate = ctx.load_labware('customabnest_96_wellplate_200ul',
                                    '2')
    # mag_module = ctx.load_module('magnetic module gen2', '4')
    # reagent_resv = ctx.load_labware('nest_12_reservoir_15ml', '5')
    # liquid_trash = ctx.load_labware('nest_1_reservoir_195ml', '6')

    # load tipracks
    # tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
    #              for slot in ['7']]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['8']]

    # load instrument
    # m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tiprack200)

    # reagents
    '''includes reagents used in other steps for housekeeping purposes'''
    master_mix_tag = thermo_tubes.rows()[0][0]
    # nf_water = thermo_tubes.rows()[0][1]
    # tsb = thermo_tubes.rows()[0][2]
    sample_dest = sample_plate.rows()[0][:num_cols]

    # hard code variables
    airgap = 20
    # protocol
    """DNA samples  MUST be 30ul"""

    # Add 20ul master mix slot 1 to slot 2 samples
    for dest in sample_dest:
        m300.pick_up_tip()
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4
        m300.aspirate(20, master_mix_tag)
        m300.move_to(master_mix_tag.top(-2))
        ctx.delay(seconds=2)
        m300.touch_tip(v_offset=-2)
        m300.aspirate(airgap, master_mix_tag.top())
        m300.dispense(airgap, dest.top())
        m300.dispense(20, dest)
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        m300.mix(10, 45)
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        m300.drop_tip()

    ctx.comment('''Tagmentation Prep Complete. Please transfer samples to
    thermocycler to complete tagmentation''')

    # for c in ctx.commands():
    #     print(c)
