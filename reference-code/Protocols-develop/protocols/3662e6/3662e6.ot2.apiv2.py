metadata = {
    'protocolName': 'Custom Drug Dilution Assay',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt300, mnt10, nc] = get_values(  # noqa: F821
     'mnt300', 'mnt10', 'nc')

    # load labware
    tips10 = [protocol.load_labware('opentrons_96_filtertiprack_10ul', '5')]
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '2')]

    m10 = protocol.load_instrument('p10_multi', mnt10, tip_racks=tips10)
    m300 = protocol.load_instrument('p300_multi', mnt300, tip_racks=tips300)
    m10.flow_rate.aspirate = 10
    m10.flow_rate.dispense = 10

    dd01, dd1, dd10, ds200 = [
        protocol.load_labware(
            'corning_96_wellplate_360ul_flat',
            s,
            n) for s, n in zip(range(1, 12, 3), [
                'Drug Dilution 0.1uM',
                'Drug Dilution 1uM',
                'Drug Dilution 10uM',
                'Drug Stock 200uM'])]

    cells, media = [
        protocol.load_labware(
            'axygen_1_reservoir_90ml',
            s,
            n) for s, n in zip([11, 8], ['Cells', 'Media+IL-2+OKT3+CD28'])]

    # Transfer 100µL Media to wells in plates
    allPlateWells = dd10.rows()[0][:nc]+dd1.rows()[0][:nc]+dd01.rows()[0][:nc]

    protocol.comment('Transferring 100µL of Media to all wells...')
    tipctr = 0

    for well in allPlateWells:
        if tipctr == 0:
            m300.pick_up_tip()
        m300.aspirate(20, media['A1'].top())
        m300.aspirate(60, media['A1'])
        m300.dispense(60, media['A1'])
        m300.aspirate(100, media['A1'])
        m300.air_gap(30)
        m300.dispense(150, well)
        m300.blow_out()
        tipctr += 1
        if tipctr == 4:
            m300.return_tip()
            m300.reset_tipracks()
            tipctr = 0
    if m300.has_tip:
        m300.return_tip()

    # Perform dilutions
    protocol.comment('Performing 10x dilutions...')
    plates = [p.rows()[0][:nc] for p in [ds200, dd10, dd1, dd01]]
    for s, p1, p2, p3 in zip(*plates):
        m10.pick_up_tip()

        m10.transfer(
            10, s, p1, new_tip='never',
            mix_before=(4, 10), mix_after=(4, 10))
        m10.blow_out()
        m10.transfer(
            10, p1, p2, new_tip='never',
            mix_before=(1, 7), mix_after=(4, 10))
        m10.blow_out()
        m10.transfer(
            10, p2, p3, new_tip='never',
            mix_before=(1, 7), mix_after=(4, 10))
        m10.blow_out()

        m10.transfer(
            10, p3, protocol.fixed_trash['A1'], new_tip='never',
            mix_before=(1, 7), blow_out=True)

        m10.drop_tip()

    # Transfer 100µL Cells to wells in plates
    protocol.comment('Transferring 100µL of cells to all wells...')
    tipctr = 0
    m300.flow_rate.dispense = 200

    for well in allPlateWells:
        if tipctr == 0:
            m300.pick_up_tip(tips300[0]['A2'])
        m300.mix(5, 300, cells['A1'])
        m300.blow_out(cells['A1'])
        m300.aspirate(20, cells['A1'].top())
        m300.aspirate(60, cells['A1'])
        m300.dispense(60, cells['A1'])
        m300.aspirate(100, cells['A1'])
        m300.air_gap(30)
        m300.dispense(150, well.top(-2))
        m300.blow_out()
        tipctr += 1
        if tipctr == 4:
            m300.drop_tip(tips300[0]['A2'])
            tipctr = 0
    if m300.has_tip:
        m300.drop_tip(tips300[0]['A2'])

    protocol.comment('Protocol complete!')
