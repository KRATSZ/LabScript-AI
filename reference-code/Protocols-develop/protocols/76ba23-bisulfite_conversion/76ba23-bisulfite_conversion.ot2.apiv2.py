from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': 'Bisulfite Conversion',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    ctx.set_rail_lights(True)

    [labware_p300_tips, labware_pcr_plate, labware_reservoir,
     labware_collect_plate, engage_time, clearance_reservoir,
     clearance_pcr_plate, clearance_deep_well, clearance_eluate,
     set_tip_max] = get_values(  # noqa: F821
     "labware_p300_tips", "labware_pcr_plate", "labware_reservoir",
     "labware_collect_plate", "engage_time", "clearance_reservoir",
     "clearance_pcr_plate", "clearance_deep_well", "clearance_eluate",
     "set_tip_max")

    # tips (capacity 200 ul if filter tips, otherwise 300 ul)
    tips300 = [
     ctx.load_labware(labware_p300_tips, str(slot)) for slot in [6, 9]]

    # keep tip useage between full and half volume capacity
    tip_capacity = tips300[0].wells_by_name()['A1'].max_volume
    tip_max = tip_capacity
    if set_tip_max is not None:
        if 0.5*tip_capacity < set_tip_max < tip_capacity:
            tip_max = set_tip_max

    # p300 multi
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # helper functions
    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    def change_tips(current_pipette):
        current_pipette.drop_tip()
        pick_up_or_refill(current_pipette)

    def change_every_n(current_pipette, j, change_freq):
        if ((j % change_freq == 0) and (j != 0)):
            change_tips(current_pipette)

    def set_default_clearances(
     current_pipette, aspirate_setting, dispense_setting):
        if 0 < aspirate_setting < 5 and 0 < dispense_setting < 5:
            current_pipette.well_bottom_clearance.aspirate = aspirate_setting
            current_pipette.well_bottom_clearance.dispense = dispense_setting

    def restore_default_clearances(current_pipette):
        current_pipette.well_bottom_clearance.aspirate = 1
        current_pipette.well_bottom_clearance.dispense = 1

    def pick_up_or_refill(current_pipette):
        try:
            current_pipette.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             "Please Refill the {} Tip Boxes".format(current_pipette))
            current_pipette.reset_tipracks()
            current_pipette.pick_up_tip()

    def pre_wet(current_pipette, volume, location):
        for rep in range(2):
            current_pipette.aspirate(volume, location)
            current_pipette.dispense(volume, location)

    def etoh_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2' or
           current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 92.86
            current_pipette.flow_rate.dispense = 300
            current_pipette.flow_rate.blow_out = 300
        elif (current_pipette.name == 'p20_multi_gen2' or
              current_pipette.name == 'p20_single_gen2'):
            current_pipette.flow_rate.aspirate = 7.56
            current_pipette.flow_rate.dispense = 22
            current_pipette.flow_rate.blow_out = 22

    def default_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2' or
           current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 92.86
            current_pipette.flow_rate.dispense = 92.86
            current_pipette.flow_rate.blow_out = 92.86
        elif (current_pipette.name == 'p20_multi_gen2' or
              current_pipette.name == 'p20_single_gen2'):
            current_pipette.flow_rate.aspirate = 7.56
            current_pipette.flow_rate.dispense = 7.56
            current_pipette.flow_rate.blow_out = 7.56

    def viscous_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2' or
           current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 60
            current_pipette.flow_rate.dispense = 60
            current_pipette.flow_rate.blow_out = 300
        elif (current_pipette.name == 'p20_multi_gen2' or
              current_pipette.name == 'p20_single_gen2'):
            current_pipette.flow_rate.aspirate = 3.5
            current_pipette.flow_rate.dispense = 3.5
            current_pipette.flow_rate.blow_out = 3.5

    def aqueous_flow_rates(current_pipette):
        if (current_pipette.name == 'p300_multi_gen2' or
           current_pipette.name == 'p300_single_gen2'):
            current_pipette.flow_rate.aspirate = 60
            current_pipette.flow_rate.dispense = 60
            current_pipette.flow_rate.blow_out = 300
        elif (current_pipette.name == 'p20_multi_gen2' or
              current_pipette.name == 'p20_single_gen2'):
            current_pipette.flow_rate.aspirate = 7.56
            current_pipette.flow_rate.dispense = 7.56
            current_pipette.flow_rate.blow_out = 7.56

    def rep_max_transfer(
     remaining, source, dest, tip_max_vol=tip_max, air=0, blow=0, touch=False,
     asp_delay=0, disp_delay=0, blow_location="destination", blow_delay=0):
        vol = tip_max_vol - air
        while remaining > vol:
            p300m.aspirate(vol, source)
            if air > 0:
                p300m.air_gap(air)
            else:
                if asp_delay > 0:
                    ctx.delay(seconds=asp_delay)
            p300m.dispense(tip_max_vol, dest)
            if disp_delay > 0:
                ctx.delay(seconds=disp_delay)
            if blow > 0:
                for rep in range(blow):
                    if rep > 0:
                        p300m.aspirate(tip_max, dest)
                    ctx.delay(seconds=blow_delay)
                    if blow_location == "destination":
                        p300m.blow_out(dest)
                    else:
                        p300m.blow_out(blow_location)
            if touch is True:
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
            remaining -= vol
        p300m.aspirate(remaining, source)
        if air > 0:
            p300m.air_gap(air)
        else:
            if asp_delay > 0:
                ctx.delay(seconds=asp_delay)
        p300m.dispense(remaining + air, dest)
        if disp_delay > 0:
            ctx.delay(seconds=disp_delay)
        if blow > 0:
            for rep in range(blow):
                if rep > 0:
                    p300m.aspirate(tip_max, dest)
                ctx.delay(seconds=blow_delay)
                if blow_location == "destination":
                    p300m.blow_out(dest)
                else:
                    p300m.blow_out(blow_location)
        if touch is True:
            p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)

    pause_attention("""
    Deck set up for bisulfite conversion:

    magnetic module in deck slot 7
    with deep well plate (collection plate)

    cf DNA in deck slot 1
    CT rxn plate in deck slot 2
    eluate plate in deck slot 10

    reagent reservoir in deck slot 3:
    A1 - CT conversion buffer
    A2 - Beads
    A3 - Water

    wash reservoir in deck slot 5
    desulph reservoir in deck slot 8
    waste reservoir in deck slot 11

    p300 tips in deck slots 6 and 9
    """)

    mag = ctx.load_module('magnetic module', '7')
    mag.disengage()
    mag_plate = mag.load_labware(labware_collect_plate, "Collection Plate")
    mag_height = {
        'omni_96_wellplate_2000ul': 8.5,
        'nest_96_wellplate_2ml_deep': 8.5,
        'usascientific_96_wellplate_2.4ml_deep': 8.5
        }

    cf_dna, pcr_plate, barcoded_pcr_plate = [
     ctx.load_labware(labware_pcr_plate, str(slot), display_name) for slot,
     display_name in zip([1, 2, 10], ["CF DNA", "CT Rxn Plate", "Eluate"])]

    trough = ctx.load_labware(
     "nest_12_reservoir_15ml", '3', 'Reagent Reservoir(CT conv,Beads,Water)')
    ct_conv, beads_mm, water = [
     trough.wells_by_name()[well_name] for well_name in ['A1', 'A2', 'A3']]

    wash_reservoir, desulph_reservoir, waste_reservoir = [ctx.load_labware(
     labware_reservoir, str(slot), display_name) for slot, display_name in zip(
     [5, 8, 11], ["Wash Buffer", "Desulph Buffer", "Waste"])]
    wash, desulph, waste = [labware.wells()[0] for labware in [
     wash_reservoir, desulph_reservoir, waste_reservoir]]

    ctx.comment("""
    add CT conversion buffer to pcr plate
    add cf DNA
    mix
    """)
    aqueous_flow_rates(p300m)
    p300m.pick_up_tip()
    p300m.transfer(
     130, ct_conv.bottom(clearance_reservoir), [
      column[0].bottom(clearance_pcr_plate) for column in pcr_plate.columns(
      )], new_tip='never')
    p300m.drop_tip()

    p300m.transfer(
     20, [column[0].bottom(clearance_pcr_plate) for column in cf_dna.columns(
     )], [column[0].bottom(5) for column in pcr_plate.columns(
     )], mix_after=(4, 75), new_tip='always')

    pause_attention("""
    paused for thermocycler steps
    when finished, return the pcr plate to its deck slot
    replenish tip racks
    resume
    """)
    p300m.reset_tipracks()

    ctx.comment("""
    bead-buffer mix and cycler product to collect plate (on magnetic module)
    """)
    viscous_flow_rates(p300m)
    for index, column in enumerate(pcr_plate.columns()):
        p300m.pick_up_tip()
        p300m.mix(10, tip_max, beads_mm.bottom(clearance_reservoir))
        rep_max_transfer(610, beads_mm.bottom(
         clearance_reservoir), mag_plate.columns()[index][0].bottom(
         clearance_deep_well), asp_delay=1, disp_delay=1, blow=3,
         blow_delay=1, touch=True)
        p300m.transfer(150, column[0].bottom(
         clearance_pcr_plate), mag_plate.columns()[index][0].bottom(
         clearance_deep_well), mix_after=(5, tip_max), new_tip='never')
        p300m.blow_out(mag_plate.columns()[index][0].top())
        ctx.delay(seconds=1)
        p300m.aspirate(tip_max, mag_plate.columns()[index][0].top())
        p300m.blow_out(mag_plate.columns()[index][0].top())
        p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
        p300m.drop_tip()
    aqueous_flow_rates(p300m)

    mag.engage(height=mag_height[labware_collect_plate])
    ctx.delay(engage_time)

    ctx.comment("""
    remove supernatant
    """)
    for column in mag_plate.columns():
        p300m.pick_up_tip()
        rep_max_transfer(760, column[0].bottom(
         clearance_deep_well), waste.top(), blow=3, blow_delay=1)
        p300m.drop_tip()

    mag.disengage()

    for rep in range(3):
        ctx.comment("""
        add wash (contains ethanol)
        """)
        etoh_flow_rates(p300m)
        change_freq = 1  # tip change frequency for this code section
        for index, column in enumerate(mag_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            pre_wet(p300m, tip_max, wash.bottom(clearance_reservoir))
            rep_max_transfer(400, wash.bottom(
             clearance_reservoir), column[0].top(), air=15,
             blow=3, blow_delay=1)
            if change_freq == 1:
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
        p300m.drop_tip()
        ctx.comment("""
        mix
        """)
        for column in mag_plate.columns():
            pick_up_or_refill(p300m)
            p300m.mix(4, tip_max, column[0].bottom(clearance_deep_well))
            p300m.blow_out(column[0].top())
            ctx.delay(seconds=1)
            p300m.aspirate(tip_max, column[0].top())
            p300m.blow_out(column[0].top())
            p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
            p300m.drop_tip()

        mag.engage(height=mag_height[labware_collect_plate])
        ctx.delay(engage_time)
        ctx.comment("""
        remove sup
        """)
        for column in mag_plate.columns():
            pick_up_or_refill(p300m)
            rep_max_transfer(400, column[0].bottom(
             clearance_deep_well), waste.top(), air=15, blow=3, blow_delay=1)
            p300m.drop_tip()

        mag.disengage()

        if rep == 0:
            ctx.comment("""
            add desulphonation buffer
            """)
            aqueous_flow_rates(p300m)
            pick_up_or_refill(p300m)
            for column in mag_plate.columns():
                rep_max_transfer(200, desulph.bottom(
                 clearance_reservoir), column[0].bottom(clearance_deep_well),
                 blow=3, blow_delay=1)
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
            p300m.drop_tip()
            ctx.comment("""
            mix
            """)
            for column in mag_plate.columns():
                pick_up_or_refill(p300m)
                p300m.mix(4, 100, column[0].bottom(clearance_deep_well))
                p300m.blow_out(column[0].top())
                ctx.delay(seconds=1)
                p300m.aspirate(tip_max, column[0].top())
                p300m.blow_out(column[0].top())
                p300m.touch_tip(radius=0.75, v_offset=-2, speed=20)
                p300m.drop_tip()

            ctx.delay(minutes=11)

            mag.engage(
             height=mag_height[labware_collect_plate])
            ctx.delay(engage_time)
            ctx.comment("""
            remove sup
            """)
            for column in mag_plate.columns():
                pick_up_or_refill(p300m)
                rep_max_transfer(200, column[0].bottom(
                 clearance_deep_well), waste.top(), blow=3, blow_delay=1)
                p300m.drop_tip()

            mag.disengage()

    pause_attention("""
    Please dry the magnetic module plate for 20 min at 55 C.
    Replenish tip racks.
    Then return the plate to the magnetic module
    and click resume.""")

    ctx.comment("""
    add water to dried beads
    """)
    p300m.reset_tipracks()
    p300m.transfer(25, water.bottom(
     clearance_reservoir), [column[0].bottom(
      clearance_deep_well) for column in mag_plate.columns()],
      new_tip='always')

    pause_attention("""
    Please incubate the magnetic module plate for 4 min at 55 C
    to elute. Then place it back on the magnetic module. Please
    replace the used tip boxes with fresh tips to transfer the
    eluate.""")

    mag.engage(height=mag_height[labware_collect_plate])
    ctx.delay(engage_time)
    ctx.comment("""
    transfer eluate to barcoded PCR plate
    """)
    p300m.transfer(25, [column[0].bottom(
     clearance_eluate) for column in mag_plate.columns()], [column[0].bottom(
      clearance_pcr_plate) for column in barcoded_pcr_plate.columns()],
      new_tip='always')
