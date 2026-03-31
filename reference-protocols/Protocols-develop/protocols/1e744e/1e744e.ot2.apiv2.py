# import from python types module
from types import MethodType
# import opentrons.types
from opentrons import types
from opentrons.protocol_api.labware import Well
import math
import string

metadata = {
    'title': 'BioGX XFree RT-PCR Reaction Setup',
    'author': 'Steve Plonk',
    'apiLevel': '2.11'
}


def run(ctx):

    [include_mastermix_step, include_sample_step, count_samples, mount_p20,
     labware_sampleplates, labware_mmplate, labware_96rxnplate,
     labware_384rxnplate, vol_mm, clearance_mmplate, clearance_samples,
     clearance_rxnplate] = get_values(  # noqa: F821
        "include_mastermix_step", "include_sample_step", "count_samples",
        "mount_p20", "labware_sampleplates", "labware_mmplate",
        "labware_96rxnplate", "labware_384rxnplate", "vol_mm",
        "clearance_mmplate", "clearance_samples", "clearance_rxnplate")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if not 1 <= count_samples <= 384:
        raise Exception('Invalid number of samples (must be 1-384).')

    # load sample plates (1-4 elution plates from extraction step)
    num_plates = math.ceil(count_samples / 96)
    sample_plates = [ctx.load_labware(
     labware_sampleplates, slot, "Samples")
           for slot in [2, 4, 5, 6][:num_plates]]

    # tips
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', str(slot))
              for slot in [7, 8, 9, 10, 11]]

    # p20 multi
    p20m = ctx.load_instrument("p20_multi_gen2", mount_p20, tip_racks=tips20)

    # 4 degree temperature module with reaction plate
    temp1 = ctx.load_module('temperature module gen2', '1')
    rxn_plate = temp1.load_labware(
     labware_96rxnplate, "Reaction Plate at 4 Degrees"
     ) if count_samples <= 96 else temp1.load_labware(
     labware_384rxnplate, "Reaction Plate at 4 Degrees")
    temp1.set_temperature(4)

    # 4 degree temperature module with mastermix plate
    temp2 = ctx.load_module('temperature module gen2', '3')
    mm_plate = temp2.load_labware(
     labware_mmplate, "Mastermix Plate at 4 Degrees")
    temp2.set_temperature(4)

    """
    extended well class to track liquid volume and height
    """

    class WellH(Well):
        def __init__(self, well, min_height=5, comp_coeff=1.15,
                     current_volume=0):
            super().__init__(well._impl)
            self.well = well
            # specified minimum well bottom clearance
            self.min_height = min_height
            self.comp_coeff = comp_coeff
            # specified starting volume in ul
            self.current_volume = current_volume
            # cross sectional area
            if self.diameter is not None:
                self.radius = self.diameter/2
                cse = math.pi*(self.radius**2)
            elif self.length is not None:
                cse = self.length*self.width
            else:
                cse = None
            self.cse = cse
            # initial liquid level in mm from start vol
            if cse:
                self.height = (current_volume/cse)
            else:
                raise Exception("""Labware definition must
                supply well radius or well length and width.""")
            if self.height < min_height:
                self.height = min_height
            elif self.height > well.parent.highest_z:
                raise Exception("""Specified liquid volume
                can not exceed the height of the labware.""")

        def height_dec(self, vol, ppt, bottom=False):
            # decrement height (mm)
            dh = (vol/self.cse)*self.comp_coeff
            # tip immersion (mm) as fraction of tip length
            mm_immersed = 0.05*ppt._tip_racks[0].wells()[0].depth
            # decrement til target reaches specified min clearance
            self.height = self.height - dh if (
             (self.height - dh - mm_immersed) > self.min_height
             ) else self.min_height + mm_immersed
            self.current_volume = self.current_volume - vol if (
             self.current_volume - vol > 0) else 0
            tip_ht = self.height - mm_immersed if bottom is False else bottom
            return(self.well.bottom(tip_ht))

        def height_inc(self, vol, top=False):
            # increment height (mm)
            ih = (vol/self.cse)*self.comp_coeff
            # keep calculated liquid ht between min clearance and well depth
            self.height = self.min_height if (
             self.height < self.min_height) else self.height
            self.height = (self.height + ih) if (
             (self.height + ih) < self.depth) else self.depth
            # increment
            self.current_volume += vol
            if top is False:
                tip_ht = self.height
                return(self.well.bottom(tip_ht))
            else:
                return(self.well.top())

    """
    *******************************************************************
    """

    """
    labware - added attributes and methods
    """

    # mastermix plate columns
    mm_plate.wells_h_list = [
     WellH(well, min_height=clearance_mmplate, current_volume=12*vol_mm)
     for well in [well for column in mm_plate.columns()[
      :num_plates] for well in column]] + [
      WellH(well, min_height=clearance_mmplate, current_volume=0)
      for well in [well for column in mm_plate.columns()[
       num_plates:] for well in column]]

    def wells_h(self):
        return self.wells_h_list

    def wells_by_name_h(self):
        return {well.well_name: well for well in self.wells_h_list}

    def rows_by_name_h(self):
        return {
         row: [well for well in self.wells_h_list if well.well_name[0] == row
               ] for row in [*string.ascii_uppercase][:len(self.rows())]}

    def columns_by_name_h(self):
        return {
         column: [well for well in self.wells_h_list if well.well_name[
          1:] == column] for column in [str(num+1) for num in range(
           len(self.columns()))]}

    def columns_h(self):
        return [
         [well for well in self.wells_h_list if well.well_name[1:] == column
          ] for column in [str(num+1) for num in range(len(self.columns()))]]

    def rows_h(self):
        return [
         [well for well in self.wells_h_list if well.well_name[0] == row
          ] for row in [*string.ascii_uppercase][:len(self.rows())]]

    # bind additional methods to labware
    for labware_object in [mm_plate]:
        for method in [wells_h, columns_h, rows_h, wells_by_name_h,
                       columns_by_name_h, rows_by_name_h]:
            setattr(
             labware_object, method.__name__,
             MethodType(method, labware_object))

    """
    *************************************************************************
    """

    """
    pipette - added attributes and methods
    """
    def aspirate_h(self, vol, source, rate=1, bottom=False):
        self.aspirate(
         vol, source.height_dec(vol, self, bottom=bottom), rate=rate)

    def dispense_h(self, vol, dest, rate=1, top=False):
        self.dispense(vol, dest.height_inc(vol, top=top), rate=rate)

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
    for pipette_object in [p20m]:
        for method in [aspirate_h, dispense_h, slow_tip_withdrawal, delay]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    """
    *************************************************************************
    """

    # yield next mastermix plate column as needed
    def mmcols():
        yield from mm_plate.columns_h()[:num_plates]

    mmcol = mmcols()
    mm = next(mmcol)

    # source from up to 4 sample plates
    sources = [well for row in [
     plate.rows()[0] for plate in sample_plates] for well in row]

    # destination in 96-well or 384-well reaction plate
    dests = rxn_plate.rows()[0] if count_samples <= 96 else [
     well for first2 in zip(
      rxn_plate.rows()[0], rxn_plate.rows()[1]) for well in first2]

    # number of dest columns to fill
    num_cols = math.ceil(count_samples / 8)

    # distribute mastermix
    if include_mastermix_step:
        p20m.pick_up_tip()
        for dest in dests[:num_cols]:
            # change to next column when volume is low
            if mm[0].current_volume < vol_mm:
                mm = next(mmcol)
            # aspirate at liquid level (avoiding overimmersion)
            p20m.aspirate_h(vol_mm, mm[0], rate=0.5)
            p20m.delay(1)
            p20m.slow_tip_withdrawal(10, mm[0])
            p20m.dispense(vol_mm, dest.bottom(clearance_rxnplate), rate=0.5)
            p20m.delay(1)
            p20m.slow_tip_withdrawal(10, dest)
        p20m.drop_tip()

    # transfer sample
    if include_sample_step:
        for source, dest in zip(sources[:num_cols], dests[:num_cols]):
            p20m.pick_up_tip()
            p20m.aspirate(5, source.bottom(clearance_samples))
            p20m.air_gap(2)
            p20m.dispense(7, dest.bottom(1))
            p20m.air_gap(2)
            p20m.drop_tip()
