from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Oncomine Focus Assay - Pt 1: Target Amplification',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):
    [
     _num_samps,  # Number of samples
     _mm_transfer_vol,  # amount of MM based on selection (8, 9, or 10uL)
     _dest_module,  # module used for destination plate containing samples
     _tc_cycles,  # number of cycles (if using Thermocycler)
     _src_module,  # module used for mastermix
     _m20_mount  # mount for p20-Multi
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        '_num_samps',
        '_mm_transfer_vol',
        '_dest_module',
        '_tc_cycles',
        '_src_module',
        '_m20_mount')

    # custom variables
    num_samps = _num_samps
    num_cols = math.ceil(num_samps/8)
    mm_transfer_vol = _mm_transfer_vol
    dest_module = _dest_module
    tc_cycles = _tc_cycles
    src_module = _src_module
    m20_mount = _m20_mount

    # load modules
    d_mod = None
    s_mod = None

    if dest_module is not None:
        d_mod = ctx.load_module(dest_module, '7')

    if src_module is not None:
        s_mod = ctx.load_module(src_module, '4')
        src_plate = s_mod.load_labware(
            'opentrons_96_aluminumblock_nest_wellplate_100ul',
            'Reagent Plate on Temp Deck')
        s_mod.set_temperature(4)

    # load labware
    if dest_module is None:
        dest_plate = ctx.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt', '7', 'Sample Plate')
    elif 'thermocycler' in dest_module:
        dest_plate = d_mod.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt',
            'Sample Plate on Thermocycler')
        d_mod.open_lid()
        d_mod.set_block_temperature(4)
    else:
        dest_plate = d_mod.load_labware(
            'opentrons_96_aluminumblock_nest_wellplate_100ul',
            'Sample Plate on Temp Deck')
        d_mod.set_temperature(4)

    if src_module is None:
        src_plate = ctx.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt', '4', 'Reagent Plate')

    # load tipracks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '3')]

    # load instrument
    p20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips)
    p20.flow_rate.aspirate = 4
    p20.flow_rate.dispense = 4

    # helper functions
    # to take vol and return estimated liq height
    def liq_height(well):
        if well.diameter is not None:
            radius = well.diameter / 2
            cse = math.pi*(radius**2)
        elif well.length is not None:
            cse = well.length*well.width
        else:
            cse = None
        if cse:
            return well.liq_vol / cse
        else:
            raise Exception("""Labware definition must
                supply well radius or well length and width.""")

    # reagents
    mm = src_plate['A1']
    mm.liq_vol = mm_transfer_vol * num_samps * 1.05

    # plate maps
    samples = dest_plate.rows()[0][:num_cols]

    # protocol
    # mastermix transfer
    ctx.comment(f'\nTransferring {mm_transfer_vol}uL Master Mix to samples\n')
    for sample in samples:
        p20.pick_up_tip()
        mm.liq_vol -= mm_transfer_vol
        mm_height = liq_height(mm) - 2 if liq_height(mm) - 2 > 1 else 1
        p20.aspirate(mm_transfer_vol, mm.bottom(mm_height))
        p20.dispense(mm_transfer_vol, sample)
        p20.mix(5, 12, sample)
        ctx.delay(seconds=1)
        p20.drop_tip()

    # optional - thermocycler
    if 'thermocycler' in dest_module:
        d_mod.set_lid_temperature(100)
        enz_temp = 98 if mm_transfer_vol == 10 else 99
        profile = [
            {'temperature': enz_temp, 'hold_time_seconds': 15},
            {'temperature': 60, 'hold_time_seconds': 240}
        ]
        d_mod.close_lid()
        d_mod.set_block_temperature(enz_temp, hold_time_seconds=120)
        d_mod.execute_profile(
            steps=profile, repetitions=tc_cycles, block_max_volume=20)
        d_mod.set_block_temperature(10)
        d_mod.deactivate_lid()
        d_mod.open_lid()

        ctx.comment('\nProtocol complete!')
    else:
        ctx.comment('\nLiquid handling complete; \
        please move plate to Thermal Cycler.\n')
