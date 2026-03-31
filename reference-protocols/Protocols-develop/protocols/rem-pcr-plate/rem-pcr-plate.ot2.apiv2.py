from opentrons import protocol_api
from types import MethodType
from opentrons.types import Point, Location

metadata = {
    'protocolName': 'Dispense PCR Master Mix (plates)',
    'author': 'REM Analytics <emily.jamieson@remanalytics.ch>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8',
    'description': 'Dispense master mix from troughs to \
    plates using multichannel pipette'
}


def run(protocol: protocol_api.ProtocolContext):
    [_source, _no_plates, _start,
     _vol_dispense, _touch_tip] = get_values(  # noqa: F821
        "source", "no_plates", "start", "vol_dispense", "touch_tip")

    protocol.set_rail_lights(False)
    protocol.set_rail_lights(True)

    # variables: number of plates/mastermixes to be prepared, dispense volume
    no_plates = _no_plates
    vol_dispense = _vol_dispense
    touch_tip = _touch_tip
    start = _start
    source = _source

    # load tiprack
    tiprack_20 = protocol.load_labware('opentrons_96_tiprack_20ul', 6)

    # load pipette
    p10_multi = protocol.load_instrument(
        "p10_multi", "left", tip_racks=[tiprack_20])

    # load labware
    master_troughs = protocol.load_labware(
        "nest_12_reservoir_15ml", 2, label="master trough"
    )

    master_plate = protocol.load_labware(
        "96w_pcr_plate2", 1, label="master-plate"
    )

    pcr_plate = protocol.load_labware(
        "96w_pcr_plate2", 5, label="pcr-plate"
    )

    # unbound methods
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
    for pipette_object in [p10_multi]:
        for method in [delay, slow_tip_withdrawal]:
            setattr(
                pipette_object, method.__name__,
                MethodType(method, pipette_object))

    # helper functions
    def touch_right(cur_position: Location):
        if touch_tip == "right":
            p10_multi.move_to(cur_position.move(Point(x=2.7, z=-0.75)))
            p10_multi.move_to(cur_position.move(Point(x=-1, z=0.75)))
        else:
            p10_multi.move_to(cur_position.move(Point(x=-2.7, z=-0.75)))
            p10_multi.move_to(cur_position.move(Point(x=1, z=0.75)))

    def dispense_mm(vol, primer_no, mm_source):
        wells = pcr_plate.columns()
        if mm_source == "trough":
            mm = master_troughs.wells()[primer_no - 1]
        else:
            mm = master_plate.columns()[primer_no - 1][0]

        p10_multi.pick_up_tip()

        for col in wells:
            p10_multi.aspirate(vol, mm)
            p10_multi.dispense(vol*2, col[0].top(-1), rate=1.6)
            touch_right(col[0].top())
            p10_multi.delay(0.2)
            p10_multi.slow_tip_withdrawal(10, col[0])

        p10_multi.drop_tip()

    # protocol: distribute master mixes
    for mm in range(start, no_plates+1):
        if source == "trough":
            protocol.pause(
                "When you press resume, the master mix will be dispensed \
                into the next plate. Ensure this plate is in position \
                (in slot 5) and that at least {}uL of master mix for this \
                plate has been added to trough {}.".format(
                    (96*vol_dispense)+297, mm)
            )
        else:
            protocol.pause(
                "When you press resume, the master mix will be dispensed into \
                the next plate. Ensure this plate is in position (in slot 5) \
                and that at least {}uL of master mix for this plate has been \
                added to each well of column {}.".format(
                    (8*vol_dispense)+10, mm))
        dispense_mm(vol_dispense, mm, source)
