import math

metadata = {
    'protocolName': 'PCR2 Setup',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.12'
}


def run(ctx):

    [num_samples, m20_mount, m300_mount, index_vol,
     pcr2_buffer_vol] = get_values(  # noqa: F821
        'num_samples', 'm20_mount', 'm300_mount', 'index_vol',
        'pcr2_buffer_vol')

    # load labware
    pcr2_buffer = ctx.load_labware('sarstedt_24_tuberack_2000ul', '1',
                                   'PCR2 buffer tube').wells()[0]
    pcr_plate = ctx.load_labware('eppendorfmetaladapter_96_wellplate_200ul',
                                 '5', 'PCR Plate')
    index_rack = ctx.load_labware('sarstedt_24_tuberack_500ul', '8',
                                  'UDI Tubes')
    tips20m = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '7')]

    # load pipette
    if m300_mount == m20_mount:
        raise Exception('Pipette mounts cannot match.')
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20m)

    num_cols = math.ceil(num_samples/6)
    num_channels = 3 if num_samples == 3 else 6
    m20.default_speed = 200
    pick_up_current_per_tip = 0.1

    def pick_up(pip=m20, channels=num_channels):
        # iterate and look for required number of consecutive tips
        pick_up_current = pick_up_current_per_tip*channels
        ctx._hw_manager.hardware._attached_instruments[
          m20._implementation.get_mount()].update_config_item(
          'pick_up_current', pick_up_current)

        for rack in pip.tip_racks:
            for col in rack.columns():
                counter = 0
                for well in col[::-1]:
                    if well.has_tip:
                        counter += 1
                    else:
                        counter = 0
                    if counter == channels:
                        pip.pick_up_tip(well)
                        return

        # refill rack if no tips available
        ctx.pause(f'Refill {pip} tipracks before resuming.')
        pip.reset_tipracks()

    indices = index_rack.rows()[0]
    sample_columns = [
        col[1:num_channels]
        for col in [
            pcr_plate.columns()[col_ind] for col_ind in [2, 4][:num_cols]]]
    all_samples = [well for col in sample_columns for well in col]

    # transfer indices
    ctx.max_speeds['Z'] = 40
    ctx.max_speeds['A'] = 40
    for col in sample_columns:
        for source, dest in zip(indices, col):
            pick_up(m20, channels=1)
            m20.aspirate(index_vol, source)
            m20.dispense(index_vol, dest)
            m20.drop_tip()

    # transfer buffer
    for dest in all_samples:
        pick_up(m20, channels=1)
        m20.aspirate(pcr2_buffer_vol, pcr2_buffer)
        m20.dispense(pcr2_buffer_vol, dest)
        m20.mix(10, pcr2_buffer_vol, dest)
        m20.drop_tip()
