from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'PCR/qPCR Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [samples, p20_mount] = get_values(  # noqa: F821
        "samples", "p20_mount")

    samples = int(samples)

    # Load Labware
    deep_well = [ctx.load_labware('kingfisher_96_deepwell_plate_2ml', slot,
                                  f'Sample Plate {slot}')
                 for slot in range(1, 5)]
    pcr_plate = ctx.load_labware('microampoptical_384_wellplate_30ul', 5,
                                 'PCR Plate')
    # reservoir = ctx.load_labware('nest_12_reservoir_15ml', 6)
    reservoir = ctx.load_labware('96well_pcr_base_200ul_strip', 6)
    # tiprack300 = ctx.load_labware('opentrons_96_tiprack_300ul', 7)
    tiprack200 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
                  for slot in range(7, 12)]

    # water = reservoir['A1']
    # multiplex = reservoir['A2']
    # dye = reservoir['A3']
    # mm = reservoir['A5']
    mm = reservoir.rows()[0][0:3]

    # Load Pipette
    # p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
    #                            tip_racks=[tiprack300])
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount,
                              tip_racks=tiprack200)

    # # Create PCR Mix
    # reactions = round((samples*0.095)+samples)
    # p300.transfer(4*reactions, water, mm)
    # p300.transfer(5*reactions, multiplex, mm)
    # p300.transfer(1*reactions, dye, mm)
    # p300.pick_up_tip()
    # p300.mix(5, 300, mm)
    # p300.drop_tip()

    # Get columns depending on sample number
    columns = math.ceil(samples / 8)

    sample_wells = [well for i in range(4) for well in
                    deep_well[i].rows()[0]][:columns]

    pcr_wells = [[a, b] for a, b in zip(pcr_plate.rows()[0],
                 pcr_plate.rows()[1])]

    flat_dests = [well for pcr_wells in pcr_wells
                  for well in pcr_wells][:columns]

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
                        resuming.')
            pip.reset_tipracks()
            pip.pick_up_tip()

    # Transfer MM to PCR Plate
    i = 0
    pick_up(m20)
    for well in flat_dests:
        m20.transfer(10, mm[i//4], well, new_tip='never')
        if i == 11:
            i = 0
        else:
            i += 1
    m20.drop_tip()

    # Transfer Samples to PCR Plate
    for s_well, dest in zip(sample_wells, flat_dests):
        pick_up(m20)
        m20.transfer(10, s_well, dest, new_tip='never')
        m20.drop_tip()
