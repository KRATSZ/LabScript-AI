from types import MethodType

metadata = {
    'protocolName': 'ProcartaPlex Protocol-2 [7/7]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    # [mnt300, numPlates] = get_values(  # noqa: F821
    #  'mnt300', 'numPlates')

    # load labware
    mnt300 = 'right'
    numPlates = 3
    tips = [
        protocol.load_labware('opentrons_96_filtertiprack_200ul', '7')
        ]

    m300 = protocol.load_instrument('p300_multi_gen2', mnt300, tip_racks=tips)
    destPlates = [
        protocol.load_labware(
            'procartaplex_96_wellplate_655096', s) for s in range(4, 7)
        ][:numPlates]
    rsvrs = [
        protocol.load_labware('nest_12_reservoir_15ml', s) for s in range(1, 4)
        ]

    # Variables
    washBuffers = [rsvr.wells()[:6] for rsvr in rsvrs]
    destWells = [plate.rows()[0] for plate in destPlates]

    def slow_tip_withdrawal(self, speed_limit, well_location, to_center=False):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        protocol.max_speeds[axis] = speed_limit
        if to_center is False:
            self.move_to(well_location.top())
        else:
            self.move_to(well_location.center())
        protocol.max_speeds[axis] = None

    def delay(self, delay_time):
        protocol.delay(seconds=delay_time)

    # bind methods to pipette
    for method in [delay, slow_tip_withdrawal]:
        setattr(m300, method.__name__, MethodType(method, m300))

    # create functions
    def msg_with_alert(msg, time=6):
        """
        This function will flash the on-deck lights, once per 2 seconds
        and display the 'msg' in the pause step in the OT app.
        Param msg: Message to be included in the pause step.
        Param time: Number of seconds to flash lights
        """
        for _ in range(time):
            protocol.set_rail_lights(not protocol.rail_lights_on)
            protocol.delay(seconds=1)

        protocol.pause(msg)

    def wash(num):
        """
        This function contains all of the steps neeeded for this custom wash.
        The pipette will pick up tips and using the same set of tips,
        transfer 150uL of Wash Buffer to all of the wells in the destination
        plate (top of the well to prevent cross contamination).
        Once complete, the pipette will trash the tips and the OT-2 will begin
        blinking to signify that the user can remove the plate for off deck
        processing.
        Param num: Location of wash buffer (should be number)
        """

        m300.pick_up_tip()
        for wells, wb in zip(destWells, washBuffers):
            src = wb[num]
            for well in wells:
                m300.aspirate(30, src.top())
                m300.aspirate(150, src)
                m300.delay(1)
                m300.slow_tip_withdrawal(10, src)
                m300.air_gap(20)
                m300.dispense(200, well.top(-2))
                m300.blow_out()
                m300.delay(1)
        m300.drop_tip()

        msg_with_alert("""
        Wash Buffer added. Please remove plate for off robot processing.
        When complete, please return plate to deck and click RESUME.
        """)

    # Perform two washes
    for i in range(2):
        wash(i)

    # Add 25ul of detection antibody
    msg_with_alert("""
    Please make sure that Detection Antibody is added to
    Column 8 of the 12-Well Reservoir(s).
    When ready, click RESUME
    """)

    protocol.comment('Adding 25uL of Detection Antibody to wells...')

    m300.pick_up_tip()

    for wells, rsvr in zip(destWells, rsvrs):
        antibody = rsvr['A8']
        for well in wells:
            m300.mix(3, 100, antibody)
            m300.aspirate(25, antibody, rate=0.7)
            m300.delay(2)
            m300.slow_tip_withdrawal(5, antibody)
            m300.air_gap(20)
            m300.dispense(45, well.top(-4), rate=0.7)
            m300.delay(1)
            m300.blow_out()

    m300.drop_tip()

    msg_with_alert("""
    Please remove plate and incubate for 30 minutes on rotator (500 rpm).
    Once complete, please replace plate on deck and click RESUME
    """)

    # Perform two washes
    for i in range(2, 4):
        wash(i)

    # Add 50uL SAP to wells
    msg_with_alert("""
    Please make sure that SAP is added to
    Column 10 of the 12-Well Reservoir.
    When ready, click RESUME
    """)

    protocol.comment('Adding 50uL of SAP to wells...')

    m300.pick_up_tip()

    for wells, rsvr in zip(destWells, rsvrs):
        sap = rsvr['A10']
        for well in wells:
            m300.mix(3, 100, sap)
            m300.aspirate(50, sap, rate=0.7)
            m300.delay(2)
            m300.slow_tip_withdrawal(5, sap)
            m300.air_gap(20)
            m300.dispense(70, well.top(-4), rate=0.7)
            m300.delay(1)
            m300.blow_out()

    m300.drop_tip()

    msg_with_alert("""
    Please remove plate and incubate for 30 minutes on rotator (500 rpm).
    Once complete, please replace plate on deck and click RESUME
    """)

    # Perform two washes
    for i in range(4, 6):
        wash(i)

    # Add 120uL Reading Buffer to wells
    msg_with_alert("""
    Please make sure that Reading Buffer is added to
    Column 12 of the 12-Well Reservoir.
    When ready, click RESUME
    """)

    protocol.comment('Adding 120uL of Reading Buffer to wells...')

    m300.pick_up_tip()

    for wells, rsvr in zip(destWells, rsvrs):
        readingBuffer = rsvr['A12']
        for well in wells:
            m300.mix(3, 100, readingBuffer)
            m300.aspirate(120, readingBuffer, rate=0.7)
            m300.delay(2)
            m300.slow_tip_withdrawal(5, readingBuffer)
            m300.air_gap(20)
            m300.dispense(140, well.top(-4), rate=0.7)
            m300.delay(1)
            m300.blow_out()

    m300.drop_tip()

    msg_with_alert("""
    Please remove plate and incubate for 5 minutes on rotator (500 rpm).
    Protocol complete.
    """)
