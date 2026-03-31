import threading
from time import sleep
from opentrons import types

metadata = {
    'protocolName': 'Nanoporo Direct RNA Sequencing',
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

    [num_samp] = get_values(  # noqa: F821
        "num_samp")
    #
    # num_samp = 2
    test_mode = False
    flash = True

    if not 2 <= num_samp <= 8:
        raise Exception("Enter a sample number between 1-8")

    # labware

    mag_mod = ctx.load_module('magnetic module gen2', 6)
    mag_plate = mag_mod.load_labware('eppendorf_96_wellplate_200ul')
    qubit_plate = ctx.load_labware('eppendorf_96_wellplate_200ul', 1)
    mag_mod.disengage()

    sample_rack = ctx.load_labware('opentrons_24_aluminumblock_nest_1.5ml_screwcap', 4)  # noqa:E501
    reag_rack = ctx.load_labware('opentrons_24_aluminumblock_nest_1.5ml_screwcap', 5)  # noqa:E501

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in [9]]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in [10, 11]]

    reservoir = ctx.load_labware('usascientific_12_reservoir_22ml', 3)

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', 'left', tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'right', tip_racks=tips300)
    m300.well_bottom_clearance.aspirate = 1.5
    m300.well_bottom_clearance.dispense = 1.5

    # PICK UP ONE TIP WITH P300 MULTI PIPETTE ######################

    num_chan = 1
    tips_ordered = [
        tip
        for row in tips300[0].rows()[
            len(tips300[0].rows())-num_chan::-1*num_chan]
        for tip in row]

    tip_count = 0

    def pick_up_one():

        current = 0.1
        ctx._hw_manager.hardware._attached_instruments[types.Mount.RIGHT].update_config_item('pick_up_current', current)  # noqa: E501
        nonlocal tip_count
        m300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # pick up multiple with p300

    num_chan2 = num_samp
    tips_ordered2 = [
        tip
        for row in tips300[1].rows()[
            len(tips300[1].rows())-num_chan2::-1*num_chan2]
        for tip in row]

    # PICK UP MULTIPLE TIPS WITH P300 MULTI PIPETTE ######################

    tip_count2 = 0

    def pick_up_multi():
        current = 0.1*num_samp
        ctx._hw_manager.hardware._attached_instruments[types.Mount.RIGHT].update_config_item('pick_up_current', current)  # noqa: E501
        nonlocal tip_count2
        if tip_count2 == len(tips_ordered2):
            pause_and_flash("Replace empty tips")
            tip_count2 = 0
        m300.pick_up_tip(tips_ordered2[tip_count2])
        tip_count2 += 1

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

    def drop_tips():
        if p20.has_tip:
            p20.drop_tip()
        if m300.has_tip:
            m300.drop_tip()

    # reagent mapping
    samples = mag_plate.wells()[:num_samp]
    sample_col = mag_plate.wells()[0]

    rna_tubes = [well for row in sample_rack.rows() for well in row][:num_samp]
    beads = reag_rack.rows()[0][1]  # A2
    reverse_transcrip = reag_rack.wells()[0]  # A1
    ethanol = reservoir.wells()[1]
    wash_buffer = reag_rack.rows()[0][4:]*24  # A5 A6
    nuc_free_water = reservoir.wells()[0]  # A1 of reservoir
    trash = reservoir.wells()[-1]
    elution_buffer = sample_rack.wells()[-1]  # D6 sample rack

    mag_location_well = mag_plate.wells()[0]

    # protocol
    ctx.comment('\n-------------------MAKING FIRST MIX-------------------\n\n')
    mix_row = reag_rack.rows()[1][:5]
    mix_tube = reag_rack.rows()[1][5]
    reag1_vols = [3, 0.5, 1, 1.5]  # neb_next, rna_cs, rt_adaptor, t4_ligase
    mix_vol_ctr = 0

    for i, (tube, volume) in enumerate(zip(mix_row, reag1_vols)):
        reag_vol = volume*num_samp*1.15
        p20.pick_up_tip()
        if reag_vol > 20:
            reag_vol /= 2
            for _ in range(2):
                p20.aspirate(reag_vol, tube, rate=0.5)
                slow_tip_withdrawal(p20, tube)
                p20.dispense(reag_vol, mix_tube)
        else:
            p20.aspirate(reag_vol, tube)
            slow_tip_withdrawal(p20, tube)
            p20.touch_tip(v_offset=-5)
            p20.dispense(reag_vol, mix_tube)
        if i <= 2:
            p20.drop_tip()

        mix_vol_ctr += reag_vol
        ctx.comment('\n')

    ctx.comment('\n--MIXING AND DISTRIBUTING MIX--\n\n')

    p20.mix(20, 0.8*mix_vol_ctr if 0.8*mix_vol_ctr <= 20 else 20, mix_tube)

    for rna_tube in rna_tubes:
        if not p20.has_tip:
            p20.pick_up_tip()
        p20.aspirate(6, mix_tube)
        p20.dispense(6, rna_tube)
        p20.mix(3, 10, rna_tube)
        p20.blow_out(rna_tube.top())
        p20.touch_tip(v_offset=-5)
        p20.drop_tip()

    ctx.delay(seconds=10 if test_mode else 600)

    ctx.comment('\n---------------MAKING SECOND MIX----------------------\n\n')
    mix2_row = reag_rack.rows()[2][:5]
    mix2_tube = reag_rack.rows()[2][5]
    reag2_vols = [9, 2, 8, 4]  # nuc water, dntps, first strand buff, dtt
    mix2_vol_ctr = 0

    for i, (tube, volume) in enumerate(zip(mix2_row, reag2_vols)):
        reag_vol = volume*num_samp*1.15
        if reag_vol > 20:
            pick_up_one()
            pip = m300
        else:
            p20.pick_up_tip()
            pip = p20

        pip.aspirate(reag_vol, tube, rate=0.5)
        slow_tip_withdrawal(pip, tube)
        pip.touch_tip(v_offset=-5)
        pip.dispense(reag_vol, mix2_tube)
        if i <= 2:
            pip.drop_tip()

        mix2_vol_ctr += reag_vol
        ctx.comment('\n')
    if p20.has_tip:
        p20.drop_tip()

    ctx.comment('\n--MIXING & DISTRIBUTING MIX--\n\n')

    if not m300.has_tip:
        pick_up_one()
    m300.mix(15, 0.8*mix2_vol_ctr, mix2_tube)

    for rna_tube in rna_tubes:
        if not m300.has_tip:
            pick_up_one()
        m300.aspirate(23, mix2_tube)
        m300.dispense(23, rna_tube)
        m300.mix(3, 30, rna_tube)
        m300.blow_out(rna_tube.top())
        m300.touch_tip(v_offset=-5)
        m300.drop_tip()

    ctx.comment('\n-------------ADDING REVERSE TRANSCRIP----------------\n\n')

    for rna_tube in rna_tubes:
        p20.pick_up_tip()
        p20.aspirate(2, reverse_transcrip, rate=0.5)
        p20.dispense(2, rna_tube)
        p20.mix(2, 20, rna_tube)  # increase mixing here?
        p20.drop_tip()

    ctx.comment('\n---------TRANSFERRING SAMPLES TO PLATE-----------\n\n')
    for rna_tube, well in zip(rna_tubes, mag_plate.wells()):
        pick_up_one()
        m300.aspirate(38, rna_tube)
        m300.dispense(38, well)
        m300.drop_tip()

    pause_and_flash('''

    Place plate on magnetic module in a thermoycler and
    incubate at 50°C for 50 min, then 70°C for 10 min,
    and bring the sample to 4°C before proceeding to
    the next step. Put plate back on magnetic module.

    ''')

    ctx.comment('\n---------TRANSFERRING BEADS TO PLATE-----------\n\n')
    pick_up_one()
    m300.mix(15, 200, beads)

    for well in samples:
        if not m300.has_tip:
            pick_up_one()
        m300.aspirate(72, beads, rate=0.6)
        slow_tip_withdrawal(m300, beads)
        m300.touch_tip(v_offset=-5)
        m300.dispense(72, well, rate=0.6)
        slow_tip_withdrawal(m300, well)
        m300.drop_tip()

    ctx.comment('\n---------INCUBATING-----------\n\n')

    pick_up_multi()
    for _ in range(4):
        m300.mix(5, 75, sample_col)
        m300.aspirate(100, sample_col.bottom(z=1.3))
        slow_tip_withdrawal(m300, mag_plate.rows()[0][0])
        m300.move_to(mag_plate.rows()[0][0].top(z=-5))
        ctx.delay(seconds=6 if test_mode else 60)  # 60 seconds
        m300.dispense(100, sample_col)
    slow_tip_withdrawal(m300, mag_plate.rows()[0][0])
    m300.blow_out(mag_plate.rows()[0][0].top(z=-5))
    m300.touch_tip(v_offset=-5)
    m300.drop_tip()

    mag_mod.engage(height_from_base=5)
    ctx.delay(minutes=3)

    ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')

    pick_up_multi()
    m300.aspirate(110, sample_col, rate=0.1)
    m300.aspirate(10, sample_col.bottom(z=1.3), rate=0.05)
    m300.aspirate(10, sample_col.bottom(z=1.1), rate=0.05)

    m300.dispense(130, trash)
    m300.blow_out()
    m300.drop_tip()

    ctx.comment('\n----------------ADDING ETHANOL-----------\n\n')

    pick_up_multi()
    m300.aspirate(150, ethanol)
    slow_tip_withdrawal(m300, ethanol)
    m300.dispense(150, sample_col)
    ctx.delay(seconds=3)

    ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')

    m300.aspirate(150, sample_col, rate=0.1)
    m300.aspirate(10, sample_col.bottom(z=1.3), rate=0.1)
    m300.aspirate(10, sample_col.bottom(z=1.1), rate=0.1)

    m300.dispense(170, trash)
    m300.blow_out()
    m300.drop_tip()

    mag_mod.disengage()

    # pause_and_flash("""
    #                    Spin down magnetic plate.
    #                    Pipette any excess ethanol.
    #                    Place magnetic plate back on magnetic module.
    #                    """)

    ctx.comment('\n---------ADDING NUC FREE WATER-----------\n\n')

    pick_up_multi()
    m300.aspirate(20, nuc_free_water)
    m300.dispense(20, sample_col)
    m300.mix(15, 20, sample_col)
    slow_tip_withdrawal(m300, sample_col)
    m300.touch_tip(v_offset=-5)
    m300.drop_tip()

    mag_mod.engage(height_from_base=5)
    ctx.delay(minutes=3)

    ctx.comment('\n---------TRANSFERRING TO FRESH COLUMN-----------\n\n')

    pick_up_multi()
    m300.aspirate(20, sample_col.bottom(z=1.3), rate=0.1)
    m300.dispense(20, mag_plate.rows()[0][2])
    m300.aspirate(20, sample_col, rate=0.1)
    m300.aspirate(20, sample_col.bottom(z=1.1), rate=0.1)
    m300.aspirate(20, sample_col.bottom(z=1), rate=0.1)
    m300.dispense(60, mag_plate.rows()[0][2].top(z=-4))
    m300.blow_out(mag_plate.rows()[0][2].top())
    m300.touch_tip()
    m300.drop_tip()

    samples_by_well = mag_plate.columns()[2][:num_samp]
    sample_col = mag_plate.rows()[0][2]
    mag_mod.disengage()

    ctx.comment('\n---------------MAKING THIRD MIX----------------------\n\n')
    mix3_row = reag_rack.rows()[3][:5]
    mix3_tube = reag_rack.rows()[3][5]
    reag3_vols = [8, 6, 3, 3]  # nebnext, adapter, water, t4
    mix3_vol_ctr = 0

    for i, (tube, volume) in enumerate(zip(mix3_row, reag3_vols)):
        reag_vol = volume*num_samp*1.15
        if reag_vol > 20:
            pick_up_one()
            pip = m300
        else:
            p20.pick_up_tip()
            pip = p20

        pip.aspirate(reag_vol, tube, rate=0.5)
        slow_tip_withdrawal(pip, tube)
        pip.touch_tip(v_offset=-5)
        pip.dispense(reag_vol, mix3_tube)

        if i <= 2:
            pip.drop_tip()

        mix3_vol_ctr += reag_vol
        ctx.comment('\n')
    if p20.has_tip:
        p20.drop_tip()

    ctx.comment('\n--MIXING & DISTRIBUTING MIX--\n\n')

    if not m300.has_tip:
        pick_up_one()
    m300.mix(15, 0.8*mix3_vol_ctr, mix3_tube)

    for sample in samples_by_well:
        if not m300.has_tip:
            pick_up_one()
        m300.aspirate(20, mix3_tube)
        m300.dispense(20, sample)
        m300.mix(3, 30, sample)
        m300.blow_out(sample.top())
        m300.touch_tip(v_offset=-5)
        m300.drop_tip()

    drop_tips()
    ctx.delay(seconds=10 if test_mode else 600)

    ctx.comment('\n---------TRANSFERRING BEADS TO PLATE-----------\n\n')

    pick_up_one()
    m300.mix(15, 200, beads)

    for well in samples_by_well:
        if not m300.has_tip:
            pick_up_one()
        m300.aspirate(40, beads, rate=0.6)
        slow_tip_withdrawal(m300, beads)
        m300.touch_tip(v_offset=-5)
        m300.dispense(40, well, rate=0.6)
        slow_tip_withdrawal(m300, well)
        m300.drop_tip()

    pick_up_multi()
    m300.mix(15, 60, sample_col)
    m300.drop_tip()

    pick_up_multi()
    for _ in range(4):
        m300.mix(5, 75, sample_col)
        m300.aspirate(70, sample_col.bottom(z=1.3))
        slow_tip_withdrawal(m300, sample_col)
        m300.move_to(mag_plate.rows()[0][2].top(z=-3))
        ctx.delay(seconds=6 if test_mode else 60)  # 60 seconds
        m300.dispense(70, sample_col)
    m300.drop_tip()

    mag_mod.engage(height_from_base=5)
    ctx.delay(minutes=3)

    ctx.comment('\n---------REMOVING SUPERNATANT-----------\n\n')

    pick_up_multi()
    m300.aspirate(80, sample_col, rate=0.05)
    m300.aspirate(10, sample_col.bottom(z=1.3), rate=0.05)
    m300.aspirate(10, sample_col.bottom(z=1.1), rate=0.05)
    m300.dispense(100, trash)
    m300.blow_out()
    m300.drop_tip()

    ctx.comment('\n---------ADD WASH BUFFER RESUSPEND BEADS-----------\n\n')

    for _ in range(1 if test_mode else 2):

        # add wash buffer
        pick_up_one()
        for wash, well in zip(wash_buffer, mag_plate.columns()[2][:num_samp]):
            m300.aspirate(150, wash)
            m300.touch_tip(v_offset=-8)
            m300.dispense(150, well.top())
            ctx.delay(seconds=2)
            m300.blow_out()
        m300.drop_tip()

        # resuspend beads
        mag_mod.disengage()

        pick_up_multi()
        for _ in range(25):
            m300.aspirate(140, sample_col.bottom().move(types.Point(x=0, y=0,
                                                                    z=1.3)))
            m300.dispense(140,
                          sample_col.bottom().move(types.Point(x=mag_location_well.diameter/2-1, y=0, z=mag_location_well.depth/2)),  # noqa:E501
                          rate=1.5)

        m300.drop_tip()

        mag_mod.engage(height_from_base=5)
        ctx.delay(minutes=3)

        # remove super
        pick_up_multi()
        m300.aspirate(150, sample_col, rate=0.1)
        m300.aspirate(10, sample_col.bottom(z=1.3), rate=0.05)
        m300.dispense(160, trash)
        m300.blow_out()
        m300.drop_tip()
    mag_mod.disengage()
    drop_tips()

    ctx.comment('\n---------ADD ELUTION BUFFER, MOVE TO COL-----------\n\n')

    for well in samples_by_well:
        pick_up_one()
        m300.aspirate(21, elution_buffer)
        m300.dispense(21, well)
        slow_tip_withdrawal(m300, well)
        m300.drop_tip()

    pick_up_multi()
    m300.mix(20, 20, mag_plate.rows()[0][2])
    m300.drop_tip()

    ctx.delay(seconds=6 if test_mode else 600)

    mag_mod.engage(height_from_base=5)
    ctx.delay(minutes=3)

    pick_up_multi()
    m300.aspirate(21, sample_col.bottom(z=1.3), rate=0.1)
    m300.dispense(21, mag_plate.rows()[0][4])
    m300.aspirate(20, sample_col, rate=0.1)
    m300.aspirate(20, sample_col.bottom(z=1.1), rate=0.1)
    m300.aspirate(20, sample_col.bottom(z=1), rate=0.1)
    m300.dispense(60, mag_plate.rows()[0][4].top(z=-4))
    m300.blow_out(mag_plate.rows()[0][4].top())
    m300.touch_tip()

    m300.drop_tip()

    ctx.comment('\n---------ADDING QUBIT-----------\n\n')

    for source, dest in zip(
                            [well
                             for well in mag_plate.columns()[4]][:num_samp],
                            qubit_plate.columns()[0]):
        p20.pick_up_tip()
        p20.aspirate(2, source, rate=0.2)
        p20.dispense(2, dest)
        p20.drop_tip()
