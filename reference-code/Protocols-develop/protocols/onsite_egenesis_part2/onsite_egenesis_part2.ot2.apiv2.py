import threading
from time import sleep
from opentrons import types
from opentrons import protocol_api

metadata = {
    'protocolName': 'Ligation Sequencing Amplicons Native Barcoding',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
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
    """FLASH SETUP."""
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

    [num_samp, barcode_well_start] = get_values(  # noqa: F821
        "num_samp", "barcode_well_start")

    # num_samp = 24
    flash = True
    # barcode_well_start = 4

    barcode_well_start -= 1

    if not 2 <= num_samp <= 24:
        raise Exception("Enter a sample number between 2-24")

    # labware
    barcode_plate = ctx.load_labware('barcode_96_wellplate_200ul', 1)
    bcode_well = barcode_plate.wells()[barcode_well_start]
    ctx.comment(f'barcode well starts {bcode_well}')

    mag_mod = ctx.load_module('magnetic module gen2', 6)
    mag_plate = mag_mod.load_labware('axygen_96_wellplate_2000ul')
    mag_mod.disengage()

    sample_plate = ctx.load_labware('eppendorf_96_wellplate_200ul', 4)
    sample_plus_barcode_plate = ctx.load_labware('eppendorf_96_wellplate_200ul', 2)  # noqa:E501

    reag_rack = ctx.load_labware('opentrons_24_aluminumblock_nest_1.5ml_screwcap', 5)  # noqa:E501

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in [8, 9]]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in [10]]

    reservoir = ctx.load_labware('usascientific_12_reservoir_22ml', 3)

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', 'left', tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'right',
                               tip_racks=[tips300[0]])
    m300.well_bottom_clearance.aspirate = 1.2
    m300.well_bottom_clearance.dispense = 1.2

    # PICK UP ONE TIP WITH P300 MULTI PIPETTE ######################
    num_chan = 1
    tips_ordered = [
        tip
        for rack in tips300
        for row in rack.rows()[
            len(tips300[0].rows())-num_chan::-1*num_chan]
        for tip in row]

    tip_count = 0

    def pick_up_one():
        current = 0.1
        ctx._hw_manager.hardware._attached_instruments[types.Mount.RIGHT].update_config_item('pick_up_current', current)  # noqa: E501
        nonlocal tip_count
        m300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    def pick_up_20():
        try:
            p20.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pause_and_flash(f"Replace empty tip rack for {p20}")
            p20.reset_tipracks()
            p20.pick_up_tip()

    def pause_and_flash(msg):
        if flash:
            if not ctx._hw_manager.hardware.is_simulator:
                cancellationToken.set_true()
            thread = create_thread(ctx, cancellationToken)
        ctx.home()
        ctx.pause(msg)
        if flash:
            cancellationToken.set_false()  # stop light flashing after home
            thread.join()
            ctx.set_rail_lights(True)

    # apply speed limit to departing tip
    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # REAGENT MAPPING ####################################################

    blunt_ta_and_water = reag_rack.rows()[1][0]  # B1
    beads = reag_rack.rows()[1][1]  # B2
    native_adapter = reag_rack.rows()[2][0]  # C1
    reaction_buff_5x = reag_rack.rows()[2][1]  # C2
    t4_ligase = reag_rack.rows()[2][2]  # C3
    long_frag_buffer = reag_rack.rows()[3][0]  # D1
    elution_buffer = reag_rack.rows()[3][1]  # D2

    edta = reservoir.wells()[2].bottom(z=3)
    ethanol = reservoir.wells()[1].bottom(z=3)
    nuc_free_water = reservoir.wells()[0].bottom(z=3)
    trash = reservoir.wells()[-1].top(z=-3)

    # PROTOCOL ####################################################
    ctx.comment('\n-------------------MAKING FIRST MIX-------------------\n\n')
    mix_row = reag_rack.rows()[0][:3]
    reag1_vols = [1, 1.75, 0.75]  # diluted dna, ultra rxn buff, ultra enzyme mix   # noqa:E501
    mix_tube = sample_plate.wells()[-1]  # h12
    mix_vol_ctr = 0

    for i, (tube, volume) in enumerate(zip(mix_row, reag1_vols)):
        reag_vol = volume*num_samp*1.15
        if reag_vol > 20:
            pick_up_one()
            pip = m300
        else:
            pick_up_20()
            pip = p20

        pip.aspirate(reag_vol, tube, rate=0.5)
        slow_tip_withdrawal(pip, tube)
        pip.touch_tip(v_offset=-5)
        pip.dispense(reag_vol, mix_tube)
        pip.drop_tip()

        mix_vol_ctr += reag_vol
    ctx.comment('\n\n\n')

    ctx.comment('\n--MIXING AND DISTRIBUTING MIX--\n\n')

    if 0.8*mix_vol_ctr <= 20:
        pick_up_20()
        p20.mix(15, 0.8*mix_vol_ctr, mix_tube)
        slow_tip_withdrawal(p20, mix_tube)
        p20.touch_tip()
        p20.drop_tip()
    else:
        pick_up_one()
        m300.mix(15, 0.8*mix_vol_ctr, mix_tube)
        slow_tip_withdrawal(m300, mix_tube)
        m300.touch_tip()
        m300.drop_tip()
    ctx.comment('\n\n\n')

    for samp in sample_plate.wells()[:num_samp]:
        pick_up_20()
        p20.aspirate(3.5, mix_tube)
        p20.dispense(3.5, samp)
        p20.mix(3, 10, samp)
        slow_tip_withdrawal(p20, samp)
        p20.touch_tip(v_offset=-10)
        p20.drop_tip()

    pause_and_flash("""
                       Ensure the components are thoroughly mixed by pipetting
                       and spin down in a centrifuge.

                       Using a thermal cycler,
                       incubate at 20°C for 5 minutes and 65°C for 5 minutes.
                       """)

    ctx.comment('\n---------------DISTRIBUTING BARCODE------------------\n\n')

    # add blunt ta + nuc water to fresh plate
    pick_up_20()
    for well in sample_plus_barcode_plate.wells()[:num_samp]:

        p20.aspirate(7.75, blunt_ta_and_water, rate=0.2)
        p20.dispense(7.75, well)
    p20.drop_tip()
    ctx.comment('\n\n\n')

    # add barcode to fresh plate
    for s, d in zip(
                    barcode_plate.wells()[
                                          barcode_well_start:barcode_well_start+num_samp  # noqa: E501
                                          ],
                    sample_plus_barcode_plate.wells()):
        pick_up_20()
        # p20.touch_tip(s, v_offset=-10, radius=0.2)
        p20.aspirate(1.25, s, rate=0.4)
        p20.dispense(1.25, d, rate=0.4)
        p20.touch_tip(v_offset=-12)
        p20.drop_tip()
    ctx.comment('\n\n\n')

    # add sample to plate
    for s, d in zip(sample_plate.wells()[:num_samp],
                    sample_plus_barcode_plate.wells()):
        pick_up_20()
        p20.aspirate(1, s, rate=0.4)
        p20.dispense(1, d, rate=0.4)
        p20.mix(3, 7, d)  # do I add a mix step here?
        p20.touch_tip(v_offset=-12)
        p20.drop_tip()
    ctx.comment('\n\n\n')

    ctx.delay(minutes=20)  # 20 minutes

    # add edta
    for samp in sample_plus_barcode_plate.wells()[:num_samp]:
        pick_up_20()
        p20.aspirate(1, edta, rate=0.4)
        p20.dispense(1, samp, rate=0.4)
        p20.mix(1, 7, samp)  # do I add a mix step here?
        p20.touch_tip(v_offset=-12)
        p20.drop_tip()

    ctx.comment('\n---------------POOLING SAMPLES------------------\n\n')

    pool_well = mag_plate.wells()[0]

    pick_up_20()
    for samp in sample_plus_barcode_plate.wells()[:num_samp]:
        p20.aspirate(10, samp, rate=0.4)
        p20.dispense(10, pool_well, rate=0.4)
        p20.touch_tip(v_offset=-12)
    p20.drop_tip()

    ctx.comment('\n---------TRANSFERRING BEADS TO PLATE-----------\n\n')

    bead_vol = 4*num_samp

    pick_up_one()
    m300.mix(15, 200, beads)

    if bead_vol >= 20:
        pip = m300
    else:
        pip = p20
        slow_tip_withdrawal(m300, beads)
        m300.touch_tip(v_offset=-10)
        m300.drop_tip()
        pick_up_20()

    pip.aspirate(bead_vol, beads, rate=0.5)
    slow_tip_withdrawal(pip, beads)
    pip.touch_tip(v_offset=-15)
    pip.dispense(bead_vol, pool_well)
    pip.drop_tip()
    bead_and_samp_vol = num_samp*10+bead_vol
    if bead_and_samp_vol*0.9 >= 20:
        if not m300.has_tip:
            pick_up_one()
            m300.mix(15,
                     bead_and_samp_vol*0.9 if bead_and_samp_vol*0.9 <= 200 else 200,  # noqa:E501
                     pool_well)
            slow_tip_withdrawal(m300, pool_well)
            m300.touch_tip(v_offset=-15)

    else:
        if not p20.has_tip:
            pick_up_20()
            p20.mix(15, bead_and_samp_vol*0.9 if bead_and_samp_vol*0.9 <= 20 else 20, pool_well)  # noqa:E501
            slow_tip_withdrawal(p20, pool_well)
            p20.touch_tip(v_offset=-15)
            p20.drop_tip()

    ctx.comment('\n---------INCUBATING-----------\n\n')

    if not m300.has_tip:
        pick_up_one()
    for _ in range(4):
        m300.mix(5, 0.9*bead_and_samp_vol if bead_and_samp_vol <= 200 else 200, pool_well)  # noqa:E501
        m300.aspirate(bead_and_samp_vol if bead_and_samp_vol <= 200 else 200, pool_well)  # noqa:E501
        slow_tip_withdrawal(m300, pool_well)
        m300.move_to(pool_well.top(z=-5))
        ctx.delay(seconds=120)  # 120 seconds
        m300.dispense(bead_and_samp_vol if bead_and_samp_vol <= 200 else 200, pool_well)  # noqa:E501

    slow_tip_withdrawal(m300, pool_well)
    m300.touch_tip(v_offset=-15)
    m300.drop_tip()
    ctx.delay(seconds=60)

    mag_mod.engage(height_from_base=3)
    ctx.delay(minutes=5.5)

    ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')

    pick_up_one()
    if bead_and_samp_vol <= 200:
        m300.aspirate(bead_and_samp_vol, pool_well, rate=0.1)
        m300.touch_tip()
        m300.dispense(bead_and_samp_vol, trash)
        m300.blow_out()
        m300.touch_tip()
    else:
        aspirate_vol = bead_and_samp_vol / 2
        for _ in range(2):
            m300.aspirate(aspirate_vol, pool_well, rate=0.1)
            m300.touch_tip()
            m300.dispense(aspirate_vol, trash)
            m300.blow_out()
            m300.touch_tip()

    m300.aspirate(20, pool_well.bottom(z=0.5), rate=0.05)
    m300.dispense(20, trash)
    m300.blow_out()
    m300.touch_tip()
    m300.drop_tip()

    ctx.comment('\n----------------TWO ETHANOL WASHES-----------\n\n')

    for _ in range(2):

        pick_up_one()

        for _ in range(4):
            m300.aspirate(175, ethanol, rate=0.8)
            slow_tip_withdrawal(m300, reservoir.wells()[1])
            m300.touch_tip()
            m300.dispense(175, pool_well.top(z=-2))
            m300.blow_out()

        ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')
        for _ in range(3):
            m300.aspirate(200, pool_well, rate=0.1)
            m300.touch_tip()
            m300.dispense(200, trash)
            m300.blow_out()
            m300.touch_tip()

        m300.aspirate(100, pool_well, rate=0.1)
        m300.touch_tip()
        m300.dispense(100, trash)
        m300.blow_out()
        m300.touch_tip()

        m300.aspirate(20, pool_well.bottom(z=0.5), rate=0.05)
        m300.touch_tip()
        m300.dispense(20, trash)
        m300.blow_out()
        m300.touch_tip()

        m300.drop_tip()

    ctx.delay(seconds=30)  # ethanol dry

    mag_mod.disengage()

    ctx.comment('\n---------ADDING NUC FREE WATER-----------\n\n')

    pick_up_one()
    m300.aspirate(35, nuc_free_water)
    m300.dispense(35, pool_well)
    m300.mix(15, 20, pool_well)
    slow_tip_withdrawal(m300, pool_well)
    m300.touch_tip(v_offset=-15)
    m300.drop_tip()

    ctx.comment('\n---------INCUBATING-----------\n\n')

    pick_up_one()
    for _ in range(4):
        m300.mix(3, 30, pool_well)
        m300.aspirate(35, pool_well)
        slow_tip_withdrawal(m300, pool_well)
        m300.move_to(pool_well.top(z=-5))
        ctx.delay(seconds=120)  # 120 seconds
        m300.dispense(35, pool_well)
    slow_tip_withdrawal(m300, pool_well)
    m300.touch_tip(v_offset=-15)
    m300.drop_tip()
    ctx.delay(seconds=60)  # 60

    mag_mod.engage(height_from_base=3)
    ctx.delay(minutes=3)

    ctx.comment('\n---------TRANSFERRING TO FRESH WELL-----------\n\n')

    pick_up_one()
    m300.aspirate(30, pool_well, rate=0.1)
    pool_well = mag_plate.wells()[1]
    m300.dispense(30, pool_well)
    m300.drop_tip()

    mag_mod.disengage()

    ctx.comment('\n---------ADDING FINAL MIX-----------\n\n')

    mix_volumes = [5, 10, 5]
    reags = [native_adapter, reaction_buff_5x, t4_ligase]

    for reag, vol in zip(reags, mix_volumes):
        pick_up_20()
        p20.aspirate(vol, reag)
        slow_tip_withdrawal(p20, tube)
        p20.dispense(vol, pool_well)
        p20.mix(2, 20, pool_well)
        slow_tip_withdrawal(p20, pool_well)
        p20.touch_tip()
        p20.drop_tip()

    ctx.delay(minutes=20)

    ctx.comment('\n---------TRANSFERRING BEADS TO PLATE-----------\n\n')

    bead_vol = 20

    pick_up_one()
    m300.mix(15, 200, beads)

    m300.aspirate(bead_vol, beads, rate=0.5)
    slow_tip_withdrawal(m300, beads)
    m300.touch_tip(v_offset=-15)
    m300.dispense(bead_vol, pool_well)
    bead_and_samp_vol = 50+bead_vol
    m300.mix(20,
             bead_and_samp_vol*0.8,
             pool_well)
    slow_tip_withdrawal(m300, pool_well)
    m300.touch_tip(v_offset=-15)

    ctx.comment('\n---------INCUBATING-----------\n\n')

    for _ in range(4):
        m300.mix(3, 45, pool_well)
        m300.aspirate(50, pool_well)
        slow_tip_withdrawal(m300, pool_well)
        m300.move_to(pool_well.top(z=-5))
        ctx.delay(seconds=120)  # 120 seconds
        m300.dispense(50, pool_well)
    slow_tip_withdrawal(m300, pool_well)
    m300.touch_tip(v_offset=-15)
    m300.drop_tip()
    ctx.delay(seconds=60)

    mag_mod.engage(height_from_base=3)
    ctx.delay(minutes=3)

    ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')

    pick_up_one()
    m300.aspirate(50, pool_well, rate=0.1)
    m300.aspirate(20, pool_well.bottom(z=0.5), rate=0.01)
    m300.touch_tip()
    m300.dispense(70, trash)
    m300.blow_out()
    m300.touch_tip()
    m300.drop_tip()

    ctx.comment('\n----------------TWO WASHES-----------\n\n')

    for _ in range(2):

        pick_up_one()
        m300.aspirate(125, long_frag_buffer)
        slow_tip_withdrawal(m300, long_frag_buffer)
        m300.touch_tip()
        m300.dispense(125, pool_well.top(z=-2), rate=0.5)
        m300.move_to(pool_well.top())
        mag_mod.disengage()
        m300.mix(15, 125, pool_well)
        slow_tip_withdrawal(m300, pool_well)
        m300.touch_tip()
        mag_mod.engage(height_from_base=3)
        ctx.delay(minutes=3)

        ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')

        m300.aspirate(125, pool_well, rate=0.1)
        m300.aspirate(20, pool_well.bottom(z=0.5), rate=0.01)
        m300.touch_tip()
        m300.dispense(145, trash)
        m300.blow_out()
        m300.touch_tip()
        m300.drop_tip()

    mag_mod.disengage()

    ctx.comment('\n---------ADDING NUC FREE WATER-----------\n\n')

    pick_up_20()
    p20.aspirate(15, elution_buffer)
    p20.dispense(15, pool_well)
    p20.mix(15, 15, pool_well)
    p20.mix(5, 20, pool_well, rate=1.3)
    slow_tip_withdrawal(p20, pool_well)
    p20.blow_out()
    p20.touch_tip(v_offset=-15)
    p20.drop_tip()

    ctx.comment('\n---------INCUBATING-----------\n\n')

    pick_up_one()
    for _ in range(4):
        m300.mix(3, 15, pool_well)
        m300.aspirate(15, pool_well)
        slow_tip_withdrawal(m300, pool_well)
        m300.move_to(pool_well.top(z=-5))
        ctx.delay(seconds=120)  # 120 seconds
        m300.dispense(15, pool_well)
    slow_tip_withdrawal(m300, pool_well)
    m300.touch_tip(v_offset=-15)
    m300.drop_tip()
    ctx.delay(seconds=60)  # 60

    mag_mod.engage(height_from_base=3)
    ctx.delay(minutes=3)

    ctx.comment('\n---------TRANSFERRING TO FRESH WELL-----------\n\n')

    pick_up_20()
    p20.aspirate(15, pool_well, rate=0.01)
    p20.aspirate(5, pool_well.bottom(z=0.5), rate=0.1)
    pool_well = mag_plate.wells()[2]
    p20.dispense(20, pool_well)
    p20.drop_tip()
    mag_mod.disengage()
