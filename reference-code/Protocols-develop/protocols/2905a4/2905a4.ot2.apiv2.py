from opentrons import types, protocol_api
from opentrons.types import Point


metadata = {
    'protocolName': 'RNA Purification with Magnetic Beads',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [samples, starting_well, p300_mount, tc_temp,
        engage_height, side_x_radius, super_asp_rate,
        super_disp_rate] = get_values(  # noqa: F821
        "samples", "starting_well", "p300_mount", "tc_temp", "engage_height",
        "side_x_radius", "super_asp_rate", "super_disp_rate")

    # Load Labware
    tc_mod = ctx.load_module('thermocycler')
    tc_plate = tc_mod.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt',
                    'Origin RNA Sample Plate')
    tips200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in range(1, 4)]
    beads_rack = ctx.load_labware(
                    'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', 4)
    tuberack = ctx.load_labware(
                    'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 5)
    temp_mod = ctx.load_module('temperature module gen2', 6)
    temp_plate = temp_mod.load_labware(
                    'nest_96_wellplate_100ul_pcr_full_skirt',
                    'Recipient Cooled Plate')
    mag_mod = ctx.load_module('magnetic module gen2', 9)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep',
                                     'Mag Deck Plate')
    trash = ctx.loaded_labwares[12]['A1']

    # Load Pipette
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips200)

    # Pipette Tip Mapping
    all_tips = [tips200[i].wells() for i in range(len(tips200))]
    available_tips = [tip for tips in all_tips for tip in tips]

    # Reagents
    beads = beads_rack['A1']
    rfw = tuberack['A3']
    wb = tuberack['A4']
    rbb = tuberack['B3']

    # 96 Well Plate Map
    # Create a map of well names by index
    # (tc_plate is used as the reference 96 well plate)
    plate_well_positions = dict(zip(range(0, len(tc_plate.wells())),
                                tc_plate.wells()))
    # Retrieve well index by using well name
    starting_well_index = list(plate_well_positions.keys())[
                            list(plate_well_positions.values()).index(tc_plate[
                                starting_well])]

    # Sample Wells
    tc_plate_wells = tc_plate.wells()[
                        starting_well_index:starting_well_index+samples]
    mag_plate_wells = mag_plate.wells()[
                        starting_well_index:starting_well_index+samples]
    temp_plate_wells = temp_plate.wells()[
                        starting_well_index:starting_well_index+samples]
    sides = [-side_x_radius + (((n // 8) % 2) * side_x_radius*2)
             for n in range(96)]

    # Helper Functions
    def getWellSide(well, plate, custom_sides=None):
        index = plate.wells().index(well)
        if custom_sides:
            return custom_sides[index]
        return sides[index]

    def pick_up(pip, loc=None):
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
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

    def remove_supernatant(vol, src, dest, side, mode=None):
        if mode == 'elution':
            p300.flow_rate.aspirate = 10
        else:
            p300.flow_rate.aspirate = super_asp_rate
            p300.flow_rate.dispense = super_disp_rate
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

    # PROTOCOL STEPS
    # Set Thermocycler at 4C
    tc_mod.set_block_temperature(tc_temp)

    # Dilute Magnetic Beads (1)
    pick_up(p300, available_tips[0])
    for dest in mag_plate_wells:
        p300.aspirate(70, rfw.bottom(70))
        p300.dispense(70, dest.bottom(2))
        p300.blow_out()
    p300.return_tip()

    # 30uL of Magnetic Beads to Purification Plate (2)
    pick_up(p300, available_tips[0])
    for dest in mag_plate_wells:
        p300.flow_rate.dispense = 300
        p300.aspirate(30, beads.bottom(15))
        p300.dispense(30, dest.bottom(2))
        p300.mix(7, 75)
        p300.touch_tip()
        p300.blow_out()
    p300.return_tip()
    reset_flow_rates()

    # Recover beads (3)
    mag_mod.engage(height=engage_height)
    # Attracting beads (4)
    ctx.delay(minutes=2, msg='Attracting beads')

    # Remove supernatant (5)
    pick_up(p300, available_tips[0])
    for well in mag_plate_wells:
        remove_supernatant(120, well, trash, getWellSide(well, mag_plate))
    p300.drop_tip()
    available_tips.pop(0)

    # Setup Dedicated Tips
    dedicated_tips = dict(zip(range(samples), available_tips[:samples]))
    available_tips = available_tips[samples::]

    # Open Thermocycler Lid and Dilute Sample (7)
    tc_mod.open_lid()
    for i, dest in enumerate(tc_plate_wells):
        pick_up(p300, dedicated_tips[i])
        p300.flow_rate.dispense = 100
        p300.aspirate(80, rfw.bottom(60))
        p300.dispense(80, dest.bottom(1))
        p300.mix(3, 75)
        p300.touch_tip()
        p300.blow_out()
        p300.return_tip()
    reset_flow_rates()

    # Disengage Mag Deck (8)
    mag_mod.disengage()

    # Transfer Mixed Samples to Magnetic Beads and Mix (9)
    for i, (src, dest) in enumerate(zip(tc_plate_wells, mag_plate_wells)):
        pick_up(p300, dedicated_tips[i])
        p300.flow_rate.dispense = 300
        p300.aspirate(120, src.bottom(0.3))
        p300.dispense(120, dest.bottom(1))
        p300.mix(10, 80, dest.bottom(1).move(types.Point(x=-1*getWellSide(dest,
                 mag_plate))))
        p300.touch_tip()
        p300.blow_out()
        p300.return_tip()
    reset_flow_rates()

    # Add RBB to sample (10)
    pick_up(p300, available_tips[0])
    for dest in mag_plate_wells:
        p300.flow_rate.dispense = 300
        for _ in range(2):
            p300.aspirate(100, rbb.bottom(5))
            p300.air_gap(20)
            p300.dispense(120, dest.bottom(15))
            p300.blow_out()
    p300.drop_tip()
    available_tips.pop(0)
    reset_flow_rates()

    # Mix Beads with RBB + sample (11)
    for i, dest in enumerate(mag_plate_wells):
        p300.flow_rate.dispense = 300
        pick_up(p300, dedicated_tips[i])
        mix_loc = dest.bottom(1).move(Point(x=-1*getWellSide(dest, mag_plate)))
        p300.mix(10, 200, mix_loc)
        p300.blow_out()
        p300.return_tip()
    reset_flow_rates()

    # Shake Beads (12)
    ctx.pause('''Shake the beads on external shaker
              (first add PCR tape to close plate)''')

    # Recover beads (13)
    mag_mod.engage(height=engage_height)
    # Attracting beads (14)
    ctx.delay(minutes=10, msg='Attracting beads')

    # Remove Supernatant (15)
    for i, well in enumerate(mag_plate_wells):
        pick_up(p300, dedicated_tips[i])
        remove_supernatant(320, well, trash, getWellSide(well, mag_plate))
        p300.return_tip()

    # Disengage Mag Deck (16)
    mag_mod.disengage()

    # Add WB to Samples (17)
    pick_up(p300, available_tips[0])
    for dest in mag_plate_wells:
        p300.aspirate(200, wb.bottom(60))
        p300.dispense(200, dest.bottom(15))
        p300.blow_out()
    p300.drop_tip()
    available_tips.pop(0)

    # Mix Beads with WB + samples (18)
    for i, dest in enumerate(mag_plate_wells):
        p300.flow_rate.dispense = 300
        pick_up(p300, dedicated_tips[i])
        mix_loc = dest.bottom(1).move(Point(x=-1*getWellSide(dest,
                                            mag_plate)))
        p300.mix(7, 150, mix_loc)
        for _ in range(2):
            p300.blow_out(dest.top(-3))
            ctx.delay(seconds=3)
        p300.return_tip()
    reset_flow_rates()

    # Engage Magnet (19)
    mag_mod.engage(height=engage_height)
    # Extracting beads (20)
    ctx.delay(minutes=5, msg='Extracting beads from volume - 5 min')

    # Remove WB (21)
    for i, well in enumerate(mag_plate_wells):
        pick_up(p300, dedicated_tips[i])
        remove_supernatant(250, well, trash, getWellSide(well, mag_plate))
        p300.drop_tip()

    # Drying magnetic beads (22)
    ctx.delay(minutes=20, msg='Drying magnetic beads')

    # Disengage Mag Deck (23)
    mag_mod.disengage()

    # Setup New Dedicated Tips
    dedicated_tips.clear()
    dedicated_tips = dict(zip(range(samples), available_tips[:samples]))
    available_tips = available_tips[samples::]

    # Elution 1 (24)
    for i, dest in enumerate(mag_plate_wells):
        pick_up(p300, dedicated_tips[i])
        p300.flow_rate.dispense = 300
        p300.aspirate(50, rfw.bottom(60))
        p300.dispense(50, dest.bottom(1.5))
        mix_loc = dest.bottom(1).move(Point(x=-1*getWellSide(dest,
                                            mag_plate)))
        p300.mix(7, 40, mix_loc)
        p300.blow_out()
        p300.return_tip()
    reset_flow_rates()

    # Eluting RNA from Magnet (25)
    ctx.delay(minutes=5, msg='Eluting RNA from magnet')

    # Engage Magnet (26)
    mag_mod.engage(height=engage_height)
    # Extracting beads (27)
    ctx.delay(minutes=2)

    # Cool Temp Mod to 4C (28)
    temp_mod.start_set_temperature(4)

    # Setup Second Set of Dedicated Tips
    dedicated_tips_set2 = dict(zip(range(samples), available_tips[:samples]))
    available_tips = available_tips[samples::]

    # First Elution to Recipient Plate (29)
    for i, (src, dest) in enumerate(zip(mag_plate_wells, temp_plate_wells)):
        pick_up(p300, dedicated_tips_set2[i])
        remove_supernatant(55, src, dest, getWellSide(src, mag_plate),
                           'elution')
        p300.return_tip()
    reset_flow_rates()

    # Disengage Mag Deck (30)
    mag_mod.disengage()

    # Fresh RFW for Second Eluate (31)
    pick_up(p300, available_tips[0])
    for dest in mag_plate_wells:
        p300.aspirate(50, rfw.bottom(60))
        p300.dispense(50, dest.bottom(10))
        p300.blow_out()
    p300.drop_tip()
    available_tips.pop(0)

    # Mixing Beads with Second Elution Buffer (32)
    mix_sides = [-0.75 + (((n // 8) % 2) * 0.75*2)
                 for n in range(96)]
    for i, dest in enumerate(mag_plate_wells):
        p300.flow_rate.dispense = 300
        pick_up(p300, dedicated_tips[i])
        mix_loc = dest.bottom(1.5).move(Point(x=-1*getWellSide(dest, mag_plate,
                                        mix_sides)))
        p300.mix(7, 40, mix_loc)
        p300.touch_tip()
        p300.blow_out()
        p300.drop_tip()
    reset_flow_rates()

    # Second Elution Pause (33)
    ctx.delay(minutes=5, msg='Eluting RNA from beads')

    # Engage Magnet (34)
    mag_mod.engage(height=engage_height)
    # Extracting beads (35)
    ctx.delay(minutes=2, msg='Extracting beads')

    # Second Elution to Recipient Plate (36)
    temp_mod.await_temperature(4)
    for i, (src, dest) in enumerate(zip(mag_plate_wells, temp_plate_wells)):
        pick_up(p300, dedicated_tips_set2[i])
        remove_supernatant(55, src, dest, getWellSide(src, mag_plate),
                           'elution')
        p300.drop_tip()
    reset_flow_rates()

    # Deactivate All Modules
    mag_mod.disengage()
    tc_mod.deactivate()

    ctx.comment('Protocol Completed!')
