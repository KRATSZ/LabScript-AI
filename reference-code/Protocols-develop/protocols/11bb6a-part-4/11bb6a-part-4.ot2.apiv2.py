import math

metadata = {
    'protocolName': '''NEBNext Quarter Volume Library Prep Step 4:
     Adapter Ligation''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_plates, labware_tempmod
     ] = get_values(  # noqa: F821
      'sample_count', 'labware_plates', 'labware_tempmod')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if sample_count < 48 or sample_count > 96:
        raise Exception('Number of samples must be 48-96.')

    # tips, p20 single, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [7, 10, 11]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [8]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module at 4 C with reagent tubes
    temp = ctx.load_module('Temperature Module', '1')
    block = temp.load_labware(
     labware_tempmod)
    [lig_mx, enhancer, mix_tube] = [
     block.wells_by_name()[name] for name in ['A1', 'A2', 'A3']]
    deadvol_tube = 10
    temp.set_temperature(4)

    ctx.load_module('magnetic module gen2', '9')

    reagent_plate = ctx.load_labware(
     labware_plates, '6', 'Reagent Plate')
    [user, adapter] = [reagent_plate.columns()[index] for index in [10, 11]]

    libraryprep_plate = ctx.load_labware(
     labware_plates, '3', 'Library Prep Plate')

    # ligation mix volume 60 uL per column of samples
    lig_mx.liq_vol = 1.1*60*num_cols + deadvol_tube

    # enhancer volume 2 uL per column of samples
    enhancer.liq_vol = 1.1*2*num_cols + deadvol_tube

    # user volume
    user[0].liq_vol = num_cols + 1

    # adapter volume
    adapter[0].liq_vol = num_cols + 1

    # mix tube volume
    mix_tube.liq_vol = 0

    # alert user to reagent volumes needed
    ctx.comment(
     "\n***\nEnsure reagents in sufficient volume are present on deck\n***\n")
    for volume, reagent, location in zip(
     [math.ceil(lig_mx.liq_vol), mix_tube.liq_vol, math.ceil(enhancer.liq_vol),
      user[0].liq_vol, adapter[0].liq_vol],
     ['ligation mix', 'master mix', 'enhancer', 'user dilution', 'adapter'],
     [lig_mx, mix_tube, enhancer, user, adapter]):
        ctx.comment(
         "\n***\n{0} uL {1} in {2}\n***\n".format(
          str(volume), reagent.upper(), location))

    # return liquid height in a well
    def liq_height(well, correcteddiameter=None):
        if well.diameter:
            if correcteddiameter:
                radius = correcteddiameter / 2
            else:
                radius = well.diameter / 2
            cse = math.pi*(radius**2)
        else:
            cse = well.length*well.width
        return well.liq_vol / cse

    # apply 10 mm/sec limit when tip leaves liquid
    def slow_tip_withdrawal(current_pipette, well_location):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        current_pipette.move_to(well_location.top())
        ctx.max_speeds[axis] = None

    ctx.comment("\n***\nSTEP - transferring ligation mix to mix tube\n***\n")

    # total volume to be transferred
    vol = 1.1*(60*num_cols)    # 10 percent overage

    # number of transfers needed
    reps = math.ceil(vol / 200)

    # volume per dispense
    v = vol / reps

    # pick up one tip on the rear-most channel
    p300m.pick_up_tip(tips300[0]['H12'])

    for rep in range(reps):

        if not rep:

            ctx.comment("\n***\nSTEP - pre-mixing ligation mix\n***\n")

            ht_mx = liq_height(lig_mx) if liq_height(lig_mx) > 1 else 1

            for rpt in range(10):
                p300m.aspirate(200, lig_mx.bottom(3), rate=0.2)
                ctx.delay(seconds=2)
                p300m.dispense(200, lig_mx.bottom(ht_mx), rate=0.2)
                ctx.delay(seconds=2)

        # increment source volume
        lig_mx.liq_vol -= v

        # tip height just below top of source liquid, avoiding over-immersion
        ht_source = liq_height(lig_mx) if liq_height(lig_mx) > 0.5 else 0.5

        # aspirate
        p300m.aspirate(v, lig_mx.bottom(ht_source), rate=0.2)
        ctx.delay(seconds=3)
        slow_tip_withdrawal(p300m, lig_mx)

        # increment dest volume
        mix_tube.liq_vol += v

        # tip height close to top of dest liquid, avoiding over-immersion
        ht_dest = liq_height(mix_tube) if liq_height(mix_tube) > 1 else 1

        # dispense
        p300m.dispense(v, mix_tube.bottom(ht_dest), rate=0.2)
        ctx.delay(seconds=3)
        slow_tip_withdrawal(p300m, mix_tube)

    p300m.drop_tip()

    ctx.comment("\n***\nSTEP - transferring enhancer to mix tube\n***\n")

    # total volume enhancer to be transferred
    vol = 1.1*(2*num_cols)    # 10 percent overage

    # pick up one tip on the rear-most channel and transfer
    p300m.pick_up_tip(tips300[0]['H11'])
    p300m.transfer(vol, enhancer, mix_tube.bottom(ht_dest), new_tip='never')

    ctx.comment(
     "\n***\nSTEP - transfer mixture to 2nd column reagent plate\n***\n")

    # volume to be transferred to each well
    vol = 7.75*num_cols + 2    # 2 uL overage

    mixture = reagent_plate.columns()[1][0]

    mixture.liq_vol = vol

    for index, well in enumerate(reagent_plate.columns()[1]):

        if not index:

            ctx.comment(
             "\n***\nSTEP - pre-mixing the contents of the mix tube\n***\n")
            for rep in range(10):
                p300m.aspirate(200, mix_tube.bottom(3), rate=0.3)
                ctx.delay(seconds=2)
                p300m.dispense(200, mix_tube.bottom(ht_dest), rate=0.3)
                ctx.delay(seconds=2)

        # increment source volume
        mix_tube.liq_vol -= vol

        # tip height just below top of source liquid, avoiding over-immersion
        ht = liq_height(mix_tube) if liq_height(mix_tube) > 0.5 else 0.5

        p300m.aspirate(vol, mix_tube.bottom(ht), rate=0.2)
        ctx.delay(seconds=2)
        slow_tip_withdrawal(p300m, mix_tube)

        p300m.dispense(vol, well.bottom(2), rate=0.2)
        ctx.delay(seconds=2)
        slow_tip_withdrawal(p300m, well)

    p300m.drop_tip()

    ctx.comment(
     "\n***\nSTEP - transfer 1 uL adapter to Library Prep Plate wells\n***\n")

    p20m.transfer(
     1, adapter[0].bottom(0.5),
     [column[0] for column in libraryprep_plate.columns()[:num_cols]],
     new_tip='always')

    ctx.comment(
     "\n***\nSTEP - transfer 7.75 uL mixture to Library Prep Plate\n***\n")

    for column in libraryprep_plate.columns()[:num_cols]:
        p20m.pick_up_tip()

        ht = liq_height(mixture) if liq_height(mixture) > 0.5 else 0.5

        mixture.liq_vol -= 7.75

        p20m.aspirate(7.75, mixture.bottom(ht), rate=0.2)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p20m, mixture)

        p20m.dispense(7.75, column[0], rate=0.2)
        ctx.delay(seconds=1)

        for rep in range(5):
            p20m.aspirate(10, column[0], rate=0.2)
            ctx.delay(seconds=1)
            p20m.dispense(10, column[0].bottom(2), rate=0.2)
            ctx.delay(seconds=1)
            if rep == 4:
                slow_tip_withdrawal(p20m, column[0])

        p20m.drop_tip()

    ctx.pause("\n***\nPausing for incubation on off-deck PCR machine\n***\n")

    ctx.comment(
     "\n***\nSTEP - transfer 1 uL User to Library Prep Plate\n***\n")

    for column in libraryprep_plate.columns()[:num_cols]:
        p20m.pick_up_tip()

        p20m.aspirate(1, user[0].bottom(0.5))
        p20m.dispense(1, column[0])

        for rep in range(5):
            p20m.aspirate(10, column[0], rate=0.2)
            ctx.delay(seconds=1)
            p20m.dispense(10, column[0].bottom(2), rate=0.2)
            ctx.delay(seconds=1)
            if rep == 4:
                slow_tip_withdrawal(p20m, column[0])

        p20m.drop_tip()

    ctx.comment("""\n***\nProceed to incubation on off-deck PCR machine.
                   Then to either part-5 or part-6\n***\n""")
