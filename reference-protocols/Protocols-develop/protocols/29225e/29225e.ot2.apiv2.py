# import from python types module
from types import MethodType
# import from opentrons.types
from opentrons import types
from opentrons.protocol_api.labware import Well, OutOfTipsError
import csv
import math

metadata = {
    'title': 'RNA Normalization',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [move_side, vol_dead, mix_rate, clearance_water_tube, clearance_rna,
     clearance_dest, clearance_mix_aspirate, raise_mix_dispense,
     labware_water_tube, labware_firstrna, labware_rna, labware_dest, vol_h2o,
     uploaded_csv] = get_values(  # noqa: F821
        "move_side", "vol_dead", "mix_rate", "clearance_water_tube",
        "clearance_rna", "clearance_dest", "clearance_mix_aspirate",
        "raise_mix_dispense", "labware_water_tube", "labware_firstrna",
        "labware_rna", "labware_dest", "vol_h2o", "uploaded_csv")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if not -4 <= move_side <= 4:
        raise Exception(
         'p20 flow rate for mix must be 1 and 3 times the default rate.')

    if not 1 <= mix_rate <= 3:
        raise Exception(
         'p20 flow rate for mix must be 1 and 3 times the default rate.')

    if not clearance_rna >= 0:
        raise Exception(
         'Well bottom clearance must be 0 mm or greater.')

    if not clearance_dest >= 1:
        raise Exception(
         'Well bottom clearance must be 1 mm or greater.')

    # ignore lines if missing both water and source vol
    tfers = [line for line in csv.DictReader(
     uploaded_csv.splitlines()) if (line['water vol'] or line['source vol'])]

    # handle missing water vol as 0 uL
    for tfer in tfers:
        if not tfer['water vol']:
            tfer['water vol'] = 0

    sample_count = len(tfers)
    if not 1 <= sample_count <= 96:
        raise Exception('Invalid number of samples (must be 1-96).')

    # p300 single, p20 single, tips
    tips20 = [ctx.load_labware(
     'opentrons_96_filtertiprack_20ul', str(slot)) for slot in [10]]
    tips300 = [ctx.load_labware(
     'opentrons_96_filtertiprack_200ul', str(slot)) for slot in [11]]
    p20s = ctx.load_instrument("p20_single_gen2", 'left', tip_racks=tips20)
    p300s = ctx.load_instrument("p300_single_gen2", 'right', tip_racks=tips300)

    # water tubes with volume and liquid height tracking
    rack = ctx.load_labware(
     labware_water_tube,
     '4', 'Reagent Rack')

    if not ((vol_dead + 100) <= vol_h2o <= rack.wells()[0].max_volume):
        raise Exception(
         '''Starting volume of water must be between {0} uL and
         {1} uL per tube.'''.format(100+vol_dead, rack.wells()[0].max_volume))

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

    # extended well class to track liquid volume and height
    class WellH(Well):
        def __init__(self, well, min_height=5, comp_coeff=1.15,
                     current_volume=0):
            super().__init__(well._impl)
            self.well = well
            self.min_height = min_height
            self.comp_coeff = comp_coeff
            self.current_volume = current_volume
            if self.diameter is not None:
                self.radius = self.diameter/2
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            self.height = (
             current_volume/cse) - (0.2*pip._tip_racks[0].wells()[0].depth)
            if self.height < min_height:
                self.height = min_height
            elif self.height > well.parent.highest_z:
                raise Exception("""Specified liquid volume
                can not exceed the height of the labware.""")

        def height_dec(self, vol):
            if self.diameter is not None:
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            dh = (vol/cse)*self.comp_coeff
            if self.height - dh > self.min_height:
                self.height = self.height - dh
            else:
                self.height = self.min_height
            if self.current_volume - vol > 0:
                self.current_volume = self.current_volume - vol
            else:
                self.current_volume = 0
            return (self.well.bottom(self.height))

        def height_inc(self, vol, top=False):
            if self.diameter is not None:
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            ih = (vol/cse)*self.comp_coeff
            if self.height < self.min_height:
                self.height = self.min_height
            if self.height + ih < self.depth:
                self.height = self.height + ih
            else:
                self.height = self.depth
            self.current_volume += vol
            if top is False:
                return (self.well.bottom(self.height))
            else:
                return (self.well.top())

    water_tubes = []
    num_tubes = math.ceil(sum([float(
     tfer['water vol']) for tfer in tfers]) / vol_h2o) + 1
    pip = p20s

    for index, tube in enumerate(rack.wells()[:num_tubes]):
        new = rack.wells()[index]
        new.liq_vol = vol_h2o
        water_tubes.append(new)

    ctx.pause(
     "Please place {0} tubes each containing {1} uL water in {2}".format(
      num_tubes, vol_h2o, rack))

    def wtr_tubes():
        yield from water_tubes

    water_tube = wtr_tubes()

    water = next(water_tube)

    # 4 C temp mod with dest plate, wells with liquid vol and ht tracking
    temp = ctx.load_module('temperature module gen2', '1')
    dest_plate = temp.load_labware(
     labware_dest, "Destination Plate at 4 Degrees")
    temp.set_temperature(4)
    dest_wells = {
     well.well_name: WellH(
      well, min_height=clearance_dest, current_volume=0
      ) for well in dest_plate.wells()}

    # load 2nd temperature module in slot 3
    temp2 = ctx.load_module('temperature module gen2', '3')
    temp2.set_temperature(4)

    # count unique in csv minus 1, load additional input RNA labware instances
    rna = [
     ctx.load_labware(
      labware_rna, slot, "Additional Input RNA Samples") for slot in [
      2, 5, 6][:len(set([tfer['source rack or plate'] for tfer in tfers]))-1]]

    # load first input RNA labware on temperature module in slot 3
    rna.insert(0, temp2.load_labware(
     labware_firstrna, "First Input RNA Samples at 4 Degrees"))

    def distribute_water(pip, lst, disposal):
        nonlocal water
        if lst != []:
            disp = []
            in_tip = 0
            pip.pick_up_tip()
            water.liq_vol -= disposal
            ht = liq_height(water) - 3 if liq_height(water) - 3 > 1 else 1
            pip.aspirate(disposal, water.bottom(ht))
            in_tip += disposal
            for index, tfer in enumerate(lst):
                vol = float(tfer['water vol'])
                dst = dest_wells[tfer['dest well']]
                if water.liq_vol <= vol + vol_dead:
                    try:
                        water = next(water_tube)
                    except StopIteration:
                        ctx.comment("The next water tube was not found.")
                if vol + in_tip > pip._tip_racks[0].wells()[0].max_volume:
                    for d in disp:
                        v = float(d[0])
                        pip.dispense(v, d[1].height_inc(v))
                    disp = []
                    water.liq_vol += disposal
                    ht = liq_height(
                     water) - 3 if liq_height(water) - 3 > 1 else 1
                    pip.dispense(disposal, water.bottom(ht))
                    in_tip = 0
                    water.liq_vol -= disposal
                    ht = liq_height(
                     water) - 3 if liq_height(water) - 3 > 1 else 1
                    pip.aspirate(disposal, water.bottom(ht))
                    in_tip += disposal
                water.liq_vol -= vol
                ht = liq_height(water) - 3 if liq_height(water) - 3 > 1 else 1
                pip.aspirate(vol, water.bottom(ht))
                in_tip += vol
                disp.append((vol, dst))
                if index == len(lst)-1:
                    for d in disp:
                        v2 = float(d[0])
                        pip.dispense(v2, d[1].height_inc(v2))
            pip.drop_tip()

    def pick_up_or_refill(self):
        try:
            self.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             """Please Refill the {} Tip Boxes
                and Empty the Tip Waste.""".format(self))
            self.reset_tipracks()
            self.pick_up_tip()

    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    for pipette_object in [p20s, p300s]:
        for method in [pick_up_or_refill]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # transfer water
    small_tfers = []
    big_tfers = []
    for tfer in tfers:
        vol = float(tfer['water vol'])
        if 0 < vol <= 10:
            small_tfers.append(tfer)
        elif vol > 10:
            big_tfers.append(tfer)

    distribute_water(p20s, small_tfers, 2)

    distribute_water(p300s, big_tfers, 15)

    # transfer RNA and mix
    for tfer in tfers:
        vol = float(tfer['source vol'])
        dest = dest_wells[tfer['dest well']]
        if vol <= 20:
            pip = p20s
        else:
            pip = p300s
        pip.pick_up_or_refill()
        pip.aspirate(
         vol, rna[int(tfer['source rack or plate'])-1].wells_by_name(
         )[tfer['source well']].bottom(clearance_rna))
        pip.dispense(vol, dest.height_inc(vol))
        rt = mix_rate if pip == p20s else 1
        if pip == p20s:
            for rep in range(3):
                pip.aspirate(20, dest.height_dec(20).move(
                 types.Point(x=0, y=0, z=-(
                  dest.height-dest.min_height)+clearance_mix_aspirate
                 )), rate=rt)
                pip.dispense(20, dest.height_inc(20).move(types.Point(
                 x=0, y=0, z=raise_mix_dispense)), rate=rt)
            ctx.delay(seconds=1)
            pip.blow_out(
             dest.bottom(10).move(types.Point(x=move_side, y=0, z=0)))
        else:
            maxv = pip._tip_racks[0].wells()[0].max_volume
            calcv = 0.8*dest.current_volume
            v = calcv if calcv < maxv else maxv
            for rep in range(3):
                pip.aspirate(v, dest.height_dec(v))
                pip.dispense(v, dest.height_inc(v))
            pip.blow_out(dest.top(-2))
        pip.touch_tip(radius=0.75, v_offset=-2, speed=20)
        pip.drop_tip()

    for tfer in tfers:
        vol = float(tfer['water vol']) + float(tfer['source vol'])
        if vol > 50:
            pip = p300s
            pip.pick_up_or_refill()
            dest = dest_wells[tfer['dest well']]
            maxv = pip._tip_racks[0].wells()[0].max_volume
            calcv = 0.8*dest.current_volume
            v = calcv if calcv < maxv else maxv
            for rep in range(3):
                pip.aspirate(v, dest.height_dec(v))
                pip.dispense(v, dest.height_inc(v))
            pip.blow_out()
            pip.touch_tip(radius=0.75, v_offset=-2, speed=20)
            pip.drop_tip()
