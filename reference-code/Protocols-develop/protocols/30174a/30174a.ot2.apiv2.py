
metadata = {
    'protocolName': 'DNA dilution using .csv file',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}

# csv_input = open("example.csv", "r").read()


def run(ctx):

    csv_input = get_values(  # noqa: F821
            'csv_input')

    plate1 = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt',
        '6',
        label="Plate 1")
    plate2 = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt',
        '9',
        label="Plate 2")
    te = ctx.load_labware('nest_1_reservoir_195ml', '8').wells()[0]

    p300s_tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '7')]
    p20s_tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '5')]

    p300s = ctx.load_instrument(
        'p300_single_gen2',
        'right',
        tip_racks=p300s_tips)
    p20s = ctx.load_instrument('p20_single_gen2', 'left', tip_racks=p20s_tips)

    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in csv_input
        if line and line.split(',')[0].strip()][1:]

    dna_transfer = []
    te_transfer = []
    wells = []

    for w, d, t in data:
        dna_transfer.append(float(d))
        te_transfer.append(float(t))
        wells.append(w)

    p300s.pick_up_tip()
    for i, vol in enumerate(te_transfer):
        p300s.transfer(
            vol, te, plate2.wells_by_name()[
                wells[i]], new_tip='never')
    p300s.drop_tip()

    for i, vol in enumerate(dna_transfer):
        p20s.transfer(
            vol, plate1.wells_by_name()[
                wells[i]], plate2.wells_by_name()[
                wells[i]], mix=(
                3, 2))
