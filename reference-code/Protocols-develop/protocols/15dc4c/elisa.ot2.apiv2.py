import math
from opentrons import protocol_api
from opentrons.types import Point

metadata = {
    'protocolName': 'SMC IL-17A High Sensitivity Immunoassay Kit',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}

DO_MIX = True
DO_INCUBATIONS = True
DROP = True
Z_OFFSET_RESERVOIR = 1.0
VOL_SAMPLE = 100.0
ELUTION_TYPE = 'SMCxPRO'  # Errena / SMCxPRO


def run(ctx):

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200
    ctx.max_speeds['Z'] = 200
    ctx.max_speeds['A'] = 200

    # [num_samples, mount_m300, m20] = get_values(  # noqa: F821
    #     'num_samples', 'mount_m300', 'mount_m20')
    num_samples, mount_m300, mount_m20 = 60, 'left', 'right'

    elution_plate = ctx.load_labware('aurora_384_wellplate_100ul', '1',
                                     'elution plate')
    sample_plate = ctx.load_labware('axygen_96_wellplate_500ul', '2',
                                    'sample preparation plate')
    standard_plate = ctx.load_labware('axygen_96_wellplate_2000ul', '4',
                                      'standards plate')
    assay_plate = ctx.load_labware('axygen_96_wellplate_500ul', '5',
                                   'assay plate')
    assay_plate_on_magnet = ctx.load_labware(
        'axygenspheremag_96_wellplate_500ul', '7', 'sphere mag plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '8',
                                 'reagents')
    tipracks200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['10', '11']]
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['3', '6', '9']]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', mount_m300,
                               tip_racks=tipracks200)
    m20 = ctx.load_instrument('p20_multi_gen2', mount_m20,
                              tip_racks=tipracks20)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(
                f'Replace P{pip.max_volume} pipette tips before resuming.')
            pip.reset_tipracks()
            pip.pick_up_tip()

    def wick(pip, well, side=1):
        if well.diameter:
            radius = well.diameter/2
        else:
            radius = well.width/2
        pip.move_to(well.bottom().move(Point(x=side*radius*0.8, z=3)))

    def slow_withdraw(pip, well, delay_seconds=1):
        ctx.delay(seconds=delay_seconds)
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # reagents
    num_cols = math.ceil(num_samples/5)

    standard_diluent = reservoir.rows()[0][0]
    sample_diluent = reservoir.rows()[0][1]
    coated_beads = reservoir.rows()[0][2]
    detection_antibody = reservoir.rows()[0][3]
    # elution_buffer_b = reservoir.rows()[0][4]
    buffer_d = reservoir.rows()[0][5]
    samples = sample_plate.rows()[0][:num_cols]

    """
    Create and plate standards
    """
    # single tip with P300
    tips_standard_dilution = m300.tip_racks[-1].rows()[-1]
    standard_dest_sets = [col[:3] for col in assay_plate.columns()]
    standard_dil_vols = [1000]*3 + [500]*8

    # pre-add diluent
    m300.pick_up_tip(tips_standard_dilution[0])
    for vol, d in zip(standard_dil_vols, standard_plate.rows()[0][1:]):
        num_trans = math.ceil(vol/tips_standard_dilution[0].max_volume)
        vol_per_trans = round(vol/num_trans, 1)
        for _ in range(num_trans):
            m300.aspirate(vol_per_trans,
                          standard_diluent.bottom(Z_OFFSET_RESERVOIR))
            slow_withdraw(m300, standard_diluent)
            m300.dispense(vol, d.bottom(2))
            slow_withdraw(m300, d)

    # perform dilution
    for tip, s, d in zip(tips_standard_dilution,
                         standard_plate.rows()[0][:10],
                         standard_plate.rows()[0][1:11]):
        num_trans = math.ceil(500/tip.max_volume)
        vol_per_trans = round(vol/num_trans, 1)
        if not m300.has_tip:
            m300.pick_up_tip(tip)
        for n in range(num_trans):
            m300.aspirate(vol_per_trans, s.bottom(2))
            slow_withdraw(m300, s)
            m300.dispense(vol_per_trans, d.bottom(2))
        if n == num_trans - 1 and DO_MIX:
            m300.mix(5, 100, d.bottom(2))
        slow_withdraw(m300, d)
        if DROP:
            m300.drop_tip()
        else:
            m300.return_tip()

    if DROP:
        tips_standard_transfer = m300.tip_racks[-1].rows()[-2]
    else:
        tips_standard_transfer = m300.tip_racks[-1].rows()[-1]

    # transfer to assay plate
    for tip, s, dest_set in zip(tips_standard_transfer,
                                standard_plate.rows()[0],
                                standard_dest_sets):
        m300.pick_up_tip(tip)
        num_asp = math.ceil(len(dest_set)*100/tip.max_volume)
        distribution_sets = [
            dest_set[i*2:(i+1)*2]
            if i < num_asp - 1
            else dest_set[i*2:]
            for i in range(num_asp)
        ]
        for d_set in distribution_sets:
            m300.aspirate(100*len(d_set), s.bottom(2))
            for d in d_set:
                m300.dispense(100, d.bottom(1))
                slow_withdraw(m300, d)

        # for d in dest_set:
        #     m300.aspirate(100, s.bottom(2))
        #     slow_withdraw(m300, s)
        #     m300.dispense(100, d.bottom(1))
        #     slow_withdraw(m300, d)
        if DROP:
            m300.drop_tip()
        else:
            m300.return_tip()

    """
    Dilute and transfer samples to assay plate
    """

    if DROP:
        tips_sample_transfer = m300.tip_racks[-1].rows()[1]
    else:
        tips_sample_transfer = m300.tip_racks[-1].rows()[3]

    sample_dests = assay_plate.rows()[3][:num_cols]
    num_trans = math.ceil(VOL_SAMPLE/tips_sample_transfer[0].max_volume)
    vol_per_trans = round(VOL_SAMPLE/num_trans, 1)
    for tip, s, d in zip(tips_sample_transfer, samples, sample_dests):
        m300.pick_up_tip(tip)
        for _ in range(num_trans):
            m300.aspirate(vol_per_trans,
                          sample_diluent.bottom(Z_OFFSET_RESERVOIR))
            slow_withdraw(m300, sample_diluent)
            m300.dispense(vol_per_trans, s.top(-1))
            if DO_MIX:
                m300.mix(5, 100, s.bottom(2))
            m300.aspirate(100, s.bottom(2))
            slow_withdraw(m300, s)
            m300.dispense(100, d.bottom(2))
            slow_withdraw(m300, d)
        if DROP:
            m300.drop_tip()
        else:
            m300.return_tip()

    """
    Add coated beads
    """
    ctx.pause('Add coated beads to reservoir channel 3.')
    standards_and_samples = assay_plate.rows()[0]
    pick_up(m300)
    for i, d in enumerate(standards_and_samples):
        # pre-air_gap
        m300.aspirate(40, coated_beads.top())
        if i == 0 and DO_MIX:
            for _ in range(5):
                m300.aspirate(100, coated_beads.bottom(2))
                m300.dispense(100, coated_beads.bottom(15))
                ctx.delay(seconds=1)
        m300.aspirate(100, coated_beads.bottom(Z_OFFSET_RESERVOIR))
        slow_withdraw(m300, coated_beads)
        m300.flow_rate.dispense *= 2
        m300.dispense(m300.current_volume, d.top(-1))
        m300.move_to(d.top().move(Point(x=d.diameter/2, z=-1)))
        m300.flow_rate.dispense /= 2
        ctx.delay(seconds=1)
    if DROP:
        m300.drop_tip()
    else:
        m300.return_tip()

    ctx.pause('Proceed with Target Capture incubation and Post-Capture Wash.')

    """
    Detection
    """
    standards_and_samples = assay_plate_on_magnet.rows()[0]
    vol_max = m300.tip_racks[0].wells()[0].max_volume - 20  # extra
    num_asp_sets = math.ceil(len(standards_and_samples)*20/vol_max)
    num_dests_per_asp = math.ceil(len(standards_and_samples)/num_asp_sets)
    detection_antibody_sets = [
        standards_and_samples[i*num_dests_per_asp:(i+1)*num_dests_per_asp]
        if i < num_asp_sets - 1
        else standards_and_samples[i*num_dests_per_asp:]
        for i in range(num_asp_sets)
    ]
    pick_up(m300)
    for d_set in detection_antibody_sets:
        # void excess if necessary
        if m300.current_volume > 0:
            m300.dispense(m300.current_volume, detection_antibody.top(-1))
        m300.aspirate(20*len(d_set) + 20,
                      detection_antibody.bottom(Z_OFFSET_RESERVOIR))
        slow_withdraw(m20, detection_antibody)
        for d in d_set:
            m300.dispense(20, d.top(-1))
            ctx.delay(seconds=2)
    if DROP:
        m300.drop_tip()
    else:
        m300.return_tip()

    ctx.pause('Proceed with Detection incubation and Post-Detection Wash \
and Shake.')

    """
    Elution
    """
    # for d in standards_and_samples:
    #     pick_up(m20)
    #     # reverse pipetting
    #     m20.aspirate(15, elution_buffer_b.bottom(Z_OFFSET_RESERVOIR))
    #     slow_withdraw(m20, elution_buffer_b)
    #     m20.dispense(10, d.bottom(0.5))
    #     slow_withdraw(m20, d)
    #     if DROP:
    #         m20.drop_tip()
    #     else:
    #         m20.return_tip()

    if ELUTION_TYPE == 'Erenna':
        ctx.pause('Proceed with Elution incubation')

        # add buffer D to elution plate
        elution_dests = elution_plate.rows()[0][::2]
        pick_up(m20)
        m20.aspirate(5, buffer_d)
        for d in elution_dests:
            # reverse pipetting
            m20.aspirate(10, buffer_d.bottom(Z_OFFSET_RESERVOIR))
            slow_withdraw(m20, buffer_d)
            m20.dispense(10, d.bottom(0.5))
            wick(m20, d)
            slow_withdraw(m20, d)

        # void extra volume
        m20.dispense(m20.current_volume, buffer_d)
        slow_withdraw(m20, buffer_d)

        m20.flow_rate.aspirate /= 10
        for s, d in zip(standards_and_samples, elution_dests):
            if not m20.has_tip:
                pick_up(m20)
            m20.aspirate(20, s.bottom(0.5))
            slow_withdraw(m20, s)
            m20.dispense(20, d.bottom(0.5))
            slow_withdraw(m20, d)
            if DROP:
                m20.drop_tip()
            else:
                m20.return_tip()

        m20.flow_rate.aspirate *= 10

    elif ELUTION_TYPE == 'SMCxPRO':

        ctx.pause('Proceed with Elution incubation. Place clean assay plate \
in slot 5')

        # add buffer D to mag plate and transfer elution to 384-plate
        elution_dests_2 = elution_plate.rows()[0][::2]
        for s, d in zip(standards_and_samples, elution_dests_2):
            pick_up(m20)

            m20.aspirate(10, buffer_d.bottom(Z_OFFSET_RESERVOIR))
            slow_withdraw(m20, buffer_d)
            m20.dispense(10, s.bottom(0.5))
            if DO_MIX:
                m20.mix(5, 10, s.bottom(0.5))
            m20.flow_rate.aspirate /= 5
            m20.aspirate(20, s.bottom(0.2))
            m20.flow_rate.aspirate *= 5
            slow_withdraw(m20, s)
            m20.dispense(20, d.bottom(0.5))
            slow_withdraw(m20, d)
            if DROP:
                m20.drop_tip()
            else:
                m20.return_tip()

    ctx.comment('Proceed with plate reading.')
