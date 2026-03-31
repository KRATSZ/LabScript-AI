from opentrons import protocol_api, types

metadata = {
    'protocolName': '''GeneRead QIAact Lung DNA UMI Panel Kit:
                       Cleanup of Target Enrichment PCR with
                       QIAact Beads''',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [samples, p300_mount,
        p20_mount, engage_height] = get_values(  # noqa: F821
        "samples", "p300_mount", "p20_mount", "engage_height")

    if not 1 <= samples <= 12:
        raise Exception('''Invalid number of samples.
                        Sample number must be between 1-12.''')

    # Load Labware
    tipracks_200ul = ctx.load_labware('opentrons_96_filtertiprack_200ul', 9)
    tipracks_20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul', 6)
    tc_mod = ctx.load_module('thermocycler module')
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    mag_mod = ctx.load_module('magnetic module gen2', 1)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
                    'opentrons_24_aluminumblock_nest_2ml_snapcap')
    pcr_tubes = ctx.load_labware(
                    'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
                    2)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 5)
    trash = ctx.loaded_labwares[12]['A1']

    # Load Pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tipracks_200ul])
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])

    # Wells
    mag_plate_wells = mag_plate.wells()[:samples]
    tc_plate_wells_forward = tc_plate.wells()[:samples]
    tc_plate_wells_reverse = tc_plate.wells()[80:80+samples]
    beads = temp_plate['A1']
    nfw = reservoir['A12']
    ethanol = reservoir['A1']

    # Helper Functions
    def pick_up(pip, loc=None):
        try:
            if loc:
                pip.pick_up_tip(loc)
            else:
                pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            pip.pause("Please replace the empty tip racks!")
            pip.reset_tipracks()
            pip.pick_up_tip()

    sides = [-1 + (((n // 8) % 2) * 1*2)
             for n in range(96)]

    def getWellSide(well, plate, custom_sides=None):
        index = plate.wells().index(well)
        if custom_sides:
            return custom_sides[index]
        return sides[index]

    def remove_supernatant(vol, src, dest, side, pip=p300, mode=None):
        if mode == 'elution':
            p300.flow_rate.aspirate = 10
        else:
            p300.flow_rate.aspirate = 30
            p300.flow_rate.dispense = 30
        while vol > 200:
            p300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            p300.dispense(200, dest)
            p300.aspirate(10, dest)
            vol -= 200
        p300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        p300.dispense(vol, dest)
        if mode == 'elution':
            p300.blow_out()
        if dest == trash:
            p300.blow_out()
        p300.flow_rate.aspirate = 50

    def reset_flow_rates():
        p300.flow_rate.aspirate = 46.43
        p300.flow_rate.dispense = 46.43

    def remove_residiual_supernatant():
        for well in mag_plate_wells:
            pick_up(p20)
            p20.aspirate(10, well.bottom().move(types.Point(
                        x=getWellSide(well, mag_plate), y=0, z=0.5)))
            p20.dispense(10, trash)
            p20.drop_tip()

    def etoh_wash(reps):
        for _ in range(reps):
            pick_up(p300)
            for well in mag_plate_wells:
                p300.aspirate(200, ethanol)
                p300.dispense(200, well.top(-2))
                p300.blow_out()
            p300.drop_tip()

            ctx.delay(minutes=2, msg="Waiting for solution to clear.")

            for well in mag_plate_wells:
                pick_up(p300)
                remove_supernatant(200, well, trash, getWellSide(well,
                                                                 mag_plate))
                p300.drop_tip()

    # Protocol Steps

    # Set Temperature Module to 20C
    temp_mod.set_temperature(20)

    # Centrifuge Product
    ctx.pause("Centrifuge the Forward and Reverse PCRs ")

    # Combine Forward and Reverse PCRs
    for fwd, rev, dest in zip(tc_plate_wells_forward, tc_plate_wells_reverse,
                              mag_plate_wells):
        pick_up(p300)
        p300.aspirate(20, fwd)
        p300.dispense(20, dest)
        p300.blow_out()
        p300.aspirate(20, rev)
        p300.dispense(20, dest)
        p300.blow_out()
        p300.drop_tip()

    # Add Nuclease-Free Water to Samples
    pick_up(p300)
    for well in mag_plate_wells:
        p300.aspirate(60, nfw)
        p300.dispense(60, well.top(-5))
        p300.blow_out()
    p300.drop_tip()

    # Add 100 uL of Beads to Samples
    for well in mag_plate_wells:
        pick_up(p300)
        p300.aspirate(100, beads)
        p300.dispense(100, well)
        p300.mix(10, 100)
        p300.blow_out()
        p300.drop_tip()

    # Incubate at Room Temperature
    ctx.delay(minutes=5, msg="Incubating at Room Temperature")

    # Engage Magnetic Module
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=10, msg='Engaging Magnetic Module for 10 minutes.')

    # Remove Supernatant
    for well in mag_plate_wells:
        pick_up(p300)
        remove_supernatant(200, well, trash, getWellSide(well, mag_plate))
        p300.drop_tip()

    # Completely Remove Residual Supernatant
    remove_residiual_supernatant()

    # Ethanol Wash (2x)
    etoh_wash(2)

    # Centrifuge Samples
    mag_mod.disengage()
    ctx.pause('''Centrifuge the samples and replace the
                 plate on the magnetic module.''')

    # Engaging Magnet for 2 minutes
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=2, msg='Engaging Magnetic Module for 2 minutes.')

    # Completely Remove Residual Supernatant
    remove_residiual_supernatant()

    # Air Dry Beads for 10 minutes
    ctx.delay(minutes=10, msg='Air Drying Beads for 10 minutes.')
    mag_mod.disengage()

    # Add 16 uL of Nuclease-Free Water to Elute DNA
    for well in mag_plate_wells:
        pick_up(p20)
        p20.aspirate(16, nfw)
        p20.dispense(16, well.bottom(3))
        p20.mix(10, 16, well.bottom(1))
        p20.blow_out()
        p20.drop_tip()

    # Engaging Magnet for 5 minutes
    mag_mod.engage(height=engage_height)
    ctx.delay(minutes=5, msg='Engaging Magnetic Module for 5 minutes.')

    pcr_tube_wells = pcr_tubes.wells()[:samples]

    # Transfer Supernatant to PCR Tubes
    for src, dest in zip(mag_plate_wells, pcr_tube_wells):
        pick_up(p20)
        p20.aspirate(13.4, src.bottom().move(types.Point(
                        x=getWellSide(well, mag_plate), y=0, z=0.5)))
        p20.dispense(13.4, dest)
        p20.blow_out()
        p20.drop_tip()
