metadata = {
    'protocolName': 'PCB Board Plating',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [p20_mount, samples, volume, trough_type] = get_values(  # noqa: F821
        "p20_mount", "samples", "volume", "trough_type")

    volume = float(volume)

    # Load Labware
    pcb = ctx.load_labware('pcb_board_250_wells', 1)
    trough = ctx.load_labware(trough_type, 6, 'Tetrahydrofuran')['A1']
    tiprack = ctx.load_labware('opentrons_96_tiprack_20ul', 3)

    # Load Pipette
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tiprack])

    # Transfer 10 uL to all wells
    for i in range(2):
        p20.transfer(volume, trough, pcb.wells()[:samples], new_tip='once')
        if i == 0:
            ctx.delay(minutes=1, msg='Pausing for 1 minute')
