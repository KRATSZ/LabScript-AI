from opentrons import protocol_api

metadata = {
    'protocolName': 'RNA Quantitation',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [
     _csv,
     _source_type,
     _p20_mount,
     _m20_mount
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "_csv",
        "_source_type",
        "_p20_mount",
        "_m20_mount")

    # VARIABLES
    csv = _csv
    source_type = _source_type
    p20_mount = _p20_mount
    m20_mount = _m20_mount

    # MODULES
    thermocyc = ctx.load_module('thermocycler')

    # LABWARE
    slots = ['1'] if source_type == "kingfisher_96_wellplate_600ul" else ['1', '2', '4', '5']  # noqa: E501
    tuberacks = [ctx.load_labware(
                 source_type,
                 slot, label='Sample Tuberack')
                 for slot in slots]
    tc_plate = thermocyc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    dest_plate = ctx.load_labware('optiplate_96_wellplate_400ul',
                                  '3', label='Optiplate')

    # TIPRACKS
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in ['6', '9']]

    # INSTRUMENTS
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tipracks)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)

    pip = m20 if source_type == "kingfisher_96_wellplate_600ul" else p20
    print(pip.type)

    def pre_wet(vol, well):
        ctx.comment('PRE-WET')
        pip.aspirate(vol, well, rate=0.5)
        pip.dispense(vol, well, rate=0.5)
        ctx.comment('DONE PRE-WET')

    # MAPPING
    slot_source = 0
    source_well = 1
    transfer_vol = 3
    slot_dest = 4
    dest_well = 5

    all_rows = [[val.strip() for val in line.split(',')]
                for line in csv.splitlines()
                if line.split(',')[0].strip()][1:]

    print(tuberacks, tc_plate, dest_plate)
    if thermocyc.lid_position != 'open':
        thermocyc.open_lid()

    # protocol

    ctx.comment('\n\nMOVING SAMPLES TO PLATE\n')

    for the in all_rows:
        if the[transfer_vol].lower() == 'x':
            continue
        vol = int(the[transfer_vol])
        source = ctx.loaded_labwares[int(the[slot_source])].wells_by_name()[
                                        the[source_well]]
        dest = ctx.loaded_labwares[int(the[slot_dest])].wells_by_name()[
                                        the[dest_well]]
        pip.pick_up_tip()
        pre_wet(vol, source)
        pip.aspirate(vol, source)
        pip.dispense(vol, dest)
        pip.drop_tip()
