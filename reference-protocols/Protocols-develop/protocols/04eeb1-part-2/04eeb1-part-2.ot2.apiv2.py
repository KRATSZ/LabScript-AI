from opentrons import types

metadata = {
    'protocolName': 'Illumina COVIDSeq Test: Synthesize First Strand cDNA',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [m20_mount, reservoir_type, plate_1_cols,
        plate_2_cols, temperature] = get_values(  # noqa: F821
        "m20_mount", "reservoir_type", "plate_1_cols", "plate_2_cols",
        "temperature")

    # Labware
    tips200ul = [ctx.load_labware('opentrons_96_filtertiprack_20ul',
                 slot) for slot in [10, 7]]
    temp_mod = ctx.load_module('temperature module gen2', 1)
    reservoir = temp_mod.load_labware(reservoir_type, "Master Mix Reservoir")
    plate_1 = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 11, "Plate 1")
    plate_2 = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 8, "Plate 2")

    # Pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tips200ul)

    # Wells
    plate_1_wells = plate_1.rows()[0]
    plate_2_wells = plate_2.rows()[0]
    mm = reservoir['A1']

    # Helper Functions
    def includeCols(includedCols, plateCols):
        included_cols = []
        if includedCols != "":
            included_cols = [int(i)-1 for i in includedCols.split(",")]
            dests = [col for i, col in enumerate(plateCols) if i
                     in included_cols]
            return dests

    def transfer(pipette, vol, src, dest):
        for well in dest:
            pipette.pick_up_tip()
            pipette.aspirate(vol, src)
            pipette.move_to(ctx.deck.position_for('4').move(types.Point(x=20,
                            y=31.5, z=100)))
            pipette.dispense(vol, well)
            pipette.drop_tip()

    # Protocol Steps
    temp_mod.set_temperature(temperature)
    transfer(m20, 8, mm, includeCols(plate_1_cols, plate_1_wells))
    if reservoir_type == 'biorad_96_wellplate_200ul_pcr':
        ctx.pause('''Please refill the master mix before continuing to Plate 2.
                Click Resume when ready.''')
    transfer(m20, 8, mm, includeCols(plate_2_cols, plate_2_wells))
