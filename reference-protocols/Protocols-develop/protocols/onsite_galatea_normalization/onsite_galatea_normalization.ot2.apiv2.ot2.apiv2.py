from opentrons import protocol_api
import threading
from time import sleep


metadata = {
    'protocolName': 'Normalization and Barcode Addition',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


class CancellationToken:
    """FLASH SETUP."""

    def __init__(self):
        """FLASH SETUP."""
        self.is_continued = False

    def set_true(self):
        """FLASH SETUP."""
        self.is_continued = True

    def set_false(self):
        """FLASH SETUP."""
        self.is_continued = False


def turn_on_blinking_notification(hardware, pause):
    """FLASH SETUP"""
    while pause.is_continued:
        hardware.set_lights(rails=True)
        sleep(1)
        hardware.set_lights(rails=False)
        sleep(1)


def create_thread(ctx, cancel_token):
    """FLASH SETUP."""
    t1 = threading.Thread(target=turn_on_blinking_notification,
                          args=(ctx._hw_manager.hardware, cancel_token))
    t1.start()
    return t1


def run(ctx):
    cancellationToken = CancellationToken()

    [csv_samp, dna_plate_type, if_48,
        p20_mount, m20_mount] = get_values(  # noqa: F821
            "csv_samp", "dna_plate_type", "if_48", "p20_mount", "m20_mount")

    flash = True

    # labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 1)
    barcode_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr',
                                     5)
    buffer_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                    6)

    dna_plate = ctx.load_labware(dna_plate_type, 2)

    final_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 3)

    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in [10, 11]]
    tipbox_less_than_eight = [ctx.load_labware(
                              'opentrons_96_filtertiprack_20ul', slot)
                              for slot in [8, 9]]

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            pip.home()
            ctx.pause('\n\n~~~~~~~~~~PLEASE REPLACE TIPRACKS~~~~~~~~~~~\n')
            ctx.home()  # home before continuing with protocol
            if flash:
                cancellationToken.set_false()  # stop light flashing after home
                thread.join()
            ctx.set_rail_lights(True)
            pip.reset_tipracks()
            pick_up(pip)

    # mapping
    water = reservoir.wells()[0]
    buffer_A = buffer_plate.rows()[0][0]
    buffer_B = buffer_plate.rows()[0][1]

    pool_wells_left = barcode_plate.rows()[0][1:6]
    pool_wells_right = barcode_plate.rows()[0][6:11]
    pool_dest_left = barcode_plate.rows()[0][0]
    pool_dest_right = barcode_plate.rows()[0][11]

    pool_wells_left_bottom = barcode_plate.rows()[4][1:6]
    pool_wells_right_bottom = barcode_plate.rows()[4][6:11]
    pool_dest_left_bottom = barcode_plate.rows()[4][0]
    pool_dest_right_bottom = barcode_plate.rows()[4][11]

    csv_rows = [[val.strip() for val in line.split(',')]
                for line in csv_samp.splitlines()
                if line.split(',')[0].strip()][1:]

    num_chan = 4
    tips_ordered = [
        tip for rack in tipbox_less_than_eight
        for row in rack.rows()[
            len(rack.rows())-num_chan::-1*num_chan]
        for tip in row]

    tip_count = 0

    def pick_up_less():
        nonlocal tip_count
        m20.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # protocol
    ctx.comment('\n------------ADDING WATER TO FINAL PLATE-------------\n\n')
    p20.pick_up_tip()
    for line in csv_rows:
        dest_well_name = line[0]
        dest_well = final_plate.wells_by_name()[dest_well_name]
        transfer_vol = round(float(line[4]))

        if transfer_vol <= 0:
            continue
        p20.transfer(transfer_vol, water, dest_well.bottom(z=1.5),
                     new_tip='never')
        p20.blow_out()

    p20.drop_tip()

    ctx.comment('\n------------ADDING DNA TO FINAL PLATE-------------\n\n')

    for line in csv_rows:
        p20.pick_up_tip()
        source_well_name = line[0]
        source_well = dna_plate.wells_by_name()[source_well_name]

        dest_well_name = line[0]
        dest_well = final_plate.wells_by_name()[dest_well_name]
        transfer_vol = round(float(line[3]))

        p20.transfer(transfer_vol, source_well, dest_well.bottom(z=1.5),
                     new_tip='never')

        p20.blow_out()
        p20.drop_tip()

    ctx.pause()

    ctx.comment('\n----------ADDING SAMPLE TO BARCODE PLATE-----------\n\n')
    # are we for sure 96 samples
    if if_48 == "96":

        for s_col, d_col in zip(final_plate.rows()[0],
                                barcode_plate.rows()[0]):
            pick_up(m20)
            m20.aspirate(6, s_col.bottom(-0.5))
            m20.dispense(6, d_col)
            m20.mix(10, 8, d_col)
            m20.blow_out()
            m20.drop_tip()

    elif if_48 == "top48":

        for s_col, d_col in zip(final_plate.rows()[0],
                                barcode_plate.rows()[0]):
            pick_up_less()
            m20.aspirate(6, s_col)
            m20.dispense(6, d_col)
            m20.mix(10, 8, d_col)
            m20.blow_out()
            m20.drop_tip()
    else:

        for s_col, d_col in zip(final_plate.rows()[0],
                                barcode_plate.rows()[4]):
            pick_up_less()
            m20.aspirate(6, s_col)
            m20.dispense(6, d_col)
            m20.mix(10, 8, d_col)
            m20.blow_out()
            m20.drop_tip()

    ctx.comment('\n----------ADDING BUFFER A TO BARCODE PLATE-----------\n\n')
    if if_48 == "96":
        for col in barcode_plate.rows()[0]:
            pick_up(m20)
            m20.aspirate(5, buffer_A)
            m20.dispense(5, col)
            m20.mix(10, 8, col)
            m20.blow_out()
            m20.drop_tip()
    elif if_48 == "top48":
        for col in barcode_plate.rows()[0]:
            pick_up_less()
            m20.aspirate(5, buffer_A)
            m20.dispense(5, col)
            m20.mix(10, 8, col)
            m20.blow_out()
            m20.drop_tip()
    else:
        for col in barcode_plate.rows()[4]:
            pick_up_less()
            m20.aspirate(5, buffer_A)
            m20.dispense(5, col)
            m20.mix(10, 8, col)
            m20.blow_out()
            m20.drop_tip()

    ctx.pause()

    ctx.comment('\n----------ADDING BUFFER B TO BARCODE PLATE-----------\n\n')
    if if_48 == "96":
        for col in barcode_plate.rows()[0]:
            pick_up(m20)
            m20.aspirate(7.5, buffer_B, rate=0.2)
            ctx.delay(seconds=1.5)
            m20.dispense(7.5, col)
            m20.mix(10, 14, col, rate=0.5)
            m20.blow_out()
            m20.drop_tip()

    elif if_48 == "top48":
        for col in barcode_plate.rows()[0]:
            pick_up_less()
            m20.aspirate(7.5, buffer_B, rate=0.2)
            ctx.delay(seconds=1.5)
            m20.dispense(7.5, col)
            m20.mix(10, 14, col, rate=0.5)
            m20.blow_out()
            m20.drop_tip()

    else:
        for col in barcode_plate.rows()[4]:
            pick_up_less()
            m20.aspirate(7.5, buffer_B, rate=0.2)
            ctx.delay(seconds=1.5)
            m20.dispense(7.5, col)
            m20.mix(10, 14, col, rate=0.5)
            m20.blow_out()
            m20.drop_tip()

    ctx.pause("Second buffer just added to plate. Resume for pooling.")

    ctx.comment('\n----------POOLING-----------\n\n')
    # are we for sure 96 samples
    if if_48 == "96":

        for side_of_plate, pool_well in zip([pool_wells_left,
                                             pool_wells_right],
                                            [pool_dest_left,
                                             pool_dest_right]):
            pick_up(m20)
            for col in side_of_plate:
                for _ in range(2):
                    m20.aspirate(12, col)
                    m20.dispense(12, pool_well)
                    m20.blow_out()
            m20.drop_tip()

    elif if_48 == "top48":

        for side_of_plate, pool_well in zip([pool_wells_left,
                                             pool_wells_right],
                                            [pool_dest_left,
                                             pool_dest_right]):
            pick_up_less()
            for col in side_of_plate:
                for _ in range(2):
                    m20.aspirate(12, col)
                    m20.dispense(12, pool_well)
                    m20.blow_out()
            m20.drop_tip()

    else:

        for side_of_plate, pool_well in zip([pool_wells_left_bottom,
                                             pool_wells_right_bottom],
                                            [pool_dest_left_bottom,
                                             pool_dest_right_bottom]):
            pick_up_less()
            for col in side_of_plate:
                for _ in range(2):
                    m20.aspirate(12, col)
                    m20.dispense(12, pool_well)
                    m20.blow_out()
            m20.drop_tip()
