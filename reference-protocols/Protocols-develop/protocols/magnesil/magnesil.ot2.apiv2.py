import math
from opentrons.protocol_api.labware import Well

metadata = {
    'protocolName': 'Promega MagneSil Purification',
    'author': 'Chaz <protocols@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(protocol):
    [num_samps, pip_model, pip_mount, filter_tip, mag_model,
     mp_type, res_type, ep_type] = get_values(  # noqa: F821
     'num_samps', 'pip_model', 'pip_mount', 'filter_tip', 'mag_model',
     'mp_type', 'res_type', 'ep_type')

    # load labware and pipettes
    if num_samps > 32:
        raise Exception('Number of Samples must be 32 or less.')

    tip_type = 'opentrons_96_filtertiprack_200ul' if filter_tip \
        else 'opentrons_96_tiprack_300ul'
    tips = [protocol.load_labware(
        tip_type, str(s)) for s in range(7, 12)]
    tip_locs = [wells for rack in tips for wells in rack.rows()[0]]
    tip_ctr = 0
    thresh = 12

    elution_plate = protocol.load_labware(ep_type, '6')

    magdeck = protocol.load_module(mag_model, '4')
    magplate = magdeck.load_labware(mp_type)

    res = protocol.load_labware(res_type, '2')

    m300 = protocol.load_instrument(pip_model, pip_mount, tip_racks=tips)

    # reagents and samples
    num_cols = math.ceil(num_samps/8)
    rb, lysis, neutr, magblue, magred, etoh, elution = res.wells()[:7]
    waste = res.wells()[8:]
    samps = magplate.rows()[0][::2][:num_cols]
    magsamps = magplate.rows()[0][1::2][:num_cols]
    elutes = elution_plate.rows()[0][:num_cols]

    protocol.set_rail_lights(True)

    # custom transfer for mapping tips
    def custom_transfer(vol, srcs, dests, **kwargs):
        """
        custom_transfer() can be used in place of instrument.transfer()
        with the added function of dropping used tips into empty tip racks
        to reduce the need for manual intervention

        `thresh` is the number of columns of tips that will be disposed
        in the trash bin before dropping tips in empty tip racks.
        """
        nonlocal tip_ctr
        nonlocal thresh

        if type(srcs) is Well:
            for dest in dests:
                m300.pick_up_tip()
                m300.transfer(vol, srcs, dest, **kwargs, new_tip='never')
                if tip_ctr < thresh:
                    m300.drop_tip()
                else:
                    m300.drop_tip(tip_locs[tip_ctr-thresh])
                tip_ctr += 1
        elif type(dests) is Well:
            for src in srcs:
                m300.pick_up_tip()
                m300.transfer(vol, src, dests, **kwargs, new_tip='never')
                if tip_ctr < thresh:
                    m300.drop_tip()
                else:
                    m300.drop_tip(tip_locs[tip_ctr-thresh])
                tip_ctr += 1
        else:
            for src, dest in zip(srcs, dests):
                m300.pick_up_tip()
                m300.transfer(vol, src, dest, **kwargs, new_tip='never')
                if tip_ctr < thresh:
                    m300.drop_tip()
                else:
                    m300.drop_tip(tip_locs[tip_ctr-thresh])
                tip_ctr += 1

    # transfers
    magdeck.disengage()

    protocol.comment('\nTransferring 90uL of Resuspension Buffer\n')
    custom_transfer(90, rb, samps, mix_after=(10, 70))

    protocol.comment('\nTransferring 120uL of Lysis Solution\n')
    custom_transfer(120, lysis, samps, mix_after=(5, 150))

    protocol.comment('Pausing operation for 2 minutes.')
    protocol.delay(minutes=2)

    protocol.comment('\nTransferring 120µL of Neutralization Buffer\n')
    custom_transfer(120, neutr, samps, mix_after=(5, 200))

    protocol.comment('\nTransferring 30µL of MagneSil Blue\n')
    custom_transfer(30, magblue, samps, mix_before=(7, 50), mix_after=(5, 50))

    magdeck.engage()

    protocol.comment('Pausing operation for 10 minutes.')
    protocol.delay(minutes=10)

    protocol.comment('\nTransferring 250uL from Odd columns to Even columns\n')
    custom_transfer(250, samps, magsamps)

    magdeck.disengage()

    protocol.comment('\nTransferring 50µL of MagneSil Red\n')
    custom_transfer(
        50, magred, magsamps, mix_before=(7, 50), mix_after=(5, 200))

    magdeck.engage()
    protocol.comment('Incubating for 10 minutes.')
    protocol.delay(minutes=10)

    protocol.comment('\nDiscarding 300µL to waste\n')
    custom_transfer(300, magsamps, waste)

    magdeck.disengage()

    for i in range(1, 4):
        protocol.comment(f'\nPerforming EtOH Wash {i}\n')
        custom_transfer(100, etoh, magsamps, mix_after=(5, 75))

        magdeck.engage()
        protocol.comment('Incubating for 2 minutes.')
        protocol.delay(minutes=2)

        protocol.comment('\nDiscarding 100µL to waste\n')
        custom_transfer(100, magsamps, waste)

        magdeck.disengage()

    protocol.comment('Drying for 10 minutes.')
    protocol.delay(minutes=10)

    for _ in range(9):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=0.2)

    protocol.pause('Please ensure elution plate is on deck. \n\
                    When ready, click RESUME')
    protocol.set_rail_lights(True)

    protocol.comment('\nTransferring 100µL Elution Buffer\n')
    custom_transfer(100, elution, magsamps, mix_after=(5, 70))

    magdeck.engage()
    protocol.comment('Incubating for 10 minutes.')
    protocol.delay(minutes=10)

    protocol.comment('\nTransferring 100µL Elution to Elution Plate\n')
    custom_transfer(100, magsamps, elutes)

    protocol.comment('\nProtocol Complete.')
