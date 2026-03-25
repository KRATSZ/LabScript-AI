# flake8: noqa
from opentrons.types import Point
metadata = {
    'protocolName': 'Dynabeads for IP Reagent-In-Plate Part 2',
    'author': '',
    'source': '',
    'apiLevel': '2.11'
}

########################

def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        'num_samples')

    [asp_height, length_from_side, p300_mount] = [0.5, 2.5, 'left']
    wash_volume = 200
    wash_times = 3

    total_cols = int(num_samples//8)
    r1 = int(num_samples%8)
    if r1 != 0: total_cols = total_cols + 1

    #########################

    # load labware
    wash_res = ctx.load_labware('nest_12_reservoir_15ml', '2', 'wash')
    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    temp_mod = ctx.load_module('temperature module gen2', '3')
    elution_plate = temp_mod.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul')
    reagent_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '4', 'reagents')
    #samples = ctx.load_labware('nest_96_wellplate_2ml_deep', '5', 'samples')
    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in ['6', '7', '8']]
    tiprack_reuse = ctx.load_labware('opentrons_96_tiprack_300ul', '5')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', '9', 'waste')

    # load pipette
    pip = ctx.load_instrument('p300_multi_gen2', p300_mount, tip_racks=tiprack)

    # liquids
    wash = wash_res.wells()[:total_cols]
    #beads = reagent_plate.rows()[0][0]
    #ab = reagent_plate.rows()[0][1]
    elution = reagent_plate.rows()[0][11]
    waste = waste_res.wells()[0]
    #samples = samples.rows()[0][:total_cols]
    working_cols = mag_plate.rows()[0][:total_cols]
    final_cols = elution_plate.rows()[0][:total_cols]

    def remove_supernatant(vol):
        ctx.comment('\n\n\n~~~~~~~~REMOVING SUPERNATANT~~~~~~~~\n')
        pip.pick_up_tip()
        pip.flow_rate.aspirate = 45
        for i, col in enumerate(working_cols):
            side = -1 if i % 2 == 0 else 1
            aspirate_loc = col.bottom(z=asp_height).move(
                            Point(x=(col.length/2-length_from_side)*side))
            pip.transfer(vol,
                         aspirate_loc,
                         waste.bottom(z=25),
                         new_tip='never'
                         # blow_out=True,
                         # blowout_location='destination well'
                         )
            # pip.blow_out()
        pip.flow_rate.aspirate = 92
        pip.drop_tip()

    def remove_residue(vol):
        ctx.comment('\n\n\n~~~~~~~~REMOVING RESIDUE~~~~~~~~\n')
        pip.flow_rate.aspirate = 45
        for i, col in enumerate(working_cols):
            side = -1 if i % 2 == 0 else 1
            aspirate_loc = col.bottom(z=asp_height).move(
                            Point(x=(col.length/2-length_from_side)*side))
            pip.pick_up_tip()
            pip.aspirate(vol, aspirate_loc)
            pip.drop_tip()
        pip.flow_rate.aspirate = 92

    # protocol
    mag_mod.disengage()
    ctx.pause('load sample plate')
    #temp_mod.set_temperature(70)
    mag_mod.engage(height_from_base=4.2)
    ctx.delay(minutes=2)
    remove_supernatant(250)
    mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~THREE WASHES~~~~~~~~\n')
    for i in range(3):
        ctx.comment('\n\n\n~~~~~~~~ADDING WASH~~~~~~~~\n')
        #pip.starting_tip = tiprack_reuse.well('A1')
        x = 0
        for wash_well, working_well in zip(wash, working_cols):
            pip.pick_up_tip(tiprack_reuse.well(x))
            pip.aspirate(200, wash_well)
            pip.dispense(200, working_well)
            pip.mix(10, 175, working_well, rate = 3)
            pip.return_tip()
            x = x+8
        mag_mod.engage(height_from_base=4.2)
        ctx.delay(minutes=1)
        remove_supernatant(200)
        if i == 2: remove_residue(50)

        mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~ADD ELUTION~~~~~~~~\n')
    pip.pick_up_tip()
    for col in working_cols:
        pip.aspirate(30, elution)
        pip.dispense(30, col.bottom(7.5))
        pip.blow_out()
        pip.touch_tip()
    pip.drop_tip()

    ctx.comment('\n\n\n~~~~~~~~MOVE ELUTE TO FINAL PLATE~~~~~~~~\n')
    for source_col, dest_col in zip(working_cols, final_cols):
        pip.pick_up_tip()
        pip.mix(10, 25, source_col)
        pip.aspirate(35, source_col.bottom(0.5), rate = 0.1)
        pip.dispense(35, dest_col)
        pip.blow_out()
        pip.drop_tip()

    ctx.pause('SEAL THE PLATE - 10 MINUTE INCUBATION AT 70C')
    temp_mod.set_temperature(70)
