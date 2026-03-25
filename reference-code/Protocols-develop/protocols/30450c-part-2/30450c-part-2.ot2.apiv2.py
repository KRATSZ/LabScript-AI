import math

metadata = {
    'protocolName': 'Add Samples and Standard Dilutions to ELISA Plates',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [plate_count, tip_touch, src_height, replenish_tips_manually,
     labware_elisa_plate, change_standard_tip] = get_values(  # noqa: F821
      'plate_count', 'tip_touch', 'src_height', 'replenish_tips_manually',
      'labware_elisa_plate', 'change_standard_tip')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if plate_count < 1 or plate_count > 5:
        raise Exception('Invalid number of ELISA plates (must be 1-5).')

    # 20 uL tips, 300 uL tips, empty 300 uL tip box, p20 multi, p300 multi

    # col 1 for buffer distribution, cols 2-12 to replenish row H of empty box
    tips300buffer = [ctx.load_labware(
     "opentrons_96_tiprack_300ul", str(slot)) for slot in [11]]
    tipsource = [
     tip for row in reversed(tips300buffer[0].rows()) for tip in row[1:]]

    # empty 300 uL box slot 9 (standards with one-tip on front-most channel)
    tips300standards = [ctx.load_labware(
     "opentrons_96_tiprack_300ul", str(slot),
     'Empty 300 uL Tip Box for Standard Tips') for slot in [9]]
    tips20 = [ctx.load_labware(
     "opentrons_96_tiprack_20ul", str(slot)) for slot in [10]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300standards)

    # yield list chunks of size n
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    elisaplates = [
     ctx.load_labware(labware_elisa_plate, str(slot+1),
                      'Elisa Plate in Slot {}'.format(
                      str(slot+1))) for slot in [*range(5)][:plate_count]]

    reagentreservoir = ctx.load_labware(
     'nest_1_reservoir_195ml', '7', 'Bulk Reagent 1x Assay Diluent A')

    sample_plate = ctx.load_labware(
     'falcon_353077_96_wellplate_320ul', '8', 'Sample Plate')

    # 90 uL buffer to rows A-G of each ELISA plate

    vol = 90

    source = reagentreservoir.wells()[0]

    for index, plate in enumerate(elisaplates[:plate_count]):

        if index > 0:
            ctx.pause("""\nPlease ensure 20 uL tips and the sample plate\n
            \nfor ELISA plate {} are on deck\n""".format(index+1))

        # pick up 7 tips
        p300m.pick_up_tip(tips300buffer[0]['B1'])

        # if tip touch, repeat dispense (faster plate filling), disposal vol
        if tip_touch:

            disposal_volume = 30

            dispense_locations = [column[0] for column in plate.columns()]

            chunk_size = math.floor(
             (tips300buffer[0].wells()[0].max_volume - disposal_volume) / vol)

            chunks = [*create_chunks(dispense_locations, chunk_size)]

            for chunk in chunks:

                p300m.aspirate(
                 len(chunk)*vol + disposal_volume, source.bottom(src_height))

                for well in chunk:
                    p300m.dispense(vol, well.top())
                    p300m.touch_tip()

                # return disposal to source for less reagent usage
                p300m.dispense(disposal_volume, source.bottom(src_height))

        # for clean top dispense when tip touch is not an option
        else:

            for column in plate.columns():

                # pre air gap
                p300m.move_to(source.top())
                p300m.air_gap(20)
                p300m.aspirate(vol, source.bottom(src_height))

                # dispense liquid followed by air at rate=2
                p300m.dispense(vol+20, column[0].top(), rate=2)
                # followed by delayed blowout
                ctx.delay(seconds=0.5)
                p300m.blow_out()

        if index + 1 < plate_count:
            p300m.return_tip()
        else:
            p300m.drop_tip()

        # load row H of empty standards tip box in slot 9
        def standardtips():
            yield from tipsource

        standardtip = standardtips()

        if not replenish_tips_manually:

            tipsneeded = 1 if not change_standard_tip else 12

            for column in tips300standards[0].columns()[:tipsneeded]:
                p300m.pick_up_tip(next(standardtip))
                p300m.drop_tip(column[-1])

            p300m.reset_tipracks()

        # single tip on front-most channel only
        # 100 uL standard from sample plate row H to ELISA plate row H

        newtip = 'always' if change_standard_tip else 'once'

        source_low_to_high = reversed(
         [column for chunk in zip(
          [*create_chunks(sample_plate.columns(), 6)][0],
          [*create_chunks(sample_plate.columns(), 6)][1]) for column in chunk])

        dest_low_to_high = reversed(
         [column for chunk in zip(
          [*create_chunks(plate.columns(), 6)][0],
          [*create_chunks(plate.columns(), 6)][1]) for column in chunk])

        p300m.transfer(
         100, [column[0].bottom(1) for column in source_low_to_high],
         [column[0].bottom(4) for column in dest_low_to_high],
         touch_tip=True, new_tip=newtip)

        # 7-tip 10 uL sample to ELISA plate rows A-G
        tiplist = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6',
                   'B7', 'B8', 'B9', 'B10', 'B11', 'B12']

        for tip, col1, col2 in zip(
         tiplist, sample_plate.columns(), plate.columns()):

            p20m.pick_up_tip(tips20[0][tip])

            p20m.aspirate(10, col1[0].bottom(1))
            ctx.delay(seconds=1)

            p20m.dispense(10, col2[0].bottom(2))
            ctx.delay(seconds=1)
            p20m.blow_out(col2[0].top())
            p20m.touch_tip()

            p20m.drop_tip()

    ctx.comment("Finished")
