import math

metadata = {
    'protocolName': '4. DNA template-edit',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [clearance_aspirate, clearance_dispense, sample_count
     ] = get_values(  # noqa: F821
      'clearance_aspirate', 'clearance_dispense', 'sample_count')

    num_cols = math.ceil(sample_count / 8)

    # p50 multi, p20 multi and tips
    tips20 = [ctx.load_labware("opentrons_96_tiprack_20ul", '1')]
    tips300 = [ctx.load_labware("opentrons_96_tiprack_300ul", '4')]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'right', tip_racks=tips20)
    p50m = ctx.load_instrument(
        "p50_multi", 'left', tip_racks=tips300)

    # thermo 96 well plate on slot 6
    dna_template = ctx.load_labware("thermo_96_wellplate_200ul", '6')

    # pcr plate on slot 3
    pcr_plate = ctx.load_labware("pcr_plate", '3')

    # aspir8 reservoir in slot 2 with ghost movement to reservoir
    reservoir = ctx.load_labware("aspir8_1_reservoir_taped", '2')
    p50m.transfer(0, reservoir.wells_by_name()[
     'A1'], reservoir.wells_by_name()['A1'], trash=False)

    # transfer 5 ul DNA template to pcr plate
    for index, column in enumerate(pcr_plate.columns()[:num_cols]):
        p20m.pick_up_tip()
        p20m.aspirate(
         5, dna_template.columns()[index][0].bottom(clearance_aspirate))
        p20m.move_to(dna_template.columns()[index][0].top(z=10))
        ctx.delay(seconds=2)
        p20m.dispense(5, column[0].bottom(clearance_dispense))
        p20m.drop_tip()
