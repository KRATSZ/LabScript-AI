import math
from opentrons import protocol_api
from opentrons.types import Point

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, mount_p20, mount_m20] = get_values(  # noqa: F821
        'num_samples', 'mount_p20', 'mount_m20')

    num_plates = math.ceil(num_samples/96)
    num_cols = math.ceil(num_samples/8)

    # load labware
    sample_plates = [
        ctx.load_labware('biorad_96_wellplate_200ul_pcr', slot,
                         f'sample plate {i+1}')
        for i, slot in enumerate(['1', '4', '7', '10'][:num_plates])]
    pcr_plate = ctx.load_labware('biorad_384_wellplate_50ul_', '2',
                                 'PCR plate')
    reagent_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr', '5',
        'reagent plate')
    reagent_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '8',
        'reagent tuberack')

    occupied = [k for k in ctx.loaded_labwares.keys()]
    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in range(1, 12)
        if slot not in occupied]

    # load pipettes
    p20 = ctx.load_instrument(
            'p20_single_gen2', mount_p20, tip_racks=tipracks20)
    m20 = ctx.load_instrument(
            'p20_multi_gen2', mount_m20, tip_racks=tipracks20)

    # place reagents
    all_samples = [
        well for plate in sample_plates for well in plate.rows()[0]][:num_cols]
    all_destinations = [
        well for row in pcr_plate.rows()[:2] for well in row][:num_cols]
    ntc_dests = [
        pcr_plate.wells_by_name()[well] for well in ['P17', 'P18', 'P19']]
    ipc_mm_dests = pcr_plate.rows()[-1][-5:]
    ipc_template_dests = [
        pcr_plate.wells_by_name()[well] for well in ['P20', 'P21', 'P22']]
    ipc_water_dests = [
        pcr_plate.wells_by_name()[well] for well in ['P23', 'P24']]

    mm = reagent_plate.rows()[0][:2]
    nuclease_free_water = reagent_rack.wells()[0]
    ipc_mm = reagent_rack.wells()[1]
    ipc_template = reagent_rack.wells()[2]

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace the tips")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def wick(pip, well, side=1):
        radius = well.diameter/2 if well.diameter else well.width/2
        pip.move_to(well.bottom().move(Point(x=side*radius*0.5, z=3)))

    def slow_withdraw(pip, well, z=0, delay_seconds=2.0):
        ctx.max_speeds['A'] = 10
        ctx.max_speeds['Z'] = 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top(z))
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    # transfer mastermix to all sample wells
    pick_up(m20)
    for i, d in enumerate(all_destinations):
        mm_source = mm[i//24]
        m20.aspirate(1, mm_source.top())
        m20.aspirate(7, mm_source.bottom(1))
        slow_withdraw(m20, mm_source)
        m20.dispense(m20.current_volume, d.bottom(1))
        wick(m20, d)
        slow_withdraw(m20, d)
    m20.drop_tip()

    # add NTC MM
    pick_up(p20)
    for d in ntc_dests:
        mm_source = mm[0]
        p20.aspirate(1, mm_source.top())
        p20.aspirate(7, mm_source.bottom(1))
        slow_withdraw(p20, mm_source)
        p20.dispense(p20.current_volume, d.bottom(1))
        p20.mix(3, 5, d.bottom(1))
        wick(p20, d)
        slow_withdraw(p20, d)
    p20.drop_tip()

    # add all samples
    for s, d in zip(all_samples, all_destinations):
        pick_up(m20)
        m20.aspirate(1, s.top())
        m20.aspirate(3, s.bottom(1))
        slow_withdraw(m20, s)
        m20.dispense(m20.current_volume, d.bottom(1))
        m20.mix(3, 5, d.bottom(1))
        wick(m20, d)
        slow_withdraw(m20, d)
        m20.drop_tip()

    # add NTC
    for d in ntc_dests:
        pick_up(p20)
        p20.aspirate(1, nuclease_free_water.top())
        p20.aspirate(3, nuclease_free_water.bottom(1))
        slow_withdraw(p20, nuclease_free_water)
        p20.dispense(p20.current_volume, d.bottom(1))
        p20.mix(3, 5, d.bottom(1))
        wick(p20, d)
        slow_withdraw(p20, d)
        p20.drop_tip()

    # add IPC MM
    pick_up(p20)
    for d in ipc_mm_dests:
        p20.aspirate(1, ipc_mm.top())
        p20.aspirate(8, ipc_mm.bottom(1))
        slow_withdraw(p20, ipc_mm)
        p20.dispense(p20.current_volume, d.bottom(1))
        p20.mix(3, 5, d.bottom(1))
        wick(p20, d)
        slow_withdraw(p20, d)
    p20.drop_tip()

    # add cDNA IPC template
    for d in ipc_template_dests:
        pick_up(p20)
        p20.aspirate(1, ipc_template.top())
        p20.aspirate(2, ipc_template.bottom(1))
        slow_withdraw(p20, ipc_template)
        p20.dispense(p20.current_volume, d.bottom(1))
        p20.mix(3, 5, d.bottom(1))
        wick(p20, d)
        slow_withdraw(p20, d)
        p20.drop_tip()

    # add nuclease free water template
    for d in ipc_water_dests:
        pick_up(p20)
        p20.aspirate(1, nuclease_free_water.top())
        p20.aspirate(2, nuclease_free_water.bottom(1))
        slow_withdraw(p20, nuclease_free_water)
        p20.dispense(p20.current_volume, d.bottom(1))
        p20.mix(3, 5, d.bottom(1))
        wick(p20, d)
        slow_withdraw(p20, d)
        p20.drop_tip()
