import math
from opentrons.protocol_api.labware import Well


metadata = {
    'protocolName': '''Custom Aliquoting''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # parameter values from json above
    [sample_count_1, sample_count_2, labware_clinical_samples_1,
     labware_clinical_samples_2, labware_aliquots, clearance_clinical_samples,
     clearance_aliquots] = get_values(  # noqa: F821
      'sample_count_1', 'sample_count_2', 'labware_clinical_samples_1',
      'labware_clinical_samples_2', 'labware_aliquots',
      'clearance_clinical_samples', 'clearance_aliquots')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    sample_count_tot = sample_count_1 + sample_count_2
    if not 1 <= sample_count_tot <= 48:
        raise Exception(
         'Invalid total number of clinical samples ({}). Must be 1-48.'.format(
          sample_count_tot))
    if not (clearance_clinical_samples >= 1 and clearance_aliquots >= 1):
        raise Exception('Tube bottom clearances must be at least 1 mm.')

    # 1000 ul tips and p1000
    tips1000 = [ctx.load_labware("opentrons_96_tiprack_1000ul", '11')]

    # p1000 single gen2
    p1000s = ctx.load_instrument(
     "p1000_single_gen2", 'left', tip_racks=tips1000)

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

    # clinical sample racks, clinical sample tubes with liquid height tracking
    clinical_sample_tubes = []
    for lbwr, slot, count in zip(
     [labware_clinical_samples_1, labware_clinical_samples_2],
     ['8', '9'],
     [sample_count_1, sample_count_2]):
        if lbwr:
            ctx.load_labware(lbwr, slot, 'Clinical Samples')
            if not 1 <= count <= len(ctx.deck[slot].get_wells()):
                raise Exception('''Invalid number of samples in
                slot {0} (must be 1-{1}).'''.format(
                 slot, len(ctx.deck[slot].get_wells())))
            new = [WellH(
             tube, min_height=clearance_clinical_samples, current_volume=2000)
             for tube in ctx.loaded_labwares[int(slot)].wells()[:count]]
            clinical_sample_tubes.extend(new)
        else:
            if count:
                raise Exception(
                 '''Invalid number of samples in slot {}
                 (must be 0 if no rack is specified).'''.format(slot))

    # aliquots
    [*aliquots] = [
     ctx.load_labware(labware_aliquots, slot, "Aliquots") for slot in [
      '10', '7', '4', '5', '6', '1', '2', '3'][
      :math.ceil((sample_count_tot*4) / 24)]]

    # to yield 4 aliquot tubes
    def tube_col():
        for rack in aliquots:
            for column in rack.columns():
                yield column

    aliquot_tubes = tube_col()

    # perform aliquotting steps
    for tube in clinical_sample_tubes:
        p1000s.pick_up_tip()
        for dest, vol in zip(next(aliquot_tubes), [1000, 500, 500, 1000]):
            p1000s.aspirate(vol, tube.height_dec(vol))
            p1000s.dispense(vol, dest.bottom(clearance_aliquots))
        p1000s.drop_tip()
