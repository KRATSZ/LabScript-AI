metadata = {
    'protocolName': 'PCR 1',
    'author': 'Steve <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    ctx.set_rail_lights(True)

    # uploaded parameter values
    [choose_tip_rack, uploaded_csv] = get_values(  # noqa: F821
        "choose_tip_rack", "uploaded_csv")

    # sample type from manifest
    type_line = uploaded_csv.splitlines()[2]
    sample_type = type_line[type_line.find('(')+1:type_line.find(')')]

    # tips and p300 multi
    tips300 = [
     ctx.load_labware(choose_tip_rack, str(slot)) for slot in [6, 9, 8, 11]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    # magnetic module with magnets disengaged
    mag = ctx.load_module('magnetic module gen2', '4')
    mag.disengage()
    mag_plate = mag.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")

    # labware, CT converted cf DNA (barcoded pcr plate) in slot 1
    [barcoded_pcr_plate, pcr1_mm_plate, pcr_plate, trough, etoh_reservoir] = [
     ctx.load_labware(labware, slot) for labware, slot in zip(
        ["nest_96_wellplate_100ul_pcr_full_skirt",
         "corning_96_wellplate_360ul_flat",
         "nest_96_wellplate_100ul_pcr_full_skirt", "nest_12_reservoir_15ml",
         "nest_1_reservoir_195ml"],
        [str(num) for num in [1, 3, 2, 5, 7]])]

    # PCR 1 master mix in slot 3
    pcr1_mm = pcr1_mm_plate.columns_by_name()['1'][0]

    # beads, water, waste in wells A1, A2, A3 of trough in slot 5
    beads, water, waste = [trough.wells_by_name()[
     well_name] for well_name in ['A1', 'A2', 'A3']]

    # ethanol reservoir in slot 7
    etoh = etoh_reservoir.wells()[0]

    # helper function to reuse tips
    def reuse_tips(which_tips):
        p300m.reset_tipracks()
        p300m.starting_tip = which_tips

    # transfer bisulfite converted sample DNA and master mix to PCR plate
    p300m.distribute(
     23, pcr1_mm, [column[0] for column in pcr_plate.columns()])
    p300m.transfer(
     2, [column[0] for column in barcoded_pcr_plate.columns()],
     [column[0] for column in pcr_plate.columns()],
     new_tip='always', mix_after=(4, 15))

    if sample_type == "saliva":
        ctx.pause("""Please proceed to PCR1 thermocycling.
                     When cycling is finished, proceed to the PCR2 step.""")
    else:
        ctx.pause("""Pause for PCR1 thermocycling.
                     Be sure to return the plate to the magnetic module when
                     cycling is finished to proceed with PCR1 clean up steps.
                     Please replenish the used tips and then click resume.""")

        # add pre-warmed beads
        p300m.reset_tipracks()
        p300m.transfer(
         45, beads, [column[0] for column in mag_plate.columns()],
         mix_after=(4, 35), new_tip='always', trash=False)

        mag.engage()
        ctx.delay(minutes=5)

        # remove sup
        p300m.reset_tipracks()
        p300m.transfer(
         70, [column[0] for column in mag_plate.columns()],
         waste, new_tip='always', trash=False)

        # add 70 percent etoh keep magnets engaged, remove sup, repeat
        etoh_tips = tips300[1].next_tip()
        for rep in range(2):
            reuse_tips(etoh_tips)
            p300m.pick_up_tip()
            p300m.transfer(
             150, etoh, [column[0].top() for column in mag_plate.columns()],
             air_gap=25, new_tip='never')
            p300m.return_tip()
            ctx.delay(seconds=15)
            p300m.reset_tipracks()
            p300m.transfer(
             150, [column[0].top() for column in mag_plate.columns()], waste,
             air_gap=25, new_tip='always', Trash=False)

        # air dry beads
        ctx.delay(minutes=10)

        # add water, mix, and recover
        water_tips = tips300[2].next_tip()
        recovery_tips = tips300[3].next_tip()
        reuse_tips(water_tips)
        p300m.pick_up_tip()
        p300m.distribute(
         25, water, [column[0].top() for column in mag_plate.columns()],
         new_tip='never')
        p300m.return_tip()
        reuse_tips(water_tips)
        for column in mag_plate.columns():
            p300m.pick_up_tip()
            p300m.mix(4, 15, column[0])
            p300m.drop_tip()
        reuse_tips(recovery_tips)
        ctx.pause("Please add a fresh barcoded pcr plate to deck slot 1.")
        p300m.transfer(
         25, [column[0] for column in mag_plate.columns()],
         [column[0] for column in barcoded_pcr_plate.columns()],
         new_tip='always')
