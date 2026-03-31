# flake8: noqa
from opentrons import protocol_api
import math


def get_values(*names):
    import json
    _all_values = json.loads(
        """{"num_samples":5,
            "repeats_per_sample":3,
            "cryo_rack":"cryo_35_tuberack_1800ul",
            "sample_plate": "nest_96_wellplate_2ml_deep",
            "glycerol_plate": "opentrons_6_tuberack_falcon_50ml_conical",
            "pipette_type":"p1000_single_gen2",
            "pipette_mount":"right",
            "tip_type":"opentrons_96_tiprack_1000ul"
            }""")
    return [_all_values[n] for n in names]


metadata = {
    'apiLevel': '2.8',
    'protocolName': 'Glycerol Stock',
    'author': 'Tim Dobbs <tim@bioartbot.org>',
    'source': 'BioArtBot Project at LPI Paris',
    'description': """Adaptable protocol for making glycerol stocks"""
    }


def run(protocol: protocol_api.ProtocolContext):

    [num_of_samples, repeats_per_sample,
     cryo_rack, sample_plate, glycerol_plate,
     pipette_type, pipette_mount, tip_type] = get_values(
        'num_samples', 'repeats_per_sample',
        'cryo_rack', 'sample_plate', 'glycerol_plate', 
        'pipette_type', 'pipette_mount', 'tip_type')

    # a function that gets us the next available slot on the deck
    def slot_generator(available_slots):
        for slot in available_slots:
            yield slot
    available_slots = range(11, 0, -1)
    get_slot = slot_generator(available_slots)

    # a function that gets us the next available well on a plate
    # if the plate is full, the functions provisions another plate
    def well_generator(labware_type):
        while True:
            try:
                plate = protocol.load_labware(labware_type, next(get_slot))
            except StopIteration:
                    raise IndexError("""There aren't enough slots on the deck to run
                                        all of the samples you're attempting to run.
                                        Try doing it on two separate runs."""
                                    ) #Would prefer to raise StopIteration, but OT seems to be weird about handling it
            for well in plate.wells():
                yield well
    get_cryo_well = well_generator(cryo_rack)
    get_sample_well = well_generator(sample_plate)


    # load a tiprack and glycerol reservoir
    tipracks = list()
    for rack in range(math.ceil(num_of_samples / 95)):
        tipracks.append(protocol.load_labware(tip_type, next(get_slot)))
        
    protocol.comment('**CHECK BEFORE RUNNING**')
    protocol.comment('Ensure you have enough glycerol (500ul for each cryo tube)')
    glycerol_reservoir = protocol.load_labware(glycerol_plate, next(get_slot))

    # set the pipette we will be using
    pipette = protocol.load_instrument(
            pipette_type,
            mount=pipette_mount,
            tip_racks=tipracks
    )

    protocol.comment('Ensure you have matched the expected culture platemap:')
    source_list = list()
    for sample in range(num_of_samples):
        source_well = next(get_sample_well)
        source_list.append(source_well)
        protocol.comment(f'SAMPLE {sample + 1} -> {source_well}')

    well_mapping = {}
    for source in source_list:
        destination_list = []
        for repeat in range(repeats_per_sample):
            destination_list.append(next(get_cryo_well))
        well_mapping[source] = destination_list

    #load glycerol into all of the necessary tubes
    flat_well_list = [well for sublist in well_mapping.values() for well in sublist]
    pipette.distribute(source=glycerol_reservoir.wells("A1"),dest=flat_well_list,volume=500, disposal_volume=0)

    #load cultures into each appropriate tubes
    for source in well_mapping:
        pipette.distribute(source=source,dest=well_mapping[source],volume=500, disposal_volume=0)
