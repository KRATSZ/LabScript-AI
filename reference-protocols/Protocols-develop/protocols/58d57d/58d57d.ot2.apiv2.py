metadata = {
    'protocolName': 'Promega ADP-Glo Kinase Assay',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [samples, liquid_A_vol, liquid_B_vol, liquid_C_vol,
        liquid_D_vol] = get_values(  # noqa: F821
        "samples", "liquid_A_vol", "liquid_B_vol",
        "liquid_C_vol", "liquid_D_vol")

    # Load Labware
    plate = ctx.load_labware("greiner_384_wellplate_130ul", 1)
    tiprack = ctx.load_labware("opentrons_96_tiprack_20ul", 2)
    tuberack = ctx.load_labware(
                "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", 4)

    # Load Pipette
    p20 = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[tiprack])

    # Get wells by row
    sample_wells = [well for wells in plate.rows() for well in wells][:samples]

    # Reagents
    liquid_A = tuberack['A1']
    liquid_B = tuberack['B1']
    liquid_C = tuberack['C1']
    liquid_D = tuberack['D1']

    p20.transfer(liquid_A_vol, liquid_A, sample_wells, touch_tip=True)
    ctx.pause("Centrifuge Plate to Mix Liquid A")

    p20.transfer(liquid_B_vol, liquid_B, sample_wells, touch_tip=True)
    ctx.pause("Centrifuge Plate and Incubate for 60 minutes")

    p20.transfer(liquid_C_vol, liquid_C, sample_wells, touch_tip=True)
    ctx.pause("Incubate for 40 minutes")

    p20.transfer(liquid_D_vol, liquid_D, sample_wells, touch_tip=True)
    ctx.pause("Incubate for 30 minutes")
