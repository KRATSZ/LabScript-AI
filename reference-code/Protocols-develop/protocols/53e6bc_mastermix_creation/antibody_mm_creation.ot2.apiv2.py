import math

# metadata
metadata = {
    'protocolName': 'Mastermix Creation',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    # load labware
    tempdeck = ctx.load_module('tempdeck', '1')
    ab_plate = tempdeck.load_labware('eppendorftwin.tec_96_wellplate_150ul')
    tempdeck.set_temperature(4)
    rack_5ml = ctx.load_labware(
        'vwr_15_tuberack_selfstanding_5ml_conical', '2', '3x5 5ml tuberack')
    tiprack300 = ctx.load_labware(
        'opentrons_96_tiprack_300ul', '3', '300ul tiprack')
    rack_1500ul = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '4')
    tiprack50 = ctx.load_labware(
        'opentrons_96_tiprack_300ul', '5', '300ul tiprack')

    # reagent setup
    mm = rack_5ml.wells()[0]
    pbs = rack_5ml.wells()[1]
    bs_buffer = rack_1500ul.wells()[0]

    [p50_single_mount, p300_single_mount, number_of_samples,
        antibody_csv] = get_values(  # noqa: F821
            "p50_single_mount", "p300_single_mount", "number_of_samples",
            "antibody_csv"
        )

    # check
    if number_of_samples > 96 or number_of_samples < 1:
        raise Exception('Number of samples must be from 1-96.')
    if p300_single_mount == p50_single_mount:
        raise Exception('Pipette mounts cannot match.')

    # pipettes
    p50 = ctx.load_instrument(
        'p50_single', mount=p50_single_mount, tip_racks=[tiprack50])
    p300 = ctx.load_instrument(
        'p300_single', mount=p300_single_mount, tip_racks=[tiprack300])

    # transfer data from .csv files
    transfer_data = [
        [val.strip() for val in line.split(',')]
        for line in antibody_csv.splitlines() if line
    ][1:]

    # volume calculations and mastermix creation
    vol_buffer = 11*number_of_samples

    # volume check
    if vol_buffer + sum(
            [float(t[0])*number_of_samples for t in transfer_data]) > 5000:
        raise Exception('WARNING: Specified volumes and sample number may \
cause overflow in the mastermix tube.')

    ab_total_vol = sum([float(t[0]) for t in transfer_data])

    # adjust with PBS
    end_vol = 100*number_of_samples
    pbs_vol = end_vol - ab_total_vol
    pip = p50 if pbs_vol < 50 else p300
    mix_vol = (
        end_vol/2
        if end_vol/2 < p50.max_volume*0.9
        else p50.max_volume*0.9
    )
    num_trans = math.ceil(pbs_vol/50)
    pip.pick_up_tip()
    for t in range(num_trans):
        if t < num_trans - 1:
            t_vol = 50
        else:
            t_vol = 50 if pbs_vol % 50 == 0 else pbs_vol % 50
        pip.aspirate(t_vol, pbs)
        pip.move_to(pbs.top(15))
        pip.dispense(t_vol, mm)
    if p50.hw_pipette['has_tip']:
        p50.drop_tip()
    if not p300.hw_pipette['has_tip']:
        p300.pick_up_tip()
    p300.mix(5, mix_vol, mm)
    p300.drop_tip()

    # transfer buffer, antibodies, and pbs
    current_vol = 0
    pip = p50 if vol_buffer < 50 else p300
    pip.transfer(vol_buffer, bs_buffer, mm)

    for t in transfer_data:
        vol = float(t[0])*number_of_samples
        source = ab_plate.wells(t[2].upper())
        pip = p50 if vol_buffer < 50 else p300

        current_vol += pbs_vol
        pip.pick_up_tip()
        pip.transfer(vol, source, mm, new_tip='never')
        mix_vol = (
            current_vol*0.5
            if current_vol*0.5 < pip.max_volume*0.9
            else pip.max_volume*0.9
        )
        pip.mix(3, mix_vol, mm)
        pip.blow_out(mm.top(-5))
        pip.drop_tip()

    ctx.comment('Proceed with Flow Cytometry Staining.')
