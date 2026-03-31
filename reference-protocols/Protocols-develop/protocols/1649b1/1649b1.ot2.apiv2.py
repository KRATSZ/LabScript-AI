metadata = {
    'protocolName': 'LGC Sbeadex Plant Maxi Kit Nucleic Acid Extraction',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [m300_mount] = get_values(  # noqa: F821
        "m300_mount")

    # Load Modules
    mag_mod = ctx.load_module('magnetic module gen2', 1)
    temp_mod = ctx.load_module('temperature module gen2', 3)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    temp_plate = temp_mod.load_labware(
                'nest_96_wellplate_100ul_pcr_full_skirt')

    # Load Labware
    sample_plate = ctx.load_labware('spex_96_wellplate_2400ul', 2,
                                    'Ground Sample Plate')
    lysis = ctx.load_labware('nest_1_reservoir_195ml', 4,
                             'Lysis Buffer').wells()[0]
    binding = ctx.load_labware('nest_1_reservoir_195ml', 5,
                               'Binding Buffer and Magnetic Beads').wells()[0]
    wash1 = ctx.load_labware('nest_1_reservoir_195ml', 7,
                             'Wash Buffer 1').wells()[0]
    wash2 = ctx.load_labware('nest_1_reservoir_195ml', 8,
                             'Wash Buffer 2').wells()[0]
    elution = ctx.load_labware('nest_1_reservoir_195ml', 6,
                               'Elution Buffer').wells()[0]
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in range(9, 12)]

    # Load Pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips300)

    tip_log = {'count': {m300: 0}}

    tip_log['tips'] = {
        m300: [tip for rack in tips300 for tip in rack.rows()[0]]}
    tip_log['max'] = {m300: len(tip_log['tips'][m300])}

    def _pick_up(pip, loc=None):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
            tip_loc = tip_log['tips'][pip][tip_log['count'][pip]]
            tip_log['count'][pip] += 1
            return tip_loc

    mag_plate_samples = mag_plate.rows()[0]
    temp_plate_wells = temp_plate.rows()[0]
    sample_plate_wells = sample_plate.rows()[0]

    # Home Pipette
    m300.home()

    # Initial Pause Step
    ctx.pause('Did you add Proteinase K and 2-ME to the lysis buffer?')

    # (1) Transfer 600 uL of Lysis Buffer to Sample Plate
    _pick_up(m300)
    for samples in sample_plate_wells:
        m300.transfer(600, lysis, samples.top(), new_tip='never')
    m300.drop_tip()

    # (2) Pause for Incubation
    ctx.pause('Pausing for Incubation...')

    # (3) Transfer 400 uL of Sample to NEST Deep Well Plate
    for samples, mag_well in zip(sample_plate_wells,
                                 mag_plate_samples):
        _pick_up(m300)
        m300.transfer(400, samples, mag_well, new_tip='never')
        m300.drop_tip()

    # (4) Pausing...
    ctx.pause('Pausing protocol...')

    # (5) Mix Binding Buffer
    _pick_up(m300)
    m300.mix(6, 300, binding)

    # (6) Transfer 490 uL of Binding Buffer + Mag Beads
    for mag_well in mag_plate_samples:
        if not m300.has_tip:
            _pick_up(m300)
        m300.transfer(490, binding, mag_well, mix_before=(2, 300),
                      mix_after=(10, 245), new_tip='never')
        m300.drop_tip()

    # (7) Engage Magnet + Pause for 5 minutes
    mag_mod.engage()
    ctx.delay(minutes=5, msg='Pausing for 5 minutes...')

    # (8) Transfer 890 uL from Mag Plate to Binding Reservoir
    for mag_well in mag_plate_samples:
        _pick_up(m300)
        m300.transfer(890, mag_well, binding, new_tip='never')
        m300.drop_tip()

    # (9) Pause
    ctx.pause('Empty binding buffer reservoir in hazardous waste')

    # (10) Transfer 75uL of Elution Buffer to Temp Plate
    # CONSERVE TIPS
    _pick_up(m300)
    m300.transfer(75, elution, temp_plate_wells, new_tip='never')
    m300.return_tip()

    # Warm Elution Buffer to 60C
    temp_mod.set_temperature(60)

    # (11) Disengage Magnet
    mag_mod.disengage()

    # (12) Transfer 600 uL Wash 1 Buffer to Mag Plate
    # CONSERVE TIPS
    wash1_tips = []
    for mag_well in mag_plate_samples:
        wash1_tips.append(_pick_up(m300))
        m300.transfer(600, wash1, mag_well, mix_after=(10, 300),
                      new_tip='never')
        m300.return_tip()

    # (13) Engage Mag Mod and Pause for 3 minutes
    mag_mod.engage()
    ctx.delay(minutes=3, msg='Pausing for 3 minutes...')

    # (14) Transfer 600 uL from mag plate to binding buffer reservoir
    for mag_well in mag_plate_samples:
        _pick_up(m300)
        m300.transfer(600, mag_well, binding, new_tip='never')
        m300.drop_tip()

    # (15) Disengage Magnet
    mag_mod.disengage()

    # (16) Transfer 600 uL of Wash 1 to Mag Plate
    # USE SAME TIPS from STEP 12
    for loc, mag_well in zip(wash1_tips, mag_plate_samples):
        _pick_up(m300, loc)
        m300.transfer(600, wash1, mag_well, mix_after=(5, 300),
                      new_tip='never')
        m300.return_tip()

    # (17) Engage Magnet
    mag_mod.engage()

    # (18) Pause for 3 minutes
    ctx.delay(minutes=3, msg='Pausing for 3 minutes...')

    # (19) Transfer 600 uL from Mag Plate to Wash 1 Reservoir
    for mag_plate in mag_plate_samples:
        _pick_up(m300)
        m300.transfer(600, mag_plate, wash1, new_tip='never')
        m300.drop_tip()

    # (20) Disengage Magnet
    mag_mod.disengage()

    # (21) Transfer 600 uL Wash 2 to Mag Plate and Mix 5 times
    # USE SAME TIPS AS STEPS 12, 16
    for loc, mag_well in zip(wash1_tips, mag_plate_samples):
        _pick_up(m300, loc)
        m300.transfer(600, wash2, mag_well, mix_after=(5, 300),
                      new_tip='never')
        m300.drop_tip()

    # (22) Engage and Pause
    mag_mod.engage()
    ctx.delay(minutes=3, msg='Pausing for 3 minutes...')

    # (23) Transfer 600uL from Mag Plate to Wash 2 Reservoir
    for mag_well in mag_plate_samples:
        _pick_up(m300)
        m300.transfer(600, mag_well, wash2, new_tip='never')
        m300.drop_tip()

    # (24) Disengage Magnet
    mag_mod.disengage()

    # (25) Transfer 70uL of Elution Buffer to Mag Plate
    for elution_well, mag_well in zip(temp_plate_wells,
                                      mag_plate_samples):
        _pick_up(m300)
        m300.transfer(70, elution_well, mag_well, mix_after=(10, 35),
                      new_tip='never')
        m300.drop_tip()
    temp_mod.deactivate()

    # (26) Pause Protocol for 5 minutes
    ctx.delay(minutes=5, msg='Pausing for 5 minutes...')

    # (27) Engage Magnet and Pause for 3 minutes
    mag_mod.engage()
    ctx.delay(minutes=3, msg='Pausing for 3 minutes...')

    # (28) Transfer 70 uL from Mag Plate to Temp Plate
    for temp_well, mag_well in zip(temp_plate_wells, mag_plate_samples):
        _pick_up(m300)
        m300.transfer(70, mag_well, temp_well, new_tip='never')
        m300.drop_tip()
