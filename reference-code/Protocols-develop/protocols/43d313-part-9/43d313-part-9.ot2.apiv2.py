import math
import csv
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''ArcBio RNA Workflow Continuous:
    Post-PCR Instrument: Pooling''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [count_samples, clearance_reservoir, height_engage, time_engage, offset_x,
     time_dry, uploaded_csv] = get_values(  # noqa: F821
      'count_samples', 'clearance_reservoir', 'height_engage', 'time_engage',
      'offset_x', 'time_dry', 'uploaded_csv')

    ctx.set_rail_lights(True)

    if not 1 <= count_samples <= 96:
        raise Exception('Invalid sample count (must be 1-96).')

    # csv transfers as a list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    # helper functions

    # notify user to replenish tips
    def pick_up_or_refill(pip, vol=200):
        nonlocal tipCtr
        try:
            if vol == 200:
                pip.pick_up_tip()
            else:
                if tipCtr < len(tips300.rows()[0]):
                    pip.pick_up_tip(tips300.rows()[0][tipCtr])
                    tipCtr += 1
                else:
                    tipCtr = 0
                    ctx.pause(
                     """Please Refill the 300 uL Tip Box
                     and Empty the Tip Waste""")
                    pip.pick_up_tip(tips300.rows()[0][tipCtr])
                    tipCtr += 1
        except OutOfTipsError:
            ctx.pause(
             """Please Refill the {} Tip Boxes
             and Empty the Tip Waste""".format(pip))
            pip.reset_tipracks()
            pip.pick_up_tip()

    # set liquid volume
    def liq_volume(wells, vol):
        for well in wells:
            well.liq_vol = vol

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

    # tips, p20 multi, p300 multi
    tips20 = [ctx.load_labware(
     "opentrons_96_filtertiprack_20ul", str(slot)) for slot in [10, 11]]
    p20s = ctx.load_instrument(
        "p20_single_gen2", 'left', tip_racks=tips20)
    tips300 = ctx.load_labware("opentrons_96_tiprack_300ul", 9)
    tipCtr = 0

    # pool tubes
    pooltubes = ctx.load_labware(
     'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
     '2', 'Pools')

    fourpools = pooltubes.rows()[0][:4]

    # libraries in PCR plate on temperature module at 4 degrees C
    temp = ctx.load_module('temperature module gen2', '3')
    libraries = temp.load_labware(
     'eppendorftwin.tec96_96_aluminumblock_200ul',
     "Libraries at Room Temperature")
    temp.set_temperature(4)

    ctx.comment("""STEP - Transfer CSV-specified library volume to
    one of four pool tubes (24 libraries / pool)""")

    p20s.transfer(
     [float(tfer['aspiration vol (uL)']) for tfer in tfers],
     [libraries.wells_by_name()[tfer['well']].bottom(1) for tfer in tfers],
     [fourpools[math.ceil(int(tfer['well'][1:]) / 4)].bottom(
      1) for tfer in tfers], new_tip='always')

    ctx.pause(
     '''Pooling protocol complete''')
