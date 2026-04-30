metadata = {
    'protocolName': 'QIAseq FastSelect Normalization',
    'author': 'Trevor <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):
    [pipette_type_1, pipette_mount_1, pipette_type_2, pipette_mount_2,
     p300_used, transfer_csv] = get_values(  # noqa: F821
        "pipette_type_1", "pipette_mount_1", "pipette_type_2",
        "pipette_mount_2", "p300_used",
        "transfer_csv")
    # load tips
    tips = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
            for slot in [3, 5]]
    if p300_used == 'yes':
        tips3 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                 for slot in [8]]
    # load modules
    tempdeck_1 = ctx.load_module('temperature module gen2', '10')
    tempdeck_2 = ctx.load_module('temperature module gen2', '7')
    # load labware
    water_res = ctx.load_labware('perkinelmer_12_reservoir_21000ul', 2,
                                 'Water reservoir')
    source_plate = tempdeck_1.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul',  # noqa: E501
                                           'source RNA plate')
    destination_plate = tempdeck_2.load_labware('appliedbiosystemsenduraplate_96_aluminumblock_220ul',  # noqa: E501
                                                'Dilution plate')
    # mapping
    water = water_res.rows()[0][0]
    # Turn on Temp Mods
    tempdeck_1.set_temperature(4)
    tempdeck_2.set_temperature(4)
    # pipettes
    if pipette_type_1 == 'p20_single_gen2':
        p20 = ctx.load_instrument(pipette_type_1, pipette_mount_1,
                                  tip_racks=tips)
    else:
        p300 = ctx.load_instrument(pipette_type_1, pipette_mount_1,
                                   tip_racks=tips3)
    if pipette_type_2 == 'p300_single_gen2':
        p300 = ctx.load_instrument(pipette_type_2, pipette_mount_2,
                                   tip_racks=tips3)
    else:
        p20 = ctx.load_instrument(pipette_type_2, pipette_mount_2,
                                  tip_racks=tips)
    # Parse CSV
    data = [[val.strip() for val in line.split(',')]
            for line in transfer_csv.splitlines()
            if line.split(',')[0].strip()][1:]
    # pre-transfer water
    p20.pick_up_tip()  # before all water transfers
    if p300_used == 'yes':
        p300.pick_up_tip()  # before all water transfers
    for i, line in enumerate(data):
        rna_conc = float(line[0])
        goal_conc = float(line[1])
        total_volume = float(line[2])
        water_vol = total_volume - ((goal_conc*total_volume)/rna_conc)
        if water_vol > 0:
            destination_well = destination_plate.wells()[i]
            if water_vol < 20:
                p20.transfer(water_vol, water, destination_well,
                             new_tip='never')
            else:
                p300.transfer(water_vol, water, destination_well,
                              new_tip='never')
    p20.drop_tip()  # after all water transfers
    if p300_used == 'yes':
        p300.drop_tip()  # after all water transfers
    # add RNA and mix
    for i, line in enumerate(data):
        rna_conc = float(line[0])
        goal_conc = float(line[1])
        total_volume = float(line[2])
        rna_vol = ((goal_conc*total_volume)/rna_conc)
        rna_vol = total_volume if rna_vol > total_volume else rna_vol
        source_well = source_plate.wells()[i]
        destination_well = destination_plate.wells()[i]
        if rna_vol < 20:
            p20.pick_up_tip
            p20.transfer(rna_vol, source_well, destination_well,
                         mix_after=(5, 10))
            p20.drop_tip
        else:
            p300.pick_up_tip
            p300.transfer(rna_vol, source_well, destination_well,
                          mix_after=(5, 10))
            p300.drop_tip
    ctx.pause('Click continue when ready to turn the cooling plates off')
    tempdeck_1.deactivate()
    tempdeck_2.deactivate()
    ctx.comment(
     '''Process Complete.''')
