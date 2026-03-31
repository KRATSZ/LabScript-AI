from opentrons.protocol_api.labware import Well, OutOfTipsError
# import MethodType from the python types module
from types import MethodType
# import opentrons.types
from opentrons import types
import math
import csv
from opentrons.protocols.api_support.types import APIVersion

metadata = {
    'title': 'Protein Crystallization Screen Builder',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [dead_vol, skip_mix_step, labware1, labware2, labware3, labware4, labware5,
     labware6, labware7, labware8, reagents_csv,
     formulation_csv] = get_values(  # noqa: F821
        'dead_vol', 'skip_mix_step', 'labware1', 'labware2', 'labware3',
        'labware4', 'labware5', 'labware6', 'labware7', 'labware8',
        'reagents_csv', 'formulation_csv')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # p300 single, p1000 single, tips
    tips300 = [ctx.load_labware(
     'opentrons_96_tiprack_300ul', str(slot)) for slot in [10]]
    tips1000 = [ctx.load_labware(
     'opentrons_96_tiprack_1000ul', str(slot)) for slot in [11]]
    p300s = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)
    p1000s = ctx.load_instrument(
     'p1000_single_gen2', 'right', tip_racks=tips1000)

    # labware for reagents (based on protocol parameters)
    reagent_labware = [
     ctx.load_labware(labware, slot) for labware, slot in zip(
      [labware1, labware2, labware3, labware4, labware5, labware6, labware7,
       labware8], [num+1 for num in range(8)]) if labware is not None]

    ctx.comment(
     'reagent labware loaded for this run {}'.format(
      [labware.load_name for labware in reagent_labware]))

    # crystallization screening plate
    output_plate = ctx.load_labware(
     'usascientific_96_wellplate_2.4ml_deep', '9')

    def pick_up_or_refill(self):
        try:
            self.pick_up_tip()
        except OutOfTipsError:
            pause_attention('Please Refill the {} Tip Boxes \
and Empty the Tip Waste.'.format(self))
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
                 x=0, y=0, z=well_location.height+(20*(self._tip_racks[
                  0].wells()[0].depth / 88)))))
            else:
                self.move_to(well_location.center())
        ctx.max_speeds[axis] = previous_limit

    def delay(self, delay_time):
        ctx.delay(seconds=delay_time)

    def prewet_tips(self, well_location, vol=None, reps=2):
        for rep in range(reps):
            if vol is None:
                vol = self.max_volume
            else:
                vol = vol
            self.aspirate(vol, well_location.height_dec(vol))
            self.dispense(vol, well_location.height_inc(vol))

    def blow_out_solvent(self, well_location, reps=3, delay=1, touch=False):
        for rep in range(reps):
            if rep > 0:
                self.aspirate(self.max_volume, source.top())
            self.blow_out(well_location.top())
        if touch is True:
            self.touch_tip(radius=0.75, v_offset=-2, speed=20)

    class WellH(Well):
        def __init__(self, well, min_height=5, comp_coeff=1.15,
                     current_volume=0):
            super().__init__(well.parent, well._core, APIVersion(2, 13))
            self.well = well
            self.min_height = min_height
            self.comp_coeff = comp_coeff
            self.current_volume = current_volume
            if self.diameter is not None:
                self.radius = self.diameter/2
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            self.height = current_volume/cse
            if self.height < min_height:
                self.height = min_height
            elif self.height > well.parent.highest_z:
                raise Exception('Specified liquid volume \
can not exceed the height of the labware.')

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

    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    for pipette_object in [p300s, p1000s]:
        for method in [prewet_tips, delay, slow_tip_withdrawal,
                       blow_out_solvent, pick_up_or_refill]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # wells of output plate as rows
    dest_wells = []
    for row in output_plate.rows():
        row_wells = []
        for well in row:
            new = WellH(well, min_height=3)
            row_wells.append(new)
        dest_wells.append(row_wells)

    # formulation csv input
    [first_blank_line, *formulation_csv_lines] = formulation_csv.splitlines()
    dispenses = []
    liquids = ['H2O', '1', '2', '3', '4', '5', '6', '7', '8']
    lines = [*csv.reader(formulation_csv_lines)]
    for chunk in create_chunks(lines, 9):
        new = {}
        for line, liquid in zip(chunk, liquids):
            new[liquid] = []
            for index in range(2, 26, 2):
                new[liquid].append(line[index])
        dispenses.append(new)

    # reagent csv input
    [*reagent_csv_lines] = reagents_csv.splitlines()
    reagents = []
    for line in csv.DictReader(reagent_csv_lines):
        if line['Deck_Slot']:
            new = {}
            for key, value in zip(
             ['reagent', 'slot', 'wells', 'vols', 'liq', 'viscosity', 'sticky'
              ], [
              line['Reagent'], line['Deck_Slot'], line['Positions'].split(),
              line['Initial Volumes'].split(), line['Liquid class'],
              line['Viscosity'], line['Stickiness']]):
                new[key] = value
            reagents.append(new)

    source_locations = {}
    source_volumes = {}
    source_class = {}
    source_viscosity = {}
    for reagent in reagents:
        for key, value in ctx.loaded_labwares.items():
            if str(key) == str(reagent['slot']):
                source_locations[str(reagent['reagent'])] = [
                 value.wells_by_name()[well] for well in reagent['wells']]
                source_volumes[str(reagent['reagent'])] = [
                 int(volume) for volume in reagent['vols']]
                source_class[str(reagent['reagent'])] = reagent['liq']
                source_viscosity[
                 str(reagent['reagent'])] = reagent['viscosity']

    for rgnt in source_locations.keys():
        ctx.comment('Transferring reagent {} to output plate'.format(rgnt))
        liquid_class = source_class[rgnt]
        ctx.comment(' liquid class {}'.format(liquid_class))
        if liquid_class == 'viscous':
            if not source_viscosity[rgnt]:
                raise Exception('Viscosity in mPa*s must be provided \
for each viscous reagent.')
            else:
                viscosity = int(round(float(source_viscosity[rgnt])))
                ctx.comment(' viscosity {}'.format(viscosity))
                delay_time = round(1.67*(viscosity**0.2831))
                ctx.comment('calculated post-aspirate and post-dispense \
delay of {} seconds'.format(delay_time))
                adjusted_rate = round(
                 (81.379*(math.e)**(-0.002*viscosity)) / 92, 1)
                ctx.comment('calculated aspirate and dispense flow rate \
adjusted to {} times default rate.'.format(adjusted_rate))
                withdraw_speed = int(round(6.4613*(viscosity**-0.318)))
                ctx.comment('calculated tip withdraw speed adjusted \
to {} mm/sec.'.format(withdraw_speed))
        else:
            delay_time = 0
            adjusted_rate = 1
            withdraw_speed = None

        source_wells = []
        for well, vol in zip(source_locations[rgnt], source_volumes[rgnt]):
            minht = 3 if well.max_volume > 2000 else 1.5
            new = WellH(well, min_height=minht, current_volume=int(vol))
            source_wells.append(new)
        ctx.comment('''using locations as source: {}'''.format(source_wells))

        def reagent_wells():
            yield from source_wells

        reagent_well = reagent_wells()
        source = next(reagent_well)
        for row, dispense in zip(dest_wells, dispenses):
            for well, vol in zip(row, dispense[rgnt]):
                if vol:
                    if (source.current_volume <= (dead_vol*source.max_volume
                                                  ) or (int(vol) + (
                                                   dead_vol*source.max_volume
                                                   )) > source.current_volume):
                        try:
                            source = next(reagent_well)
                        except StopIteration:
                            ctx.comment(
                                'reagent {} supply is exhausted'.format(rgnt))
                            ctx.comment('''due to insufficient reagent volume,
                            skipped transfers (except well dispenses already
                            completed and listed above) to row {}'''.format(
                                row))
                            break
                    if (source.current_volume <= (dead_vol*source.max_volume
                                                  ) or (int(vol) + (
                                                   dead_vol*source.max_volume
                                                   )) > source.current_volume):
                        ctx.comment(
                             'reagent {} supply is exhausted'.format(rgnt))
                        ctx.comment('''due to insufficient reagent volume,
                        skipped transfers (except well dispenses already
                        completed and listed above) to row {}'''.format(
                             row))
                        break
                    reps = 1
                    if liquid_class == 'volatile':
                        air_gap_vol = 15
                    else:
                        air_gap_vol = 0
                    if int(vol) + air_gap_vol > 300:
                        pip = p1000s
                        top_dispenses = True
                        if liquid_class == 'volatile':
                            air_gap_vol = 25
                        if int(vol) + air_gap_vol > 1000:
                            reps = math.ceil(int(vol) / 1000)
                    else:
                        pip = p300s
                        top_dispenses = True
                        if int(vol) < 50:
                            top_dispenses = False

                    for rep in range(reps):
                        if not pip.has_tip:
                            pip.pick_up_or_refill()
                        if liquid_class == 'volatile':
                            pip.prewet_tips(source)
                        pip.aspirate(
                         (int(vol) / reps), source.height_dec(int(vol) / reps),
                         rate=adjusted_rate)
                        pip.delay(delay_time)
                        if withdraw_speed is not None:
                            pip.slow_tip_withdrawal(
                             withdraw_speed, source, to_surface=True)
                        if liquid_class == 'viscous':
                            speed_arg = 3.14*source.diameter
                            r = source.diameter / 2
                            radius_arg = (r - 0.5) / r
                            pip.touch_tip(
                             radius=radius_arg, v_offset=-2, speed=speed_arg)
                            top_dispenses = False
                        if liquid_class == 'volatile':
                            pip.air_gap(air_gap_vol)
                        dispense_location = well.height_inc(
                         int(vol) / reps, top=top_dispenses)
                        pip.dispense(
                         (int(vol) / reps)+air_gap_vol,
                         dispense_location, rate=adjusted_rate)
                        pip.delay(delay_time)
                        if top_dispenses is False:
                            if withdraw_speed is not None:
                                pip.slow_tip_withdrawal(
                                 withdraw_speed, well, to_surface=True)
                            if liquid_class == 'viscous':
                                original_value = pip.flow_rate.blow_out
                                pip.flow_rate.blow_out = original_value / 10
                                pip.blow_out()
                                pip.flow_rate.blow_out = original_value
                            else:
                                pip.blow_out()
                            pip.touch_tip(radius=0.75, v_offset=-2, speed=20)
                            pip.drop_tip()
                        else:
                            if liquid_class == 'volatile':
                                pip.blow_out_solvent(well)
                            else:
                                pip.blow_out()
        for pipette in [p300s, p1000s]:
            if pipette.has_tip:
                pipette.drop_tip()
    if not skip_mix_step:
        for row in dest_wells:
            for well in row:
                if well.current_volume > 0:
                    p1000s.pick_up_or_refill()
                    mix_volume = well.current_volume / 2
                    if (well.current_volume / 2) > 1000:
                        mix_volume = 1000
                    p1000s.mix(
                     10, mix_volume, well.bottom(well.height / 2), rate=0.25)
                    p1000s.drop_tip()
