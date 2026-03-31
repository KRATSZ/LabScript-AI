# metadata
metadata = {
    'protocolName': 'Mass Spec Sample Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [p300_mount, p20_mount, num_samples] = get_values(  # noqa: F821
        'p300_mount', 'p20_mount', 'num_samples')

    # check
    if num_samples > 22 or num_samples < 1:
        raise Exception('Invalid number of samples (must be 1-22)')
    if p300_mount == p20_mount:
        raise Exception('Pipette mounts cannot match.')

    # labware
    tempdeck = ctx.load_module('tempdeck', '1')
    plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul')
    tubeblock = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap', '2', 'sample tubes')
    tiprack300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', '5', '300ul tiprack')]
    tiprack20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', '6', '20ul tiprack')]

    # pipettes
    p300 = ctx.load_instrument(
        'p300_single_gen2', p300_mount, tip_racks=tiprack300)
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_mount, tip_racks=tiprack20)

    # samples and reagent setup
    starting_tubes = [
        tube for tube in
        [well for col in tubeblock.columns()[:2] for well in col[:3]] + [
         well for col in tubeblock.columns()[2:]
         for well in col]][:num_samples]
    samples = [
        plate.wells_by_name()[tube.display_name.split(' ')[0]]
        for tube in starting_tubes][:num_samples]
    denaturing_sol = tubeblock.wells_by_name()['D1']
    dtt = tubeblock.wells_by_name()['D2']

    # transfer from tubes to plate
    for tube, well in zip(starting_tubes, samples):
        p300.pick_up_tip()
        p300.transfer(50, tube, well, air_gap=10, new_tip='never')
        p300.blow_out(well.top(-1))
        p300.drop_tip()

    # transfer denaturing solution
    for well in samples:
        p300.pick_up_tip()
        p300.transfer(
            50, denaturing_sol, well, mix_after=(5, 50), new_tip='never')
        p300.blow_out(well.top(-1))
        p300.drop_tip()

    # transfer DTT
    for well in samples:
        p20.pick_up_tip()
        p20.transfer(10, dtt, well, new_tip='never')
        p20.blow_out(well.top(-1))
        p20.drop_tip()

    tempdeck.set_temperature(50)
    ctx.delay(minutes=60)
    tempdeck.set_temperature(4)
    ctx.comment('Protocol finished. Remove plate from 4˚C temperature module \
when ready.')
