metadata = {
    'protocolName': 'Custom Sample Transfer',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [asp_speed, disp_speed, asp_height,
        disp_height] = get_values(  # noqa: F821
        "asp_speed", "disp_speed", "asp_height", "disp_height")

    asp_speed = float(asp_speed)
    disp_speed = float(disp_speed)
    asp_height = float(asp_height)
    disp_height = float(disp_height)

    # Load Labware
    plate1 = ctx.load_labware('waters_96_wellplate_2ml', 1, 'Plate 1')
    plate2 = ctx.load_labware('waters_96_wellplate_2ml', 2, 'Plate 2')
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', 4)

    # Load Pipette
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack])

    # Get sample columns
    plate1_wells = plate1.rows()[0]
    plate2_wells = plate2.rows()[0]

    # Flow Rates
    m300.flow_rate.aspirate = asp_speed
    m300.flow_rate.dispense = disp_speed

    # Pre-Wet Tip with 300 uL
    # Transfer 750 uL to Plate 2
    for p1_well, p2_well in zip(plate1_wells, plate2_wells):
        m300.pick_up_tip()
        for _ in range(3):
            m300.aspirate(300, p1_well.bottom(z=asp_height))
            m300.move_to(p1_well.top())
            m300.dispense(300, p1_well.bottom(z=disp_height))
        m300.transfer(750, p1_well.bottom(z=asp_height),
                      p2_well.bottom(z=disp_height), air_gap=30,
                      touch_tip=True,
                      blow_out=True, blowout_location='destination well',
                      new_tip='never')
        m300.drop_tip()
