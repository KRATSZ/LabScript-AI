import math

metadata = {
    'protocolName': 'Add Bulk Reagent to ELISA Plates',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json
    [plate_count, step, src_height, pause_for_washing, tip_touch,
     labware_reservoir, labware_elisa_plate] = get_values(  # noqa: F821
      'plate_count', 'step', 'src_height', 'pause_for_washing', 'tip_touch',
      'labware_reservoir', 'labware_elisa_plate')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if plate_count < 1 or plate_count > 5:
        raise Exception('Invalid number of ELISA plates (must be 1-5).')

    if step == 'blocking' and labware_reservoir == 'nest_12_reservoir_15ml':
        raise Exception('Use 195 mL reservoir for 200 uL blocking transfers')

    # tips, p300 multi
    tips300 = [ctx.load_labware(
     "opentrons_96_tiprack_300ul", str(slot)) for slot in [11]]
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    reagent_dict = {'blocking': '1x Assay Diluent',
                    'coating': 'capture ab in 1x Coating Buffer A',
                    'detection ab': 'diluted detection ab',
                    'avidin hrp': 'diluted Avidin-HRP',
                    'TMB substrate': 'TMB substrate',
                    'stop': 'stop solution'}

    vol_dispense_dict = {'blocking': 200,
                         'coating': 100,
                         'detection ab': 100,
                         'avidin hrp': 100,
                         'TMB substrate': 100,
                         'stop': 100}

    # yield list chunks of size n
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    elisaplates = [
     ctx.load_labware(labware_elisa_plate, str(slot+1),
                      'Elisa Plate in Slot {}'.format(
                      str(slot+1))) for slot in [*range(5)][:plate_count]]

    reagentreservoir = ctx.load_labware(
     labware_reservoir, '10', 'Bulk Reagent {}'.format(
      reagent_dict[step]))

    vol = vol_dispense_dict[step]

    bufferwells = 5*[
     reagentreservoir.wells()[0]
     ] if labware_reservoir != 'nest_12_reservoir_15ml' \
        else reagentreservoir.wells()[:5]

    p300m.pick_up_tip()

    for index, plate in enumerate(elisaplates[:plate_count]):

        source = bufferwells[index]

        # pause for off deck washing, then fill
        if pause_for_washing:
            p300m.move_to(reagentreservoir.wells()[0].top())
            ctx.pause(
             """Pausing to wash ELISA plate {}.
             Resume to fill with {} uL {}""".format(
              index+1, vol, reagent_dict[step]))
        else:
            ctx.comment(
             "Filling ELISA plate {} with {} uL {}".format(
              index+1, vol, reagent_dict[step]))

        # if tip touch, repeat dispense (faster plate filling), disposal vol
        if tip_touch:

            disposal_volume = 100

            dispense_locations = [column[0] for column in plate.columns()]

            chunk_size = math.floor(
             (tips300[0].wells()[0].max_volume - disposal_volume) / vol)

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

    p300m.drop_tip()

    ctx.comment("Finished with {} step".format(step))
