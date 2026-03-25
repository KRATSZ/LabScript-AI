"""PROTOCOL."""
import math
metadata = {
    'protocolName': 'Nucleic Acid Purification/Cloning',
    'author': 'Opentrons',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx):
    """PROTOCOL BODY."""
    [num_samples
     ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples")

    # define all custom variables above here with descriptions:

    # number of samples
    num_cols = math.ceil(num_samples/8)

    # load modules
    temp_1 = ctx.load_module('tempdeck', '1')
    temp_3 = ctx.load_module('tempdeck', '3')

    # load labware
    gibson_tubes = temp_1.load_labware('opentrons_24_aluminumblock_generic'
                                       '_2ml_screwcap')
    fragment_plate = ctx.load_labware('azentalifesciences_96_wellplate_200ul',
                                      '2')
    assembly_plate = temp_3.load_labware(
                                        'azentalifesciences_96_aluminumblock'
                                        '_200ul'
                                         )
    backbone_reservoir = ctx.load_labware('azentalifesciences_12_reservoir'
                                          '_21000ul', '4')

    # load tipracks
    tiprack = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
               for slot in ['10', '11']]

    # load instrument
    p20 = ctx.load_instrument(
                        'p20_single_gen2',
                        mount='right',
                        tip_racks=tiprack
    )
    m20 = ctx.load_instrument(
                        'p20_multi_gen2',
                        mount='left',
                        tip_racks=tiprack
    )

    # reagents
    gibson = gibson_tubes.wells()[0]
    fragments = fragment_plate.rows()[0][:num_cols]
    backbone = backbone_reservoir.wells()[0]
    sample_dests_s = assembly_plate.wells()[:num_samples]
    sample_dests_m = assembly_plate.rows()[0][:num_cols]

    # plate, tube rack maps

    # protocol
    # Step 0, set temperature
    temp_1.set_temperature(4)
    temp_3.set_temperature(4)

    # Step 1 Add 9ul backbone to assembly_plate
    m20.pick_up_tip()
    for dest in sample_dests_m:
        m20.transfer(9,
                     backbone,
                     dest,
                     new_tip='never'
                     )
    m20.drop_tip()
    # Step 2 Add 1ul fragments to assembly_plate
    for source, dest in zip(fragments, sample_dests_m):
        m20.pick_up_tip()
        m20.transfer(1,
                     source,
                     dest,
                     new_tip='never'
                     )
        m20.drop_tip()
    # Step 3 Add 10ul gibson to assembly_plate
    for dest in sample_dests_s:
        p20.pick_up_tip()
        p20.transfer(10,
                     gibson,
                     dest,
                     mix_after=(3, 10),
                     new_tip='never'
                     )
        p20.drop_tip()

    for c in ctx.commands():
        print(c)
