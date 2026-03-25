metadata = {
    'protocolName': 'Custom Slide Transfer Protocol',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):

    # load labware
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', '1')
    [rack1, rack2] = [
        protocol.load_labware(
            'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
            s) for s in ['2', '3']
            ]
    slides = protocol.load_labware('spi_slides_4x21', '6')

    p20 = protocol.load_instrument(
        'p20_single_gen2', 'right', tip_racks=[tips20])

    # Adding 1ul spot to all slides
    # /source tubes are A2, A3, A4, & A5
    sourceTubes = [rack1['A'+str(i)] for i in range(2, 6)]
    # /create slide definitions based on rows
    slideWells = [well for row in slides.rows() for well in row]
    [slide1, slide2, slide3, slide4] = [[], [], [], []]
    for i, well in enumerate(slideWells):
        idx = i//3
        if idx % 4 == 0:
            slide1.append(well)
        elif idx % 4 == 1:
            slide2.append(well)
        elif idx % 4 == 2:
            slide3.append(well)
        else:
            slide4.append(well)

    protocol.comment('Transferring 1ul to each slide...')
    for src, slide in zip(sourceTubes, [slide1, slide2, slide3, slide4]):
        p20.pick_up_tip()
        tipval = 0
        for well in slide:
            if tipval == 0:
                p20.aspirate(3, src)
                tipval = 3
            p20.dispense(1, well)
            tipval -= 1
        p20.drop_tip()

    # Add 1ul across three wells in each slide
    [tubes1, tubes2, tubes3, tubes4] = [
        rack2.rows()[x] for x in range(4)
        ]
    for t, tlist in zip(rack1.columns()[-1], [tubes1, tubes2, tubes3, tubes4]):
        tlist.insert(0, t)

    protocol.comment('Adding 1ul to each 3 wells...')

    tubes = [tubes1, tubes2, tubes3, tubes4]
    slides2 = [slide1, slide2, slide3, slide4]
    for tube, slide in zip(tubes, slides2):
        for idx, well in enumerate(slide):
            i = idx//3
            p20.pick_up_tip()
            p20.aspirate(1, tube[i])
            p20.dispense(1, well)
            p20.drop_tip()

    protocol.comment('Protocol complete!')
