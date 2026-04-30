from opentrons import protocol_api

metadata = {
    'apiLevel': '2.9',
    'protocolName': 'Standard Biotools Dynamic Array 48.48: Load 4 uL',
    'description': '''Transfer Samples and Assays
    from 96 well plate to Dynamic Array''',
    'author': 'Standard Biotools Inc',
    'source': 'Standard Biotools Inc',
}


def run(protocol: protocol_api.ProtocolContext):
    Rate_Normal = 1.0
    Rate_Slow = 0.66
    Rate_Slowest = 0.1

    def set_speed(rate):
        protocol.max_speeds['X'] = (600 * rate)
        protocol.max_speeds['Y'] = (400 * rate)
        protocol.max_speeds['Z'] = (125 * rate)
        protocol.max_speeds['A'] = (125 * rate)

    # load labware
    AssayPlate = protocol.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '4')
    SamplePlate = protocol.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '5')
    IFC = protocol.load_labware('dynamic_array_48_48', '2')

    tips20 = [
        protocol.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['10']
    ]

    # load instrument
    m20 = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)

    # Set Assay Volumes
    Vol_Asp = 4.1  # aspriate 0.1ul more
    Vol_Disp = 4

    # Tip Pickup Handler
    tips20_count = 0
    tips20_max = len(tips20)*12

    def pick_up20():
        nonlocal tips20_count
        if tips20_count == tips20_max:
            raise Exception('Replace 20µl tipracks before resuming.')
        tips20_count += 1
        m20.pick_up_tip()

    # Set Flow Rates
    # Default Aspirate Speed - 150 uL/s
    # Default Dispense Speed - 300 uL/s
    Delay_Asp = 0.5
    Delay_Disp = 1

    # protocol
    Chunks_48A = [
        AssayPlate.rows()[0][i:i+3] for i in range(
            0, len(AssayPlate.rows()), 3)]
    Chunks_48B = [
        SamplePlate.rows()[0][i:i+3] for i in range(
            0, len(SamplePlate.rows()), 3)]

    # the above chunks_48 variable makes a list of lists.
    # i.e. [[A1, A2, A3], [A4, A5, A6]]
    # the first [0] after .rows() attribute gives row A, the second index
    # [i:i+3] gives the numbers of wells

    cmtLine = '='*15
    protocol.comment(cmtLine)
    protocol.comment('Transfer Assay Mix - Plate 1 to IFC (Assay Inlets)')
    protocol.comment(cmtLine)
    m20.flow_rate.aspirate = 2
    m20.flow_rate.dispense = 2

    row_start = 0
    col_start = 0
    count = 0

    for chunk in Chunks_48A:  # left side (assay inlets)
        for source, dest in zip(chunk,
                                IFC.rows()[row_start][col_start:]):
            set_speed(Rate_Normal)
            pick_up20()
            m20.move_to(source.top(5))
            set_speed(Rate_Slowest)
            m20.aspirate(Vol_Asp, source.bottom(0.5))
            protocol.delay(seconds=Delay_Asp)
            m20.move_to(source.top(5))
            set_speed(Rate_Slow)
            m20.move_to(dest.top(5))
            set_speed(Rate_Slowest)
            m20.dispense(Vol_Disp, dest.bottom(0))
            protocol.delay(seconds=Delay_Disp)
            m20.move_to(dest.top(5))
            set_speed(Rate_Normal)
            m20.drop_tip()
            count += 1

            if count == 6:

                count = 0
                row_start = 0
                col_start = 3

                for chunk in Chunks_48B:  # right side (sample inlets)
                    for source, dest in zip(chunk,
                                            IFC.rows()[row_start][col_start:]):
                        set_speed(Rate_Normal)
                        pick_up20()
                        m20.move_to(source.top(5))
                        set_speed(Rate_Slowest)
                        m20.aspirate(Vol_Asp, source.bottom(0.5))
                        protocol.delay(seconds=Delay_Asp)
                        m20.move_to(source.top(5))
                        set_speed(Rate_Slow)
                        m20.move_to(dest.top(5))
                        set_speed(Rate_Slowest)
                        m20.dispense(Vol_Disp, dest.bottom(0))
                        protocol.delay(seconds=Delay_Disp)
                        m20.move_to(dest.top(5))
                        set_speed(Rate_Normal)
                        m20.drop_tip()
                        count += 1

                        if count == 6:
                            return
                    row_start += 1  # now change it to row B

        row_start += 1  # now change it to row B

    protocol.comment('\nProtocol Complete!')
