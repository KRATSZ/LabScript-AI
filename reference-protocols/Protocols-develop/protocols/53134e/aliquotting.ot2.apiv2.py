metadata = {
    'protocolName': 'Media Aliquotting',
    'author': 'Nick <ndiehl@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


def run(ctx):
    [num_samples, transfer_vol, p1000_mount] = get_values(  # noqa: F821
        'num_samples', 'transfer_vol', 'p1000_mount')

    # labware
    source = ctx.load_labware('nest_1_reservoir_195ml', '1',
                              'liquid reservoir').wells()[0]
    tuberack = ctx.load_labware('custom_24_tuberack_2000ul', '2',
                                'custom tuberack')
    tiprack = [
        ctx.load_labware('opentrons_96_tiprack_1000ul', '4', '1000µl tiprack')]

    # pipette
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack)

    # perform transfers
    for d in tuberack.wells()[:num_samples]:
        for _ in range(2):
            p1000.pick_up_tip()
            p1000.transfer(
                transfer_vol, source, d, air_gap=50, new_tip='never')
            p1000.air_gap(50)
            p1000.drop_tip()
