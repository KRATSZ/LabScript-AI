from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Oncomine Focus Assay - Pt 3: Ligate Adapters',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):
    [
     _samp_cols,  # column numbers for digestion
     _dest_module,  # module used for destination plate containing samples
     _src_module,  # module used for mastermix
     _m20_mount  # mount for p20-Multi
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        '_samp_cols',
        '_dest_module',
        '_src_module',
        '_m20_mount')

    # custom variables
    samp_cols = _samp_cols.split(",")
    dest_module = _dest_module
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
    switch = src_plate['A3']
    switch.liq_vol = 4 * len(samp_cols) * 1.05
    ligase = src_plate['A4']
    ligase.liq_vol = 2 * len(samp_cols) * 1.05
    adapter_mix = src_plate.rows()[0][4:4+len(samp_cols)]

    # protocol
    # Switch Solution Transfer
    ctx.comment(f'\nTransferring 4uL Switch Solution \
    to samples in columns {samp_cols}\n')
    for col in samp_cols:
        p20.pick_up_tip()
        switch.liq_vol -= 4
        s_height = liq_height(switch) - 2 if liq_height(switch) - 2 > 1 else 1
        p20.aspirate(4, switch.bottom(s_height))
        p20.dispense(4, dest_plate['A'+col.strip()])
        ctx.delay(seconds=1)
        p20.drop_tip()

    # Barcode Adapter Mix Transfer
    ctx.comment(f'\nTransferring 2uL Barcode Adapter Mix \
    to samples in columns {samp_cols}\n')
    for col, re in zip(samp_cols, adapter_mix):
        p20.pick_up_tip()
        p20.aspirate(2, re)
        p20.dispense(2, dest_plate['A'+col.strip()])
        ctx.delay(seconds=1)
        p20.drop_tip()

    # Switch Solution Transwer
    ctx.comment(f'\nTransferring 2uL DNA Ligase \
    to samples in columns {samp_cols}\n')
    for col in samp_cols:
        p20.pick_up_tip()
        ligase.liq_vol -= 2
        l_height = liq_height(ligase) - 2 if liq_height(ligase) - 2 > 1 else 1
        p20.aspirate(2, ligase.bottom(l_height))
        p20.dispense(2, dest_plate['A'+col.strip()])
        p20.mix(5, 15)
        ctx.delay(seconds=1)
        p20.drop_tip()

    # optional - thermocycler
    if 'thermocycler' in dest_module:
        d_mod.set_lid_temperature(100)
        d_mod.close_lid()
        for temp, time in zip([22, 68, 72], [30, 5, 5]):
            d_mod.set_block_temperature(temp, hold_time_minutes=time)
        d_mod.set_block_temperature(10)
        d_mod.deactivate_lid()
        d_mod.open_lid()
        ctx.comment('\nProtocol complete!')
    else:
        ctx.comment('\nLiquid handling complete; \
        please move plate to Thermal Cycler.\n')
