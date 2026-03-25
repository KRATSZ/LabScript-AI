metadata = {
    'protocolName': 'Dinosaur',
    'author': 'Opentrons <protocols@opentrons.com>',
    'description': 'Draw a picture of a dinosaur',
    'apiLevel': '2.9'
}


def run(ctx):

    [p300_mount, tip_type, plate_type] = get_values(  # noqa: F821
        "p300_mount", "tip_type", "plate_type")

    # Load Labware
    tiprack = ctx.load_labware(tip_type, 6)
    plate = ctx.load_labware(plate_type, 3)
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 8)

    # Load Pipette
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tiprack])

    # Solutions
    green = reservoir['A1']
    blue = reservoir['A2']

    # Wells to dispense green
    green_wells = [well for well in plate.wells(
        'E1', 'D2', 'E2', 'D3', 'E3', 'F3', 'G3', 'H3',
        'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'C5', 'D5',
        'E5', 'F5', 'G5', 'C6', 'D6', 'E6', 'F6', 'G6',
        'C7', 'D7', 'E7', 'F7', 'G7', 'D8', 'E8', 'F8',
        'G8', 'H8', 'E9', 'F9', 'G9', 'H9', 'F10', 'G11',
        'H12')]

    # Wells to dispense blue
    blue_wells = [well for well in plate.wells(
                  'C3', 'B4', 'A5', 'B5', 'B6', 'A7', 'B7',
                  'C8', 'C9', 'D9', 'E10', 'E11', 'F11', 'G12')]

    # Distribute green solution to wells
    p300.distribute(50, green, green_wells, disposal_vol=0, blow_out=True)
    # Distribute blue solution to wells
    p300.distribute(50, blue, blue_wells, disposal_vol=0, blow_out=True)
