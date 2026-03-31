import math
from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'Viral Nucleic Acid Isolation from Oral and Nasal swabs',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_col, samp_and_lys_rep, shake_well, incubate_bind_time,
     mag_engage_time, asp_height, asp_flow_rate, disp_flow_rate,
     length_from_side, bead_dry_time,
     bead_dry_time_nuc_water, nuc_free_water_vol_well, p20_mount,
     p300_mount] = get_values(  # noqa: F821
        "num_col", "samp_and_lys_rep", "shake_well", "incubate_bind_time",
        "mag_engage_time", "asp_height", "asp_flow_rate", "disp_flow_rate",
        "length_from_side", "bead_dry_time",
        "bead_dry_time_nuc_water", "nuc_free_water_vol_well", "p20_mount",
        "p300_mount")

    if not 1 <= num_col <= 12:
        raise Exception("Enter a number of columns between 1 and 12")
    if not 1 <= length_from_side <= 4.15:
        raise Exception("Enter an aspiration distance from well side 1-4.15mm")

    # load labware
    mag_deck = ctx.load_module('magnetic module gen2', '1')
    mag_plate = mag_deck.load_labware('nest_96_wellplate_2ml_deep')
    supernat = ctx.load_labware('nest_12_reservoir_15ml', '4')
    ethanol = ctx.load_labware('nest_12_reservoir_15ml', '10')
    mastermix_tubes = ctx.load_labware(
            'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '7')
    pcr_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '8')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '11')
    tiprack_300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                   for slot in ['3', '6', '9']]
    tiprack_20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                  for slot in ['2', '5']]

    # load instruments
    p20 = ctx.load_instrument('p20_single_gen2', 'left',
                              tip_racks=tiprack_20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'right',
                               tip_racks=tiprack_300)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all 200 ul tip racks on Slots 3, 6, and 9")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # number of tips trash will accommodate before prompting user to empty
    switch = True
    drop_count = 0
    drop_threshold = 120

    def _drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        if pip.type == 'multi':
            drop_count += 8
        else:
            drop_count += 1
        if drop_count >= drop_threshold:
            m300.home()
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()  # home before continuing with protocol
            drop_count = 0

    m300.flow_rate.aspirate = asp_flow_rate
    m300.flow_rate.dispense = disp_flow_rate

    # reagents
    lysis_buffer = reservoir.wells()[0:2]
    isoprop_beads = reservoir.wells()[3:7]
    isoprop_beads_ext = isoprop_beads*3
    nuc_free_water = reservoir.wells_by_name()["A12"]

    # protocol volumes for user
    num_samp = num_col*8
    lys_vol_needed_per_col = 8*290
    lys_vol_case1 = num_samp*290 if num_col <= 6 else lys_vol_needed_per_col*6
    lys_vol_case2 = lys_vol_needed_per_col*(num_col-6)
    case2_str = f"and {lys_vol_case2}ul in row A2" if num_col > 6 else ""
    isoprop_beads_vol = 8*510*math.ceil(num_col/4)
    nuc_free_water_vol = num_samp*nuc_free_water_vol_well
    ethanol_vol = math.ceil(1000*num_samp/12)
    mix_vol_per_col = 8*20
    mastermix_vol_case1 = num_samp*20 if num_col <= 6 else mix_vol_per_col*6
    mastermix_vol_case2 = mix_vol_per_col*(num_col-6)
    case2_str = f"and {mastermix_vol_case2}ul in tube B1"if num_col > 6 else ""

    ctx.pause(f'''Please confirm that the following volumes are in their
respective labware before beginning the protocol:\n
Minimum {lys_vol_case1}ul of MagBio CTL medium in row A1 {case2_str}
of the Nest 15mL reservoir on Slot 11.\n
Minimum {isoprop_beads_vol}ul of isopropanol + magnetic bead mastermix is in
each row from row A4 to row A7 of the nest 15mL reservoir on Slot 11.\n
Minimum {nuc_free_water_vol}ul of nuclease free water in row 10 of the
Nest 15mL reservoir on Slot 11.\n
Minimum {ethanol_vol}ul of ethanol for each row up to row {num_col} of the
Nest 15mL reservoir on Slot 10.\n
Minimum {mastermix_vol_case1}ul of PCR mastermix in tube A1 {case2_str}
of the Nest 15mL reservoir on Slot 11.\n''')

    # add MagBio CTL medium lysis buffer
    ctx.comment('\n--------- ADDING MAGBIO CTL MEDIUM ---------\n')
    for i, col in enumerate(mag_plate.rows()[0][:num_col]):
        pick_up(m300)
        m300.transfer(290,
                      lysis_buffer[0 if i < 6 else 1],
                      col.top(),
                      new_tip='never')
        m300.mix(samp_and_lys_rep, 200, col)
        _drop(m300)

    # add binding buffer
    ctx.comment('\n--------- ADDING BINDING BUFFER ---------\n')
    pick_up(m300)
    for s, col in zip(isoprop_beads_ext, mag_plate.rows()[0][:num_col]):
        m300.transfer(510,
                      s,
                      col.top(),
                      new_tip='never')
    _drop(m300)
    for col in mag_plate.rows()[0][:num_col]:
        pick_up(m300)
        m300.mix(15, 200, col)
        _drop(m300)

    ctx.delay(minutes=incubate_bind_time)

    # resuspend MAG-S1 particles before engaging magnet
    ctx.comment('\n--------- RESUSPEND MAG-S1 BEADS BEFORE ENGAGE ---------\n')
    for col in mag_plate.rows()[0][:num_col]:
        pick_up(m300)
        m300.mix(shake_well, 200, col)
        _drop(m300)
    # engage magnetic module, remove supernatant with 2 ethanol washes
    ctx.comment('\n--------- ENGAGE MAGDECK WITH 2 ETHANOL WASHES ---------\n')
    for i in range(3):
        mag_deck.engage()
        ctx.delay(minutes=mag_engage_time)

        # remove supernat
        ctx.comment('\n--------- REMOVING SUPERNATANT ---------\n')
        for index, (s_col, d_col) in enumerate(zip(
             mag_plate.rows()[0][:num_col], supernat.rows()[0])):
            pick_up(m300)
            side = -1 if index % 2 == 0 else 1
            aspirate_loc = s_col.bottom(z=asp_height).move(
                    Point(x=(s_col.length/2-length_from_side)*side))
            m300.transfer(500 if i > 0 else 1000,
                          aspirate_loc,
                          d_col.top(),
                          new_tip='never')
            _drop(m300)
        # only use the top half of this loop for 3rd iteration
        if i > 1:
            break

        # add ethanol and mix
        ctx.comment('\n--------- ADDING ETHANOL ---------\n')
        mag_deck.disengage()
        pick_up(m300)
        for s_col, d_col in zip(
         ethanol.wells(), mag_plate.rows()[0][:num_col]):
            m300.transfer(500,
                          s_col,
                          d_col.top(),
                          new_tip='never')
        _drop(m300)
        for col in mag_plate.rows()[0][:num_col]:
            pick_up(m300)
            m300.mix(15, 200, col)
            _drop(m300)
    ctx.delay(minutes=bead_dry_time)
    mag_deck.disengage()

    # add nuclease free nuclease free water
    ctx.comment('\n--------- ADDING NUCLEASE-FREE WATER ---------\n')
    pick_up(m300)
    for col in mag_plate.rows()[0][:num_col]:
        m300.transfer(nuc_free_water_vol_well,
                      nuc_free_water,
                      col.top(),
                      new_tip='never')
    _drop(m300)
    for col in mag_plate.rows()[0][:num_col]:
        pick_up(m300)
        m300.mix(15, nuc_free_water_vol_well-10, col)
        _drop(m300)
    ctx.delay(minutes=bead_dry_time_nuc_water)
    mag_deck.engage()
    ctx.delay(minutes=mag_engage_time)

    # transfer eluate and mastermix to pcr plate
    ctx.comment('\n--------- ADDING MASTERMIX TO PCR PLATE ---------\n')
    p20.pick_up_tip()
    for i, well in enumerate(pcr_plate.wells()[:num_samp]):
        p20.aspirate(20, mastermix_tubes.wells()[0 if i < 48 else 1])
        p20.dispense(20, well.top())
        p20.blow_out()
    p20.drop_tip()

    ctx.comment('\n--------- ADDING ELUATE TO PCR PLATE ---------\n')
    airgap = 5
    for s, d in zip(mag_plate.wells()[:num_samp], pcr_plate.wells()):
        p20.pick_up_tip()
        p20.aspirate(5, s)
        p20.air_gap(airgap)
        p20.dispense(5+airgap, d)
        p20.mix(2, 15, d)
        p20.blow_out(d.top())
        p20.drop_tip()
    mag_deck.disengage()
