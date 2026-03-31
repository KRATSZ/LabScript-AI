from operator import itemgetter
from opentrons.protocol_api.labware import Well, OutOfTipsError
# import from python types module
from types import MethodType
# import types from opentrons module
from opentrons import types
import math
import csv

metadata = {
    'title': 'qRT-PCR Reaction Setup',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [move_side, sample_cherrypicking, vol_h2o, labware_mm, labware_samp,
     labware_pcr, clearance_mm, clearance_samp, clearance_pcr,
     uploaded_csv_mastermix, uploaded_csv] = get_values(  # noqa: F821
        "move_side", "sample_cherrypicking", "vol_h2o", "labware_mm",
        "labware_samp", "labware_pcr", "clearance_mm", "clearance_samp",
        "clearance_pcr", "uploaded_csv_mastermix", "uploaded_csv")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if not -4 <= move_side <= 4:
        raise Exception(
         'Sideways move must be between 0 and 4 mm.')

    if not 100 <= vol_h2o <= 1000:
        raise Exception(
         'Starting volume of water must be between 100 and 1000 uL.')

    # csv transfers as list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    sample_count = len(tfers)
    if not 1 <= sample_count <= 96:
        raise Exception('Invalid number of samples (must be 1-96).')

    # count unique values in csv, load Normalized RNA labware
    samps = [ctx.load_labware(labware_samp, slot, "Normalized RNA Samples")
             for slot in [2, 3, 5, 6][:len(set([tfer['source plate or rack']
                                      for tfer in tfers]))]]

    # count unique values in csv, load master mix labware
    mms = [ctx.load_labware(labware_mm, slot, "Master Mixes")
           for slot in [4, 7, 8, 9][:len(set([tfer['master mix rack']
                                              for tfer in tfers]))]]

    # tips
    tips20 = [ctx.load_labware(
     'opentrons_96_filtertiprack_20ul', str(slot)) for slot in [10]]
    tips300 = [ctx.load_labware(
     'opentrons_96_filtertiprack_200ul', str(slot)) for slot in [11]]

    # p300 single
    p300s = ctx.load_instrument("p300_single_gen2", 'right', tip_racks=tips300)

    # p20 multi(if RNA not cherry-picked and in 96-well) otherwise single
    pip20 = ctx.load_instrument(
     "p20_multi_gen2", 'left', tip_racks=tips20) if (
     not sample_cherrypicking and len(samps[0].wells()) == 96
     ) else ctx.load_instrument("p20_single_gen2", 'left', tip_racks=tips20)

    # 4 degree temperature module with PCR plate
    temp = ctx.load_module('temperature module gen2', '1')
    pcr_plate = temp.load_labware(
     labware_pcr, "PCR Plate at 4 Degrees")
    temp.set_temperature(4)

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
             current_volume/cse) - (0.1*pip._tip_racks[0].wells()[0].depth)
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
            return self.well.bottom(self.height)

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
                return self.well.bottom(self.height)
            else:
                return self.well.top()

    # water tube (vol and liquid height tracking)
    pip = pip20
    water = WellH(mms[0].wells()[0], min_height=1, current_volume=vol_h2o)

    # master mix tubes (vol and liquid height tracking)
    mm_tubes = [WellH(mms[int(line['master mix rack'])-1].wells_by_name()[
     line['master mix well']], min_height=1, current_volume=int(
     line['master mix starting vol'])) for line in sorted(csv.DictReader(
      uploaded_csv_mastermix.splitlines()), key=itemgetter(
      'master mix rack', 'master mix well')) if mms[int(
       line['master mix rack'])-1].wells_by_name()[
       line['master mix well']] in [mms[int(
        line['master mix rack'])-1].wells_by_name()[
        line['master mix well']] for line in tfers]]

    def mm_sources():
        yield from mm_tubes

    mm = mm_sources()

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

    def slow_tip_withdrawal(
     self, speed_limit, well_location, to_surface=False):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        previous_limit = None
        if axis in ctx.max_speeds.keys():
            for key, value in ctx.max_speeds.items():
                if key == axis:
                    previous_limit = value
        ctx.max_speeds[axis] = speed_limit
        if to_surface is False:
            self.move_to(well_location.top())
        else:
            if isinstance(well_location, WellH):
                self.move_to(well_location.bottom().move(types.Point(
                 x=0, y=0, z=well_location.height+(
                  20*(self._tip_racks[0].wells()[0].depth / 88)))))
            else:
                self.move_to(well_location.center())
        ctx.max_speeds[axis] = previous_limit

    def delay(self, delay_time):
        ctx.delay(seconds=delay_time)

    # bind additional methods to pipettes
    for pipette_object in [pip20, p300s]:
        for method in [pick_up_or_refill, slow_tip_withdrawal, delay]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    def distribute_water(pip, lst, disposal):
        nonlocal water
        if lst != []:
            disp = []
            in_tip = 0
            pip.pick_up_tip()
            pip.aspirate(disposal, water.height_dec(disposal))
            in_tip += disposal
            for index, tfer in enumerate(lst):
                vol = float(tfer['water vol'])
                dst = pcr_plate.wells_by_name()[tfer['dest well']]
                # if water.current_volume <= 50:
                #    try:
                #        water = next(water_tube)
                #    except StopIteration:
                #        ctx.comment("The next water tube was not found.")
                if vol + in_tip > pip._tip_racks[0].wells()[0].max_volume:
                    for d in disp:
                        pip.dispense(float(d[0]), d[1].bottom(clearance_pcr))
                    disp = []
                    pip.dispense(disposal, water.height_inc(disposal))
                    in_tip = 0
                    pip.aspirate(disposal, water.height_dec(disposal))
                    in_tip += disposal
                pip.aspirate(vol, water.height_dec(vol))
                in_tip += vol
                disp.append((vol, dst))
                if index == len(lst)-1:
                    for d in disp:
                        pip.dispense(float(d[0]), d[1].bottom(clearance_pcr))
            pip.drop_tip()

    # distribute water to PCR plate
    water_transfers = []
    for tfer in tfers:
        if int(tfer['water vol']):
            water_transfers.append(tfer)
    if water_transfers != []:
        if pip20.name == "p20_single_gen2":
            distribute_water(pip20, water_transfers, 2)
        else:
            pause_attention("""Please manually dispense the indicated volumes
            of water to the corresponding PCR plate wells and then resume
            {}.""".format(["{0} ul to {1}".format(
             tfer['water vol'], tfer['dest well']
             ) for tfer in water_transfers]))

    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    # distribute master mix to PCR plate
    pip = p300s
    mm_source = next(mm)
    current_transfers = {'vol': [], 'dest': []}
    p300s.pick_up_tip()
    for index, tfer in enumerate(sorted(
     tfers, key=itemgetter('master mix rack', 'master mix well'))):
        if mms[int(tfer['master mix rack'])-1].wells_by_name()[
         tfer['master mix well']] == mm_source:
            current_transfers['vol'].append(float(tfer['master mix vol']))
            current_transfers['dest'].append(tfer['dest well'])
            if index == len(tfers) - 1:
                dest = (dest for dest in current_transfers['dest'])
                if not p300s.has_tip:
                    p300s.pick_up_or_refill()
                for chunk in create_chunks(
                 current_transfers['vol'], math.floor(
                  tips300[0].wells()[0].max_volume / 20)):
                    asp_vol = sum(chunk)
                    p300s.aspirate(15, mm_source.height_dec(15), rate=0.3)
                    p300s.aspirate(
                     asp_vol, mm_source.height_dec(asp_vol), rate=0.3)
                    p300s.delay(1)
                    p300s.slow_tip_withdrawal(10, mm_source)
                    p300s.touch_tip(
                     mm_source, radius=0.75, v_offset=-2, speed=10)
                    for vol in chunk:
                        d = pcr_plate.wells_by_name()[next(dest)]
                        p300s.dispense(vol, d.bottom(clearance_pcr), rate=0.3)
                        p300s.delay(1)
                        p300s.slow_tip_withdrawal(10, d)
                    if p300s.current_volume > 0:
                        p300s.dispense(p300s.current_volume,
                                       mm_source.height_inc(
                                            p300s.current_volume),
                                       rate=0.3)

        else:
            dest = (dest for dest in current_transfers['dest'])
            if not p300s.has_tip:
                p300s.pick_up_or_refill()
            for chunk in create_chunks(current_transfers['vol'], math.floor(
             tips300[0].wells()[0].max_volume / 20)):
                asp_vol = sum(chunk)
                p300s.aspirate(15, mm_source.height_dec(15), rate=0.3)
                p300s.aspirate(
                 asp_vol, mm_source.height_dec(asp_vol), rate=0.3)
                p300s.delay(1)
                p300s.slow_tip_withdrawal(10, mm_source)
                p300s.touch_tip(mm_source, radius=0.75, v_offset=-2, speed=10)
                for vol in chunk:
                    d = pcr_plate.wells_by_name()[next(dest)]
                    p300s.dispense(vol, d.bottom(clearance_pcr), rate=0.3)
                    p300s.delay(1)
                    p300s.slow_tip_withdrawal(10, d)
            try:
                if p300s.current_volume > 0:
                    p300s.dispense(p300s.current_volume,
                                   mm_source.height_inc(
                                        p300s.current_volume),
                                   rate=0.3)
                mm_source = next(mm)
                p300s.drop_tip()
            except StopIteration:
                break
            current_transfers = {'vol': [], 'dest': []}
            current_transfers['vol'].append(float(tfer['master mix vol']))
            current_transfers['dest'].append(tfer['dest well'])
            if index == len(tfers) - 1:
                dest = (dest for dest in current_transfers['dest'])
                if not p300s.has_tip:
                    p300s.pick_up_or_refill()
                p300s.aspirate(15, mm_source.height_dec(15), rate=0.3)
                for chunk in create_chunks(
                 current_transfers['vol'], math.floor(
                  tips300[0].wells()[0].max_volume / 20)):
                    asp_vol = sum(chunk)
                    p300s.aspirate(
                     asp_vol, mm_source.height_dec(asp_vol), rate=0.3)
                    p300s.delay(1)
                    p300s.slow_tip_withdrawal(10, mm_source)
                    p300s.touch_tip(
                     mm_source, radius=0.75, v_offset=-2, speed=10)
                    for vol in chunk:
                        d = pcr_plate.wells_by_name()[next(dest)]
                        p300s.dispense(vol, d.bottom(clearance_pcr), rate=0.3)
                        p300s.delay(1)
                        p300s.slow_tip_withdrawal(10, d)
    if p300s.has_tip:
        p300s.drop_tip()

    # transfer normalized RNA to PCR plate
    pip = pip20
    rna_tfers = [tfer for tfer in tfers if (tfer['dest well'] in [
     'A'+str(num+1) for num in range(12)] and tfer['source well'] in [
     'A'+str(num+1) for num in range(12)])] if pip20.name == \
        "p20_multi_gen2" else tfers
    for tfer in rna_tfers:
        pip20.pick_up_or_refill()
        vol = float(tfer['source vol'])
        pip20.aspirate(
         vol, samps[int(tfer['source plate or rack'])-1].wells_by_name()[
          tfer['source well']].bottom(clearance_samp))
        loc = pcr_plate.wells_by_name()[tfer['dest well']]
        pip20.dispense(vol, loc.bottom(clearance_pcr))
        for rep in range(3):
            pip20.aspirate(10, loc.bottom(1), rate=0.5)
            pip20.dispense(10, loc.bottom(4), rate=0.5)
        ctx.delay(seconds=1)
        pip20.blow_out(loc.bottom(6).move(types.Point(x=move_side, y=0, z=0)))
        pip20.drop_tip()
