from opentrons.protocol_api.labware import Well, OutOfTipsError
from types import MethodType
import math
import csv

metadata = {
    'title': 'Custom Dilution From CSV',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [mix_asp_rate, mix_disp_rate, dead_vol, labware_parent, labware_child,
     labware_reservoir, clearance_plate, clearance_reservoir,
     clearance_aspirate, clearance_dispense, mix_reps,
     uploaded_csv] = get_values(  # noqa: F821
        "mix_asp_rate", "mix_disp_rate", "dead_vol", "labware_parent",
        "labware_child", "labware_reservoir", "clearance_plate",
        "clearance_reservoir", "clearance_aspirate", "clearance_dispense",
        "mix_reps", "uploaded_csv")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # csv as list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    plates_child = [
     ctx.load_labware(labware_child, slot, "Child Plate") for slot in sorted(
      list(set([int(tfer['Child Plate Location']) for tfer in tfers])))]
    plates_parent = [
     ctx.load_labware(labware_parent, slot, "Parent Plate") for slot in sorted(
      list(set([int(tfer['Parent Plate Location']) for tfer in tfers])))]

    if not 1 <= len(plates_child) <= 1:
        raise Exception(
         'Invalid number of child plates specified in csv (must be 1).')

    if not 1 <= len(plates_parent) <= 5:
        raise Exception(
         'Invalid number of parent plates specified in csv (must be 1-5).')

    if not 0.3 <= mix_asp_rate <= 3:
        raise Exception(
         'Invalid value for mix aspiration rate (must be 0.3-3).')

    if not 0.3 <= mix_disp_rate <= 3:
        raise Exception(
         'Invalid value for mix dispense rate (must be 0.3-3).')

    # tips
    tips20 = [ctx.load_labware(
     'opentrons_96_filtertiprack_20ul', str(slot)) for slot in [1, 2, 3]]
    tips300 = [ctx.load_labware(
     'opentrons_96_filtertiprack_200ul', str(slot)) for slot in [6]]

    # p300 single, p20 single
    p300s = ctx.load_instrument("p300_single_gen2", 'right', tip_racks=tips300)
    p20s = ctx.load_instrument("p20_single_gen2", 'left', tip_racks=tips20)

    def pause_attention(message):
        ctx.set_rail_lights(False)
        ctx.delay(seconds=10)
        ctx.pause(message)
        ctx.set_rail_lights(True)

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

    # buffer in reservoir with vol and liquid height tracking
    reservoir = ctx.load_labware(labware_reservoir, '9', "Reservoir")
    vol_per_well = round(0.90909*reservoir.wells()[0].max_volume)

    # count of reservoir wells to be filled
    tfers_totalvol = sum(
     [float(tfer['Volume Buffer (ul)']) for tfer in tfers if tfer[
      'Volume Buffer (ul)']])
    buffer_vol = 1.1*tfers_totalvol + (math.ceil(
     1.1*tfers_totalvol / vol_per_well)*dead_vol)
    filledwells_count = math.ceil(buffer_vol / vol_per_well)

    if not 1 <= filledwells_count <= 12:
        raise Exception(
         'Number of reservoir wells to be filled must be between 1 and 12.')

    pause_attention(
     """Please ensure that the first {0} reservoir wells are each filled with
     at least {1} mL of buffer. Then resume.""".format(
      filledwells_count, round(vol_per_well / 1000)))

    def pick_up_or_refill(self):
        try:
            self.pick_up_tip()
        except OutOfTipsError:
            pause_attention(
             """Please Refill the {} Tip Boxes
                and Empty the Tip Waste.""".format(self))
            self.reset_tipracks()
            self.pick_up_tip()

    # bind additional methods to pipettes
    for pipette_object in [p20s, p300s]:
        for method in [pick_up_or_refill]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # perform buffer transfers with p300s
    pip = p300s

    # instantiate height and volume tracking wells
    buffer = [WellH(
     well, min_height=clearance_reservoir, current_volume=vol_per_well
     ) for well in reservoir.wells()[:filledwells_count]]

    # to yield next buffer well
    def buffer_wells():
        yield from buffer

    buffer_well = buffer_wells()
    buffer_source = next(buffer_well)
    pip.pick_up_or_refill()
    transfers = [tfer for tfer in tfers if tfer['Volume Buffer (ul)']]
    for tfer in transfers:
        # change source to next well when vol < specified dead vol
        if buffer_source.current_volume < dead_vol:
            try:
                buffer_source = next(buffer_well)
            except StopIteration:
                ctx.comment("buffer supply is exhausted")
                break
        reps = math.ceil(float(tfer[
         'Volume Buffer (ul)']) / pip._tip_racks[0].wells()[0].max_volume)
        if reps:
            vol = float(tfer['Volume Buffer (ul)']) / reps
        dest = ctx.loaded_labwares[
         int(tfer['Child Plate Location'])].wells_by_name()[tfer[
          'Child Well Location']]
        for rep in range(reps):
            pip.aspirate(vol, buffer_source.height_dec(vol))
            pip.dispense(vol, dest.bottom(clearance_plate))
    pip.drop_tip()

    # perform parent plate to child plate transfers
    for tfer in transfers:
        pip = p300s if float(tfer['Volume from Parent (ul)']) > 20 else p20s
        mxvol = 37 if float(tfer['Volume from Parent (ul)']) > 20 else 20
        pip.pick_up_or_refill()
        reps = math.ceil(float(
         tfer['Volume from Parent (ul)']) / pip._tip_racks[
         0].wells()[0].max_volume)
        vol = float(tfer['Volume from Parent (ul)']) / reps
        source = ctx.loaded_labwares[int(
         tfer['Parent Plate Location'])].wells_by_name()[tfer[
          'Parent Well Location']]
        dest = ctx.loaded_labwares[int(
         tfer['Child Plate Location'])].wells_by_name()[
         tfer['Child Well Location']]
        for rep in range(reps):
            if rep > 0:
                pip.drop_tip()
                pip.pick_up_or_refill()
            pip.aspirate(vol, source.bottom(clearance_aspirate))
            pip.dispense(vol, dest.bottom(clearance_dispense))
        if mix_reps:
            for rep in range(mix_reps):
                pip.aspirate(
                 mxvol, dest.bottom(clearance_dispense), rate=mix_asp_rate)
                pip.dispense(
                 mxvol, dest.bottom(clearance_dispense), rate=mix_disp_rate)
        pip.drop_tip()
