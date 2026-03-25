# import from the python types module
from types import MethodType
import math
from opentrons.protocol_api.labware import Well, OutOfTipsError
# import opentrons.types
from opentrons import types


metadata = {
    'protocolName': '''Custom Nucleic Acid Extraction and Bead Clean Up''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, park_tips, labware_reservoir, labware_pcr_plate,
     labware_deep_well, res_dead_vol, tube_dead_vol, clearance_reservoir,
     clearance_magplate, clearance_bead_pellet, engage_time,
     x_offset_bead_pellet
     ] = get_values(  # noqa: F821
      'sample_count', 'park_tips', 'labware_reservoir', 'labware_pcr_plate',
      'labware_deep_well', 'res_dead_vol', 'tube_dead_vol',
      'clearance_reservoir', 'clearance_magplate', 'clearance_bead_pellet',
      'engage_time', 'x_offset_bead_pellet')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if not 1 <= sample_count <= 96:
        raise Exception('Invalid number of samples (must be 1-96).')

    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

    # 300 ul tips and p300 multi gen2
    num_steps_300 = 5 if not park_tips else 3
    num_cols = math.ceil(sample_count / 8)
    num_tips300 = math.ceil((num_cols / 12)*num_steps_300)
    tips300 = [ctx.load_labware("opentrons_96_tiprack_300ul", str(slot)
                                ) for slot in [4, 5, 7, 8, 9][:num_tips300]]

    p300m = ctx.load_instrument("p300_multi_gen2", 'right', tip_racks=tips300)

    # reservoir, elution plate, 50 mL tube rack
    reservoir = ctx.load_labware(labware_reservoir, '2', 'Reservoir')
    elution_plate = ctx.load_labware(labware_pcr_plate, '1', 'Elution Plate')
    tubes = ctx.load_labware(
     "opentrons_6_tuberack_falcon_50ml_conical", '3', '50 mL Tube Rack')

    # beads, TE, liquid waste, 70 percent EtOH
    beads = reservoir['A1']
    vol_b = 25*(num_cols*8)*1.05 + res_dead_vol

    te = reservoir['A2']
    vol_t = 50*(num_cols*8)*1.05 + res_dead_vol

    waste = reservoir.wells()[2:]

    tube_count = 2 if (950*(num_cols*8)*1.05 + tube_dead_vol) > 50000 else 1
    vol_e = (950*(num_cols*8)*1.05) + tube_dead_vol*tube_count
    etoh = tubes.columns()[1][:tube_count]
    etoh_sup = tubes.columns()[2][:tube_count]

    pause_attention("""
        Place {0} mL beads into {1}, {2} mL TE into {3}, and a total of
        {4} mL 70 percent EtOH into {5} and resume.
        """.format(str(round(vol_b / 1000, 1)), beads,
                   str(round(vol_t / 1000, 1)), te,
                   str(round(vol_e / 1000, 1)), etoh))

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
            self.height = current_volume/cse
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
            return(self.well.bottom(self.height))

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
                return(self.well.bottom(self.height))
            else:
                return(self.well.top())

    # track volume and liquid height (70 percent EtOH tubes)
    etoh_sources = []
    for index, tube in enumerate(etoh):
        if index == 0:
            v = 50000 if vol_e > 50000 else vol_e
        else:
            v = vol_e - 50000
        new = WellH(tube, min_height=3, current_volume=v)
        etoh_sources.append(new)

    def etoh_tubes():
        yield from etoh_sources

    etoh_tube = etoh_tubes()
    etoh_source = next(etoh_tube)

    # track volume and liquid height (reservoir wells for waste)
    waste_destinations = []
    for well in waste:
        new = WellH(well, min_height=3)
        waste_destinations.append(new)

    def waste_wells():
        yield from waste_destinations

    waste_well = waste_wells()
    waste_dest = next(waste_well)

    # track volume and liquid height (waste tubes)
    etoh_sups = []
    for index, tube in enumerate(etoh_sup):
        if index == 0:
            v = 50000 if vol_e > 50000 else vol_e
        else:
            v = vol_e - 50000
        new = WellH(tube, min_height=3, current_volume=v)
        etoh_sups.append(new)

    def sup_tubes():
        yield from etoh_sups

    sup_tube = sup_tubes()
    sup_waste = next(sup_tube)

    # magnetic module with deep well plate
    magdeck = ctx.load_module('magnetic module gen2', '6')
    magdeck.disengage()
    magplate = magdeck.load_labware(labware_deep_well, 'Deep Well Plate')

    # 1000 ul tips (up to num boxes needed) in remaining available deck slots
    num_steps_1000 = 3
    num_tips1000 = int(math.ceil((sample_count / 96)*num_steps_1000))
    free_slots = [slot for slot in [str(num+1) for num in range(12)]
                  if ctx.deck[slot] is None]
    tips1000 = [ctx.load_labware("opentrons_96_tiprack_1000ul", str(slot))
                for slot in free_slots[:num_tips1000]]

    # p1000 single gen2
    p1000s = ctx.load_instrument(
     "p1000_single_gen2", 'left', tip_racks=tips1000)

    def pick_up_or_refill(self):
        try:
            self.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             """Please Refill the {} Tip Boxes
                and Empty the Tip Waste.""".format(self))
            self.reset_tipracks()
            self.pick_up_tip()

    def slow_tip_withdrawal(self, speed_limit, well_location, to_center=False):
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
        if to_center is False:
            self.move_to(well_location.top())
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
                self.aspirate(self.max_volume, well_location.top())
            ctx.delay(seconds=delay)
            self.blow_out(well_location.top())
        if touch is True:
            self.touch_tip(radius=0.75, v_offset=-2, speed=20)

    for pipette_object in [p300m, p1000s]:
        for method in [prewet_tips, delay, slow_tip_withdrawal,
                       blow_out_solvent, pick_up_or_refill]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # STEP 1: add beads to used columns and mix
    for column in magplate.columns()[:num_cols]:
        p300m.pick_up_tip()
        p300m.aspirate(25, beads.bottom(clearance_reservoir), rate=0.66)
        p300m.delay(1)
        p300m.slow_tip_withdrawal(10, beads)
        p300m.dispense(25, column[0].bottom(clearance_magplate), rate=0.33)
        p300m.delay(1)
        for rep in range(5):
            p300m.aspirate(
             200, column[0].bottom(clearance_magplate), rate=0.33)
            p300m.delay(1)
            p300m.dispense(
             200, column[0].bottom(clearance_magplate), rate=0.33)
            p300m.delay(1)
        p300m.blow_out(column[0].top(-2))
        p300m.air_gap(20)
        if park_tips:
            p300m.return_tip()
            p300m.reset_tipracks()
        else:
            p300m.drop_tip()

    # STEPS 2-4: delay 1 min, engage magnets, delay
    ctx.delay(minutes=1)
    magdeck.engage()
    ctx.delay(minutes=engage_time)

    # STEP 5: remove supernatant
    for column in magplate.columns()[:num_cols]:
        p300m.pick_up_tip()
        if (waste_dest.current_volume <= waste[0].max_volume - 275):
            pass
        else:
            try:
                waste_dest = next(waste_well)
            except StopIteration:
                pause_attention("Please empty the liquid waste")
                waste_well = waste_wells()
                waste_dest = next(waste_well)
        # offset to left to avoid beads (odd col numbers)
        if magplate.columns().index(column) % 2 != 1:
            f = -1
        # offset to right to avoid beads (even col numbers)
        else:
            f = 1
        p300m.move_to(column[0].top())
        ctx.max_speeds['A'] = 10
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(225, column[0].bottom(4), rate=0.33)
        p300m.aspirate(50, column[0].bottom(clearance_bead_pellet).move(
         types.Point(x=f*x_offset_bead_pellet, y=0, z=0)), rate=0.33)
        p300m.move_to(column[0].top())
        ctx.max_speeds['A'] = None
        p300m.air_gap(20)
        p300m.dispense(295, waste_dest.height_inc(275, top=True))
        p300m.blow_out(waste_dest.top(-2))
        p300m.air_gap(20)
        if park_tips:
            p300m.return_tip()
            p300m.reset_tipracks()
        else:
            p300m.drop_tip()

    # STEP 6: disengage magnets
    magdeck.disengage()

    # STEP 7: add 750 ul EtOH and mix
    for well in magplate.wells()[:num_cols*8]:
        p1000s.pick_up_tip()
        if etoh_source.current_volume >= 2000:
            p1000s.prewet_tips(etoh_source)
        else:
            try:
                etoh_source = next(etoh_tube)
            except StopIteration:
                pause_attention(
                 "Please replenish the 70 percent ethanol tubes.")
                etoh_tube = etoh_tubes()
                etoh_source = next(etoh_tube)
            p1000s.prewet_tips(etoh_source)
        p1000s.aspirate(750, etoh_source.height_dec(750))
        p1000s.air_gap(25)
        p1000s.dispense(775, well.bottom(clearance_bead_pellet))
        p1000s.mix(5, 650, well.bottom(clearance_bead_pellet))
        p1000s.blow_out_solvent(well, touch=True)
        p1000s.air_gap(25)
        p1000s.drop_tip()

    # STEPS 8-9: engage magnets, delay
    magdeck.engage()
    ctx.delay(minutes=engage_time)

    # STEP 10: remove supernatant
    for well in magplate.wells()[:num_cols*8]:
        p1000s.pick_up_tip()
        p1000s.move_to(well.top())
        ctx.max_speeds['Z'] = 10
        p1000s.move_to(well.bottom(4))
        p1000s.aspirate(700, well.bottom(4), rate=0.33)
        p1000s.aspirate(50, well.bottom(clearance_bead_pellet), rate=0.33)
        p1000s.air_gap(25)
        p1000s.move_to(well.top())
        ctx.max_speeds['Z'] = None
        if sup_waste.current_volume + 750 > 50000:
            try:
                sup_waste = next(sup_tube)
            except StopIteration:
                pause_attention("Please empty the ethanol waste tubes.")
                sup_tube = sup_tubes()
                sup_waste = next(sup_tube)
        p1000s.dispense(775, sup_waste.height_inc(750, top=True))
        p1000s.blow_out_solvent(sup_waste)
        p1000s.air_gap(25)
        p1000s.drop_tip()

    # STEP 11: disengage magnets
    magdeck.disengage()

    # STEP 12: add 200 ul EtOH and mix
    for well in magplate.wells()[:num_cols*8]:
        p1000s.pick_up_or_refill()
        if etoh_source.current_volume >= 2000:
            pass
        else:
            try:
                etoh_source = next(etoh_tube)
            except StopIteration:
                pause_attention(
                 "Please replenish the 70 percent ethanol tubes.")
                etoh_tube = etoh_tubes()
                etoh_source = next(etoh_tube)
        p1000s.prewet_tips(etoh_source, vol=200)
        p1000s.aspirate(200, etoh_source.height_dec(200))
        p1000s.air_gap(25)
        p1000s.dispense(225, well.bottom(clearance_bead_pellet))
        p1000s.mix(5, 100, well.bottom(1))
        p1000s.blow_out_solvent(well, touch=True)
        p1000s.air_gap(25)
        p1000s.drop_tip()

    # STEPS 13-14: engage magnets, delay
    magdeck.engage()
    ctx.delay(minutes=engage_time)

    # STEP 15: remove supernatant
    for column in magplate.columns()[:num_cols]:
        p300m.pick_up_or_refill()
        if (waste_dest.current_volume <= waste[0].max_volume - 275):
            pass
        else:
            try:
                waste_dest = next(waste_well)
            except StopIteration:
                pause_attention("Please empty the liquid waste")
                waste_well = waste_wells()
                waste_dest = next(waste_well)
        # offset to left to avoid beads (odd col numbers)
        if magplate.columns().index(column) % 2 != 1:
            f = -1
        # offset to right to avoid beads (even col numbers)
        else:
            f = 1
        p300m.move_to(column[0].top())
        ctx.max_speeds['A'] = 10
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(150, column[0].bottom(4), rate=0.33)
        p300m.aspirate(50, column[0].bottom(clearance_bead_pellet).move(
         types.Point(x=f*x_offset_bead_pellet, y=0, z=0)), rate=0.33)
        p300m.move_to(column[0].top())
        ctx.max_speeds['A'] = None
        p300m.air_gap(20)
        p300m.dispense(220, waste_dest.height_inc(200, top=True))
        p300m.blow_out(waste_dest.top(-2))
        p300m.air_gap(20)
        p300m.drop_tip()

    # STEPS 16-17: air dry, disengage magnets
    ctx.delay(minutes=5)
    magdeck.disengage()

    # STEP 18: add TE and mix
    for column in magplate.columns()[:num_cols]:
        p300m.pick_up_or_refill()
        p300m.aspirate(50, te.bottom(clearance_reservoir))
        # offset to right to target beads (odd col numbers)
        if magplate.columns().index(column) % 2 != 1:
            f = 1
        # offset to left to target beads (even col numbers)
        else:
            f = -1
        p300m.dispense(50, column[0].bottom(clearance_magplate).move(
         types.Point(x=f*x_offset_bead_pellet, y=0, z=0)))
        for rep in range(5):
            p300m.aspirate(30, column[0].bottom(1).move(
             types.Point(x=f*x_offset_bead_pellet, y=0, z=0)))
            p300m.dispense(30, column[0].bottom(1).move(
             types.Point(x=f*x_offset_bead_pellet, y=0, z=0)))
        p300m.blow_out(column[0].top(-2))
        p300m.drop_tip()

    # STEPS 19-20: engage magnets, delay
    magdeck.engage()
    ctx.delay(minutes=engage_time)

    # STEP 21: transfer eluate to pcr plate
    for index, column in enumerate(magplate.columns()[:num_cols]):
        p300m.pick_up_or_refill()
        # offset to left to avoid beads (odd col numbers)
        if magplate.columns().index(column) % 2 != 1:
            f = -1
        # offset to right to avoid beads (even col numbers)
        else:
            f = 1
        p300m.move_to(column[0].top())
        ctx.max_speeds['A'] = 10
        p300m.move_to(column[0].bottom(4))
        p300m.aspirate(50, column[0].bottom(1).move(
         types.Point(x=f*x_offset_bead_pellet, y=0, z=0)), rate=0.33)
        p300m.move_to(column[0].top())
        ctx.max_speeds['A'] = None
        p300m.dispense(50, elution_plate.columns()[index][0].bottom(2))
        p300m.drop_tip()

    # STEP 22: disengage magnets
    magdeck.disengage()
