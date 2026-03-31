import csv
import math

metadata = {
    'title': 'Custom Transfer From CSV',
    'author': 'Steve Plonk',
    'apiLevel': '2.11'
}


def run(ctx):

    [vol_start_rnase, loc_rnase, vol_start_tween, loc_tween,
     count_mix, uploaded_csv] = get_values(  # noqa: F821
        "vol_start_rnase", "loc_rnase", "vol_start_tween", "loc_tween",
        "count_mix", "uploaded_csv")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # csv as list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines()[3:])]

    # tips
    tips20 = [ctx.load_labware(
     'opentrons_96_filtertiprack_20ul', str(slot)) for slot in [5, 11]]
    tips300 = [ctx.load_labware(
     'opentrons_96_filtertiprack_200ul', str(slot)) for slot in [10]]

    # p300 single, p20 single
    p300s = ctx.load_instrument("p300_single_gen2", 'right', tip_racks=tips300)
    p20s = ctx.load_instrument("p20_single_gen2", 'left', tip_racks=tips20)

    # racks 1-4, fluidx rack, RNaseA, Tween 20
    racks = [ctx.load_labware(
     'opentrons_24_tuberack_2000ul', str(slot),
     'Rack {}'.format(str(index+1))) for index, slot in enumerate(
     [7, 4, 1, 8])]

    # to satisfy linter
    ctx.comment("Racks Loaded {}".format(racks))

    fluidxrack = ctx.load_labware(
     'fluidx_96_tuberack_1000ul', '9', 'Fluidx Rack')

    rnase = fluidxrack.wells_by_name()[loc_rnase]
    rnase.liq_vol = vol_start_rnase

    tween = fluidxrack.wells_by_name()[loc_tween]
    tween.liq_vol = vol_start_tween

    # return liquid height in a well
    def liq_height(well):
        if well.diameter is not None:
            radius = well.diameter / 2
            cse = math.pi*(radius**2)
        elif well.length is not None:
            cse = well.length*well.width
        else:
            cse = None
        if cse:
            return well.liq_vol / cse
        else:
            raise Exception("""Labware definition must
                supply well radius or well length and width.""")

    # workflow step 1: serum reagent to fluidx tube
    for tfer in tfers:
        if tfer['Quantity of Serum']:

            p300s.transfer(
             int(tfer['Quantity of Serum']),
             ctx.loaded_labwares[int(tfer['Deck Position'])].wells_by_name()[
              tfer['Rack Position']].bottom(1),
             fluidxrack.wells_by_name()[tfer['TubePosition Final']].bottom(1),
             new_tip='always')

    # workflow step 2: RNaseA to fluidx tube
    for tfer in tfers:
        if tfer['Quantity of EACH Sterilization Reagent']:

            v = float(tfer['Quantity of EACH Sterilization Reagent'])

            rnase.liq_vol -= v
            tipheight = liq_height(
             rnase) - 3 if liq_height(rnase) - 3 > 1 else 1

            p20s.transfer(
             v, rnase.bottom(tipheight),
             fluidxrack.wells_by_name()[tfer['TubePosition Final']].bottom(1),
             new_tip='always')

    # workflow step 3: Tween 20 to fluidx tube
    for tfer in tfers:
        if tfer['Quantity of EACH Sterilization Reagent']:

            v = float(tfer['Quantity of EACH Sterilization Reagent'])

            tween.liq_vol -= v
            tipheight = liq_height(
             tween) - 3 if liq_height(tween) - 3 > 1 else 1

            p20s.transfer(
             v, tween.bottom(tipheight),
             fluidxrack.wells_by_name()[tfer['TubePosition Final']].bottom(1),
             mix_after=(count_mix, 20), new_tip='always')

    # workflow step 4: count 30 minutes
    ctx.delay(minutes=30)

    ctx.comment("workflow steps 1-4 are complete")

    ctx.set_rail_lights(False)
