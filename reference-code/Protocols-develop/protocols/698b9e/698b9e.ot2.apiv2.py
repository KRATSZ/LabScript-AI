metadata = {
    'protocolName': 'PCR Prep with 1.5 mL Tubes Part 1 - Plate Filling',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_plates, reagent, p20_mount,
        p300_mount] = get_values(  # noqa: F821
        "num_plates", "reagent", "p20_mount", "p300_mount")

    if not 1 <= num_plates <= 10:
        raise Exception("Enter a plate number 1-9")

    plate_slots = [str(num) for num in range(3, 3+num_plates)]

    if reagent == 'buffer':
        plate = 'nunc_96_wellplate_450ul'
        tips = 'opentrons_96_filtertiprack_200ul'
        pipette = 'p300_multi_gen2'
        mount = p300_mount
        reagent_vol = 80

    elif reagent == 'mastermix':
        plate = 'microamp_96_wellplate_100ul'
        tips = 'opentrons_96_filtertiprack_20ul'
        pipette = 'p20_single_gen2'
        mount = p20_mount
        reagent_vol = 7.6
        airgap = 3

    # load labware
    plates = [ctx.load_labware(plate, slot) for slot in plate_slots]
    tiprack = [ctx.load_labware(tips, '2')]
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '1')

    # load instruments
    pip = ctx.load_instrument(pipette, mount, tip_racks=tiprack)

    # distribute mastermix
    if reagent == 'buffer':
        pip.pick_up_tip()
        for i, plate in enumerate(plates):
            for col in plate.rows()[0]:
                pip.aspirate(reagent_vol, reservoir.wells()[i])
                pip.dispense(reagent_vol, col)
                pip.blow_out()
                pip.touch_tip()
        pip.drop_tip()

    elif reagent == 'mastermix':
        wells = [well for plate in plates for well in plate.wells()]
        chunks = [wells[i:i+2] for i in range(0, len(wells), 2)]
        pip.pick_up_tip()
        for chunk in chunks:
            pip.aspirate(reagent_vol, reservoir.wells()[0])
            pip.air_gap(airgap)
            pip.aspirate(reagent_vol, reservoir.wells()[0])
            pip.touch_tip()
            for well in chunk:
                pip.dispense(reagent_vol+airgap, well)
                pip.touch_tip()
        pip.drop_tip()
