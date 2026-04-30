from opentrons.protocol_api.labware import OutOfTipsError
from types import MethodType
import csv

metadata = {
    'title': 'Custom Cherrypicking',
    'author': 'Steve Plonk',
    'apiLevel': '2.10'
}


def run(ctx):

    [clearance_source, clearance_dest, labware_384, labware_24, labware_96,
     uploaded_csv] = get_values(  # noqa: F821
        "clearance_source", "clearance_dest", "labware_384", "labware_24",
        "labware_96", "uploaded_csv")

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    # p20 single, tips
    tips20 = [ctx.load_labware(
     'opentrons_96_tiprack_20ul', str(slot)) for slot in [11]]
    p20s = ctx.load_instrument("p20_single_gen2", 'left', tip_racks=tips20)

    # csv file input
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    # labware types from protocol parameter input
    lb_types = {key: lb for key, lb in zip(['384', '24', '96'],
                [labware_384, labware_24, labware_96])}

    # labware type for each deck slot listed as source or dest in csv input
    lbwr = {}
    for tfer in tfers:
        if tfer['Source Slot'] not in lbwr.keys():
            lbwr[tfer['Source Slot']] = lb_types[tfer['Source Plate Type']]
        if tfer['Dest Slot'] not in lbwr.keys():
            lbwr[tfer['Dest Slot']] = lb_types[tfer['Dest Plate Type']]

    # load source and dest labware
    for slot in lbwr.keys():
        ctx.load_labware(lbwr[slot], slot)

    # list loaded labware
    loaded_lbwr = ctx.loaded_labwares.values()
    ctx.comment("Labware loaded for this run: {}".format(loaded_lbwr))

    # unbound methods
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

    def prewet_tips(self, well_location, vol=None, reps=2):
        for rep in range(reps):
            if vol is None:
                vol = self.max_volume
            else:
                vol = vol
            self.aspirate(vol, well_location)
            self.dispense(vol, well_location)

    # bind methods to pipette
    for pipette_object in [p20s]:
        for method in [pick_up_or_refill, prewet_tips]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))

    # perform transfers following input csv
    for tfer in tfers:
        p20s.pick_up_or_refill()
        for lbwr in loaded_lbwr:
            if lbwr.parent == tfer['Source Slot']:
                source = lbwr
            if lbwr.parent == tfer['Dest Slot']:
                dest = lbwr
        p20s.prewet_tips(
         source.wells_by_name()[tfer['Source Well']].bottom(clearance_source),
         vol=float(tfer['Volume Transfer']))
        p20s.transfer(
         float(tfer['Volume Transfer']),
         source.wells_by_name()[tfer['Source Well']].bottom(clearance_source),
         dest.wells_by_name()[tfer['Dest Well']].bottom(clearance_dest),
         new_tip='never')
        p20s.drop_tip()
