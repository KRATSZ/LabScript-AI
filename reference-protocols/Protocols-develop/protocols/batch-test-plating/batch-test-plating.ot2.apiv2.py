from opentrons import protocol_api

# metadata
metadata = {
    'protocolName': 'Batch Test Plating',
    'author': 'Facu <frodriguezgoren@gmail.com>',
    'description': 'Protocolo de plaqueo de Mix y \
    muestras para el Test de Lote',
    'apiLevel': '2.12'
}


def run(ctx: protocol_api.ProtocolContext):
    [_well_no] = get_values(  # noqa: F821
        '_well_no')

    if not 1 <= _well_no <= 82:
        raise Exception("Enter a value between 1-82")

    """ labware """
    placa = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '2')

    tiprack20 = ctx.load_labware('opentrons_96_filtertiprack_20ul', '5')

    tuberack_Muestras = ctx.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', '1')

    """ load pipettes """
    p20 = ctx.load_instrument(
        'p20_single_gen2', 'right', tip_racks=[tiprack20])

    """ Temperature Module """
    temperature_module = ctx.load_module('temperature module gen2', 3)

    tuberack = temperature_module.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap',
        label='Temperature-Controlled Tubes')

    # Important Wells

    MIX = tuberack['A1']
    well_inicial = _well_no - 1
    well_final = well_inicial + 14

    muestra_CT1 = tuberack_Muestras.wells()[0]
    muestra_CT2 = tuberack_Muestras.wells()[1]
    muestra_MH1 = tuberack_Muestras.wells()[2]
    muestra_MH2 = tuberack_Muestras.wells()[3]
    muestra_UU1 = tuberack_Muestras.wells()[4]
    muestra_UU2 = tuberack_Muestras.wells()[5]
    agua = tuberack_Muestras.wells()[-1]

    # Seteo de Temperatura
    temperature_module.set_temperature(8)
    temperature_module.await_temperature(8)
    ctx.pause("cargar tubos y muestras en el deck")

    # Plaqueo de MIX

    p20.distribute(
        7.5, MIX.bottom(-0.8), placa.wells()[well_inicial:well_final],
        blow_out=True, blowout_location='source well')

    # Plaqueo de Muestras
    p20.distribute(
        2.5, muestra_CT1.bottom(-0.8),
        placa.wells()[well_inicial:(well_inicial+2)],
        blow_out=True, blowout_location='source well')
    p20.distribute(
        2.5, muestra_CT2.bottom(-0.8),
        placa.wells()[(well_inicial+2):(well_inicial+4)], blow_out=True,
        blowout_location='source well')
    p20.distribute(
        2.5, muestra_MH1.bottom(-0.8),
        placa.wells()[(well_inicial+4):(well_inicial+6)], blow_out=True,
        blowout_location='source well')
    p20.distribute(
        2.5, muestra_MH2.bottom(-0.8),
        placa.wells()[(well_inicial+6):(well_inicial+8)], blow_out=True,
        blowout_location='source well')
    p20.distribute(
        2.5, muestra_UU1.bottom(-0.8),
        placa.wells()[(well_inicial+8):(well_inicial+10)], blow_out=True,
        blowout_location='source well')
    p20.distribute(
        2.5, muestra_UU2.bottom(-0.8),
        placa.wells()[(well_inicial+10):(well_inicial+12)], blow_out=True,
        blowout_location='source well')
    p20.distribute(
        2.5, agua.bottom(-0.8),
        placa.wells()[(well_inicial+12):(well_inicial+14)])
