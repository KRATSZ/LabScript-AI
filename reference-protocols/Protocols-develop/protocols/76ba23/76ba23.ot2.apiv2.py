from opentrons.protocol_api.labware import OutOfTipsError
import math

metadata = {
    'protocolName': 'DNA extraction',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    ctx.set_rail_lights(True)

    [engage_time, clearance_reservoir, labware_reservoir, set_tip_max,
     dry_time, choose_tip_rack, uploaded_csv] = get_values(  # noqa: F821
        "engage_time", "clearance_reservoir", "labware_reservoir",
        "set_tip_max", "dry_time", "choose_tip_rack", "uploaded_csv")

    # define constant values
    increment_vol = 250
    baseline_vol = 500

    # sample volume from manifest
    ml_line = uploaded_csv.splitlines()[3]
    sample_volume = int(float(ml_line[
     ml_line.find(',')+1:ml_line.find(' ml')])*1000)

    # tips (capacity 200 ul if filter tips, otherwise 300 ul)
    tips_300 = [ctx.load_labware(choose_tip_rack, slot) for slot in ['6', '9']]

    # keep tip useage between full and half volume capacity
    tip_capacity = tips_300[0].wells_by_name()['A1'].max_volume
    tip_max = tip_capacity
    if set_tip_max is not None:
        if 0.5*tip_capacity < set_tip_max < tip_capacity:
            tip_max = set_tip_max

    # p300 multi
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips_300)

    # primary DNA extraction plate in slot 2
    dna_extraction_plates = [ctx.load_labware(
     "usascientific_96_wellplate_2.4ml_deep", '2')]

    # slot 1 first for sample plate, later for water
    sample_plate = deep_well = ctx.load_labware(
     "usascientific_96_wellplate_2.4ml_deep", '1')

    # slot 3 first for premix, then wash, then ethanol
    reagent_reservoir = ctx.load_labware(labware_reservoir, '3')
    premix = wash = etoh = reagent_reservoir.wells()[0]

    # waste reservoir
    reservoir = ctx.load_labware(labware_reservoir, '11')
    waste = reservoir.wells()[0]

    # pcr plate for eluate in slot 10
    elution_plate = ctx.load_labware(
     "nest_96_wellplate_100ul_pcr_full_skirt", '10')

    # magnetic module with magnets disengaged, function to remove waste
    mag = ctx.load_module('magnetic module', '7')
    mag.disengage()
    mag_plate = mag.load_labware('usascientific_96_wellplate_2.4ml_deep')
    mag_height = {
        'omni_96_wellplate_2000ul': 8.5,
        'nest_96_wellplate_2ml_deep': 8.5,
        'usascientific_96_wellplate_2.4ml_deep': 8.5
        }

    # volume of sample and premix to be dispensed to primary extraction plate
    vol_increments = math.floor((sample_volume - baseline_vol) / increment_vol)
    if vol_increments > 4:
        vol_increments = 4
    vol_primary = baseline_vol + ((vol_increments in [1, 3, 4])*increment_vol)
    if vol_primary == 500:
        premix_vol = 633
    else:
        premix_vol = 950

    # duplicate extraction plate in slot 5 if sample volume >= 1.0 mL
    dna_extraction_plate = dna_extraction_plates[0]
    if sample_volume >= 1000:
        dna_extraction_plates.append(ctx.load_labware(
         "usascientific_96_wellplate_2.4ml_deep", '5'))
        duplicate_extraction_plate = dna_extraction_plates[1]
        vol_duplicate = baseline_vol + ((vol_increments in [4])*increment_vol)
        if vol_duplicate == 500:
            duplicate_premix_vol = 633
        else:
            duplicate_premix_vol = 950

    # helper functions
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

    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    def pick_up_or_refill(current_pipette):
        try:
            current_pipette.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             "Please Refill the {} Tip Boxes".format(current_pipette))
            current_pipette.reset_tipracks()
            current_pipette.pick_up_tip()

    def pre_wet(volume, location):
        for rep in range(2):
            p300m.aspirate(volume, location)
            p300m.dispense(volume, location)

    def etoh_settings():
        p300m.flow_rate.dispense = 300
        p300m.flow_rate.blow_out = 300

    def default_settings():
        p300m.flow_rate.dispense = 94
        p300m.flow_rate.blow_out = 300

    def viscous_settings():
        p300m.flow_rate.aspirate = 60
        p300m.flow_rate.dispense = 60
        p300m.flow_rate.blow_out = 300

    def aqueous_settings():
        p300m.flow_rate.aspirate = 60
        p300m.flow_rate.dispense = 60
        p300m.flow_rate.blow_out = 300

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

    def add_reagent(
     origin, target, add_vol, change_freq, current_pipette=p300m):
        for index, column in enumerate(target.columns()):
            if index == 0:
                pick_up_or_refill(current_pipette)
            change_every_n(current_pipette, index, change_freq)
            rep_max_transfer(add_vol, origin, column[0].top())
        p300m.drop_tip()

    def remove_waste(waste_vol, change_freq):
        for index, column in enumerate(mag_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            rep_max_transfer(
             waste_vol, column[0], waste.top(), blow=3, blow_delay=1)
        p300m.drop_tip()

    # mix premix and distribute to DNA extraction plates
    change_freq = 4  # adjust tip change frequency here
    viscous_settings()
    set_default_clearances(p300m, 4, 4)
    for index, plate in enumerate(dna_extraction_plates):
        pick_up_or_refill(p300m)
        p300m.mix(10, tip_max, premix)
        for j, column in enumerate(plate.columns()):
            change_every_n(p300m, j, change_freq)
            p300m.mix(5, tip_max, premix)
            if index == 0:
                rep_max_transfer(
                 premix_vol, premix, column[0].top(), asp_delay=1,
                 disp_delay=1, blow=1, touch=True)
            else:
                rep_max_transfer(
                 duplicate_premix_vol, premix, column[0].top(), asp_delay=1,
                 disp_delay=1, blow=1, touch=True)
        p300m.drop_tip()

    # sample to DNA extraction plates
    change_freq = 1  # adjust tip change frequency here
    aqueous_settings()
    set_default_clearances(p300m, 2, 2)
    for index, column in enumerate(sample_plate.columns()):
        if index == 0:
            pick_up_or_refill(p300m)
        change_every_n(p300m, index, change_freq)
        rep_max_transfer(
         vol_primary, column[0], dna_extraction_plate.columns()[
          index][0].top())
        if sample_volume >= 1000:
            rep_max_transfer(
             vol_duplicate, column[0],
             duplicate_extraction_plate.columns()[index][0].top())
            p300m.mix(
             5, tip_max, duplicate_extraction_plate.columns()[
              index][0].bottom(4))
            p300m.mix(5, tip_max, dna_extraction_plate.columns()[
             index][0].bottom(4))
        else:
            p300m.mix(5, tip_max, dna_extraction_plate.columns()[
             index][0].bottom(4))
    p300m.drop_tip()

    # manual steps
    pause_attention("""Paused for the following manual steps: (1)Seal the
    plates, then invert 10 times to mix, then on plate shaker 10 minutes. Spin.
    (2)Unseal the primary dna extraction plate and place it on the OT-2
    magnetic module (Slot 4). If a duplicate plate, unseal and place it back in
    its original deck slot. (3)Remove the premix reservoir from the OT-2 deck
    (Slot 3). Replace it with HKG DNA Wash Buffer 1 reservoir. (4)Remove the
    sample plate from the OT-2 deck (Slot 1). Replace it with a deep well plate
    containing water (in column 1) for the elution step. (5)Click resume in
    the OT app.""")

    # engage magnets 20 min (primary DNA extraction plate)
    mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
    ctx.delay(minutes=20)

    # remove sup, final traces of sup (primary DNA extraction plate)
    change_freq = 1  # adjust tip change frequency here
    viscous_settings()
    remove_waste(premix_vol + vol_primary, change_freq)
    remove_waste(50, change_freq)

    if sample_volume >= 1000:
        pause_attention("""Remove the primary plate from the magnetic module.
        Return it to its previous deck slot. Place the duplicate DNA extraction
        plate on the magnetic module.""")

        # engage magnets 20 min (duplicate dna extraction plate)
        mag.disengage()
        mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
        ctx.delay(minutes=20)

        # add 400 ul HKG DNA Wash Buffer 1 to primary dna extraction plate
        change_freq = 4  # adjust tip change frequency here
        aqueous_settings()
        set_default_clearances(p300m, 4, 4)
        add_reagent(wash, dna_extraction_plate, 400, change_freq)

        # remove sup, remaining traces of sup (duplicate DNA extraction plate)
        change_freq = 1  # adjust tip change frequency here
        set_default_clearances(p300m, 2, 2)
        remove_waste(duplicate_premix_vol + vol_duplicate, change_freq)
        remove_waste(50, change_freq)

        # suspend primary plate beads, move to duplicate wells to combine
        change_freq = 1  # adjust tip change frequency here
        viscous_settings()
        for index, column in enumerate(dna_extraction_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            p300m.mix(5, tip_max, column[0])
            rep_max_transfer(
             400, column[0], mag_plate.columns()[index][0].top(), asp_delay=1,
             disp_delay=1)
        p300m.drop_tip()

        # suspend with additional 100 ul HKG DNA Wash Buffer 1, combine
        change_freq = 1  # adjust tip change frequency here
        aqueous_settings()
        set_default_clearances(p300m, 4, 4)
        add_reagent(wash, dna_extraction_plate, 100, change_freq)

        change_freq = 1  # adjust tip change frequency here
        for index, column in enumerate(dna_extraction_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            p300m.mix(5, 50, column[0])
            p300m.aspirate(100, column[0])
            p300m.dispense(100, mag_plate.columns()[index][0])
        p300m.drop_tip()

    else:

        # add 400 ul wash to primary DNA extraction plate (on magnetic module)
        change_freq = 4  # adjust tip change frequency here
        aqueous_settings()
        set_default_clearances(p300m, 4, 4)
        add_reagent(wash, mag_plate, 400, change_freq)

    # suspend all beads in wash on magnetic module
    change_freq = 1  # adjust tip change frequency here
    viscous_settings()
    set_default_clearances(p300m, 2, 2)
    for index, column in enumerate(mag_plate.columns()):
        if index == 0:
            pick_up_or_refill(p300m)
        change_every_n(p300m, index, change_freq)
        p300m.mix(5, tip_max, column[0])
    p300m.drop_tip()

    mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
    ctx.delay(minutes=engage_time)

    # remove sup
    change_freq = 1  # adjust tip change frequency here
    aqueous_settings()
    if sample_volume >= 1000:
        remove_waste(500, change_freq)
    else:
        remove_waste(400, change_freq)

    # add 2nd wash 400 ul all beads
    change_freq = 4  # adjust tip change frequency here
    set_default_clearances(p300m, 4, 4)
    add_reagent(wash, mag_plate, 400, change_freq)

    mag.disengage()

    # mix 2nd wash with beads
    change_freq = 1  # adjust tip change frequency here
    set_default_clearances(p300m, 2, 2)
    for index, column in enumerate(mag_plate.columns()):
        if index == 0:
            pick_up_or_refill(p300m)
        change_every_n(p300m, index, change_freq)
        p300m.mix(5, tip_max, column[0])
    p300m.drop_tip()

    mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
    ctx.delay(minutes=engage_time)

    # remove sup 2nd wash
    change_freq = 1  # adjust tip change frequency here
    remove_waste(400, change_freq)

    mag.disengage()

    # wash twice with 80 percent ethanol
    pause_attention("""Please remove the wash buffer reservoir from the OT-2
    deck (Slot 3) and replace it with the 80 percent ethanol reservoir.""")

    etoh_settings()
    set_default_clearances(p300m, 4, 4)
    change_freq = 4  # adjust tip change frequency here
    for rep in range(2):
        # add 80% etoh
        for index, column in enumerate(mag_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            pre_wet(150, etoh)
            rep_max_transfer(
             500, etoh, column[0].top(), air=15, blow=3, blow_delay=1,
             touch=True)
        p300m.drop_tip()

        # mix
        set_default_clearances(p300m, 2, 2)
        change_freq = 1  # adjust tip change frequency here
        for index, column in enumerate(mag_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            p300m.mix(5, tip_max, column[0])
        p300m.drop_tip()

        mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
        ctx.delay(minutes=engage_time)

        # remove sup
        change_freq = 1  # adjust tip change frequency here
        for index, column in enumerate(mag_plate.columns()):
            if index == 0:
                pick_up_or_refill(p300m)
            change_every_n(p300m, index, change_freq)
            rep_max_transfer(
             500, column[0], waste.top(), air=15, blow=3, blow_delay=1)
        p300m.drop_tip()

    # remove remaining traces of sup
    change_freq = 1  # adjust tip change frequency here
    for index, column in enumerate(mag_plate.columns()):
        if index == 0:
            pick_up_or_refill(p300m)
        change_every_n(p300m, index, change_freq)
        rep_max_transfer(
         50, column[0], waste.top(), air=15, blow=3, blow_delay=1)
    p300m.drop_tip()

    # air dry
    mag.disengage()
    ctx.delay(minutes=dry_time)

    pause_attention("""Replenish both tip boxes.""")
    p300m.reset_tipracks()

    # elution: add water, mix
    aqueous_settings()
    water = deep_well.columns_by_name()['1'][0]
    p300m.distribute(
     23, water, [column[0].top() for column in mag_plate.columns()])
    for index, column in enumerate(mag_plate.columns()):
        p300m.pick_up_tip()
        p300m.mix(5, 18, column[0])
        p300m.move_to(column[0].bottom(4))
        p300m.blow_out()
        p300m.drop_tip()

    mag.engage(height=mag_height['usascientific_96_wellplate_2.4ml_deep'])
    ctx.delay(minutes=engage_time)

    pause_attention("""Replenish both tip boxes.""")
    p300m.reset_tipracks()

    # recover eluate to pcr plate
    p300m.transfer(
     23, [column[0].bottom(1) for column in mag_plate.columns()],
     [column[0].bottom(2) for column in elution_plate.columns()],
     new_tip='always')
    mag.disengage()
