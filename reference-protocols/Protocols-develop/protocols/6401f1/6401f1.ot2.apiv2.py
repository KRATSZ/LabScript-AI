from types import MethodType
import csv

metadata = {
    'title': 'PCR/qPCR Prep',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [uploaded_csv] = get_values(  # noqa: F821
        "uploaded_csv")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # p300 single, p20 single, tips
    tips20 = [ctx.load_labware(
     'opentrons_96_tiprack_20ul', str(slot)) for slot in [4]]
    tips300 = [ctx.load_labware(
     'opentrons_96_tiprack_300ul', str(slot)) for slot in [5]]
    p20s = ctx.load_instrument("p20_single_gen2", 'left', tip_racks=tips20)
    p300s = ctx.load_instrument("p300_single_gen2", 'right', tip_racks=tips300)

    # PCR plate
    pcr_plate = ctx.load_labware(
     'hardshell_96_wellplate_200ul', '1', 'Plate')

    # 24 Tube Rack
    tube_rack = ctx.load_labware(
     'beckman_24_tuberack_1000ul', '2', 'PCRMix1')

    # samples and controls
    samples = ctx.load_labware(
        'lvl_96_wellplate_1317.97ul', '3', 'Sample')
    controls = ctx.load_labware(
        'lvl_96_wellplate_1317.97ul', '6', 'POS_NTC')

    # comment added to satisfy linter
    ctx.comment(
     """Sample plate {s}, control plate {c}, tube rack {t},
     and pcr plate {p} loaded""".format(
       s=samples, c=controls, t=tube_rack, p=pcr_plate))

    # list loaded labware
    loaded_labwr = ctx.loaded_labwares.values()

    # helper functions
    def chunks_by_volume(volume_list, tip_max):
        new_list = []
        for index, element in enumerate(volume_list):
            if index != len(volume_list) - 1:
                if sum(new_list) + element <= tip_max:
                    new_list.append(element)
                else:
                    yield new_list
                    new_list = []
                    new_list.append(element)
            else:
                new_list.append(element)
                yield new_list

    # unbound methods
    def slow_tip_withdrawal(self, speed_limit, well_location, to_center=False):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = speed_limit
        if to_center is False:
            self.move_to(well_location.top())
        else:
            self.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    def delay(self, delay_time):
        ctx.delay(seconds=delay_time)

    # bind methods to pipette
    for pipette_object in [p20s, p300s]:
        for method in [delay, slow_tip_withdrawal]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # csv input
    rxns = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    # master mix locations, volumes, destinations from input csv
    sources = {}
    for rxn in rxns:
        for lbwr in loaded_labwr:
            if lbwr.name == rxn['MMSource']:
                mm_well = [well for row in lbwr.rows() for well in row][
                 int(rxn['MMSourceTube'])-1]
                mm_vol = round(float(rxn['MMXferVol']), 1)
                mm_dplt = rxn['Dest']
                mm_dwell = rxn['DestWell']
                if mm_well not in sources.keys():
                    sources[mm_well] = {'vol': [], 'dplt': [], 'dwell': []}
                sources[mm_well]['vol'].append(mm_vol)
                sources[mm_well]['dplt'].append(mm_dplt)
                sources[mm_well]['dwell'].append(mm_dwell)

    tip_max = tips300[0].wells()[0].max_volume

    # distribute master mixes
    for source, dct in sources.items():
        p300s.pick_up_tip()
        count = 0
        for chunk in chunks_by_volume(dct['vol'], tip_max-5):
            p300s.aspirate(sum(chunk)+5, source.bottom(1), rate=0.7)
            p300s.delay(3)
            p300s.slow_tip_withdrawal(5, source)
            for vol in chunk:
                plate = dct['dplt'][count]
                well = dct['dwell'][count]
                for lbwr in loaded_labwr:
                    if lbwr.name == plate:
                        dest = lbwr
                disp_well = [well for row in dest.rows() for well in row][
                 int(well)-1]
                p300s.dispense(vol, disp_well.bottom(1), rate=0.7)
                p300s.delay(1)
                p300s.slow_tip_withdrawal(10, disp_well)
                count += 1
        p300s.drop_tip()

    # transfer samples and controls following input csv
    for rxn in rxns:
        for lbwr in loaded_labwr:
            if lbwr.name == rxn['SampleSource']:
                samp = lbwr
            if lbwr.name == rxn['Dest']:
                pcr = lbwr
        if int(rxn['AspFromLiquid']):
            clearance = 16
        else:
            clearance = 1
        p20s.transfer(float(rxn['SampleXferVol']), [
         well for row in samp.rows() for well in row][
         int(rxn['SampleSourceWell'])-1].bottom(clearance), [
         well for row in pcr.rows() for well in row][
         int(rxn['DestWell'])-1].bottom(1), new_tip='always')
