import math

metadata = {
    'protocolName': 'Aliquot',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.13'
    }


def run(ctx):
    [num_aliquots, vol_aliquot, lw_source, type_pip,
     mount_pip] = get_values(  # noqa: F821
        'num_aliquots', 'vol_aliquot', 'lw_source', 'type_pip', 'mount_pip')

    # labware
    num_racks = math.ceil(num_aliquots/24)
    dest_racks = [
        ctx.load_labware(
            'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', slot,
            f'rack {i+1}')
        for i, slot in enumerate(['4', '5', '1', '2'][:num_racks])]
    source = ctx.load_labware(lw_source, '6', 'source (A1)').wells()[0]

    pip = ctx.load_instrument(type_pip, mount_pip)

    tiprack = [
        ctx.load_labware(f'opentrons_96_tiprack_{pip.max_volume}ul', '3')]
    pip.tip_racks = tiprack

    def slow_withdraw(well, pip=pip, delay_seconds=2.0):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 10

    aliquots = [
        well for rack in dest_racks for well in rack.wells()][:num_aliquots]
    pip.pick_up_tip()
    for a in aliquots:
        pip.aspirate(vol_aliquot, source.bottom(3))
        slow_withdraw(source)
        pip.dispense(vol_aliquot, a.bottom(2))
        slow_withdraw(a)
    pip.drop_tip()
