import math
from opentrons import protocol_api
from opentrons.types import Point

metadata = {
    'protocolName': 'Agriseq Library Prep Part 4 - Pooling (96)',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(protocol):

    [num_samp, p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "p20_mount", "p300_mount")

    if not 1 <= num_samp <= 288:
        raise Exception("Enter a sample number between 1-288")
    tip_counter = 0

    # load labware
    pool_plate1 = protocol.load_labware('customendura_96_wellplate_200ul', '1',
                                        label='Pool Plate 1')
    pool_plate2 = protocol.load_labware('customendura_96_wellplate_200ul', '2',
                                        label='Pool Plate 2')
    reaction_plates = [protocol.load_labware('customendura_96_wellplate_200ul',
                       str(slot), label='Reaction Plate')
                       for slot in [4, 5, 6]]
    tiprack20 = [protocol.load_labware('opentrons_96_filtertiprack_20ul',
                                       str(slot))
                 for slot in [9, 10, 11]]

    tiprack200 = [protocol.load_labware(
                    'opentrons_96_filtertiprack_200ul', '8')]

    # load instruments
    p20 = protocol.load_instrument('p20_single_gen2', p20_mount,
                                   tip_racks=tiprack20)
    p300 = protocol.load_instrument('p300_single_gen2', p300_mount,
                                    tip_racks=tiprack200)

    tips = [well for tipbox in tiprack20 for well in tipbox.wells()]

    def pick_up_20():
        nonlocal tip_counter
        if tip_counter == 288:
            protocol.home()
            protocol.pause('Replace 20 ul tip racks on Slots 9, 10, and 11')
            p20.reset_tipracks()
            tip_counter = 0
            p20.pick_up_20()

        else:
            p20.pick_up_tip(tips[tip_counter])
            tip_counter += 1

    def touchtip(pip, well):
        knock_loc = well.top(z=-1).move(
                    Point(x=-(well.diameter/2.25)))
        knock_loc2 = well.top(z=-1).move(
                    Point(x=(well.diameter/2.25)))
        pip.move_to(knock_loc)
        pip.move_to(knock_loc2)

    def pick_up_300():
        try:
            p300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            protocol.home()
            protocol.pause('Replace 200 ul tip rack on slot 8')
            p300.reset_tipracks()
            p300.pick_up_tip()

    # pool each row of plates
    airgap = 2
    num_col = math.ceil(num_samp/8)
    pool_counter = 0
    vol_counter = 0
    num_plates = math.ceil(num_samp/96)
    for i, plate in enumerate(reaction_plates[:num_plates]):
        if i == 0:
            length_row = num_col
        elif i == 1:
            length_row = num_col - 12
        else:
            length_row = num_col - 24
        wells_by_row = [well for row in reaction_plates[i].rows()
                        for well in row[:length_row]]
        for well in wells_by_row:
            pick_up_20()
            p20.aspirate(5, well)
            touchtip(p20, well)
            p20.air_gap(airgap)
            p20.dispense(airgap, pool_plate1.wells()[pool_counter].top())
            p20.dispense(5, pool_plate1.wells()[pool_counter])
            p20.blow_out()
            touchtip(p20, pool_plate1.wells()[pool_counter])
            vol_counter += 5
            if vol_counter % 60 == 0:
                pool_counter += 1
                protocol.comment('\nNEXT POOL WELL\n')
            p20.return_tip()
            protocol.comment('\n')

    airgap = 5
    for s, d in zip(pool_plate1.wells()[:pool_counter], pool_plate2.wells()):
        pick_up_300()
        p300.mix(2, 60, s)
        p300.aspirate(45, s)
        touchtip(p300, s)
        p300.dispense(45, d)
        touchtip(p300, d)
        p300.blow_out()
        p300.return_tip()
