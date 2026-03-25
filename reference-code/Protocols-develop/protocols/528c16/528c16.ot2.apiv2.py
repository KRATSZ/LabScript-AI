from opentrons import protocol_api

metadata = {
    'protocolName': 'Bioanalysis with CSV input',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [
     _csv,
     _p1000_mount,
     _p20_mount
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "_csv",
        "_p1000_mount",
        "_p20_mount")

    p20_mount = 'left'
    p1000_mount = 'right'

    # VARIABLES
    csv = _csv
    p20_mount = _p20_mount
    p1000_mount = _p1000_mount

    # LABWARE
    tuberacks = [ctx.load_labware(
                 'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
                 slot, label='Sample Tuberack')
                 for slot in ['1', '2', '4']]
    reagent_rack = ctx.load_labware(
                'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', '3')

    # TIPRACKS
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['5', '6', '8', '9']]
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', slot)
                   for slot in ['7', '10', '11']]

    # INSTRUMENTS
    p20 = ctx.load_instrument('p20_single_gen2',
                              p20_mount,
                              tip_racks=tiprack20)
    p1000 = ctx.load_instrument('p1000_single_gen2',
                                p1000_mount,
                                tip_racks=tiprack1000)

    csv_rows = [[val.strip() for val in line.split(',')]
                for line in csv.splitlines()
                if line.split(',')[0].strip()][1:]
    print(tuberacks, reagent_rack)
    p20.flow_rate.aspirate = 0.75*p20.flow_rate.aspirate
    p20.flow_rate.dispense = 0.75*p20.flow_rate.dispense
    p1000.flow_rate.aspirate = 0.75*p1000.flow_rate.aspirate
    p1000.flow_rate.dispense = 0.75*p1000.flow_rate.dispense

    def mix(pipette, mix_reps, mix_vol, tube, s_or_d):
        pipette.pick_up_tip()
        pipette.mix(mix_reps, mix_vol, tube)
        if s_or_d == 'd':
            pipette.blow_out()
            pipette.touch_tip()
            pipette.aspirate(4, tube.top(z=2))

        if p1000.has_tip:
            p1000.drop_tip()
        if p20.has_tip:
            p20.drop_tip()

    # protocol
    for row in csv_rows:
        tube_type, source_slot, source_well, transfer_vol, dest_slot, \
            dest_well = row[1:7]  # noqa: E501

        mix_reps, mix_vol, mix_or_not, asp_percent, disp_percent = row[9:14]
        if int(transfer_vol) >= 100:
            pip = p1000
        else:
            pip = p20

        source = ctx.loaded_labwares[int(source_slot)].wells_by_name()[
                                        source_well]
        dest = ctx.loaded_labwares[int(dest_slot)].wells_by_name()[
                                        dest_well]
        asp_height = source.depth*int(asp_percent)/100
        disp_height = source.depth*int(disp_percent)/100
        mix_reps = int(mix_reps)
        mix_vol = int(mix_vol)

        if mix_or_not.lower() == 's' and mix_reps > 0:
            if int(mix_vol) >= 20:
                mix(p1000, mix_reps, mix_vol, source, mix_or_not.lower())
            else:
                mix(p20, mix_reps, mix_vol, source, mix_or_not.lower())

        try:
            pip.transfer(int(transfer_vol),
                         source.bottom(z=asp_height),
                         dest.bottom(z=disp_height),
                         touch_tip=True,
                         air_gap=5,
                         new_tip='always')

            if mix_or_not.lower() == 'd' and mix_reps > 0:
                if int(mix_vol) >= 20:
                    mix(p1000, mix_reps, mix_vol, dest, mix_or_not.lower())
                else:
                    mix(p20, mix_reps, mix_vol, dest, mix_or_not.lower())

            ctx.comment('\n')

        except protocol_api.labware.OutOfTipsError:
            pass
            ctx.pause("Replace empty tip racks")
            pip.reset_tipracks()
            pip.transfer(int(transfer_vol),
                         source.bottom(z=asp_height),
                         dest.bottom(z=disp_height),
                         touch_tip=True,
                         air_gap=5,
                         new_tip='always')

            if mix_or_not.lower() == 'd' and mix_reps > 0:
                print('hello')
                if int(mix_vol) >= 20:
                    mix(p1000, mix_reps, mix_vol, dest, mix_or_not.lower())
                else:
                    mix(p20, mix_reps, mix_vol, dest, mix_or_not.lower())

        ctx.comment('\n')
