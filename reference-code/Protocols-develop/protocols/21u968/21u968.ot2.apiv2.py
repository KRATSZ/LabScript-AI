# flake8: noqa

def get_values(*names):
    import json
    _all_values = json.loads("""{"p300_mount":"left","tip_type":"opentrons_96_tiprack_300ul","plate_type":"biorad_96_wellplate_200ul_pcr"}""")
    return [_all_values[n] for n in names]


metadata = {
    'protocolName': 'PCR master mix distribution',
    'author': 'Iva <iva.h.pitelkova@uit.no>',
    'description': 'This protocols distributes 32 microL of PCR master mix in each well of 96-well plate.',
    'apiLevel': '2.9'
   
}


def run(protocol):

    [p300_mount, tip_type, plate_type] = get_values(  # noqa: F821
        "p300_mount", "tip_type", "plate_type")

    # Load Labware
    tiprack = protocol.load_labware(tip_type, 7)
    plate = protocol.load_labware(plate_type, 9)
    reservoir = protocol.load_labware(
            'opentrons_6_tuberack_falcon_50ml_conical', 8)
   

    # Load Pipette
    p300 = protocol.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tiprack])

    # Solutions
    MasterMix = reservoir['A1']
   

    # Wells to dispense MasterMix
    master_mix = [well for well in plate.wells()]
   
    # Distribute MasterMix solution to wells
    p300.distribute(32, MasterMix, master_mix, disposal_vol=0, blow_out=True)
  