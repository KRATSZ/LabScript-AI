from opentrons import protocol_api
import csv

metadata = {
    "protocolName": "Multiple Primer hydration",
    "apiLevel": "2.8",
}


def run(protocol: protocol_api.ProtocolContext):
    p300_multi: protocol_api.InstrumentContext
    protocol.pause(
        "Ensure pipette current is decreased \
        from 0.8Amps (normal) to 0.1Amps"
    )
    # Define tips
    tiprack_300 = protocol.load_labware("opentrons_96_tiprack_300ul", "4")

    # Define labware
    h_falcon = protocol.load_labware(
        "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", "5"
    )
    # DO NOT MOVE TO slots 1-2-3 because
    # you won't be able to access bottom tubes
    h_tubes = protocol.load_labware(
        "opentrons_24_tuberack_generic_2ml_screwcap", "6"
    )

    # Define instruments and assign tips
    p300_multi = protocol.load_instrument("p300_multi_gen2", "right")
    p300_multi.flow_rate.aspirate = 150
    p300_multi.flow_rate.dispense = 50

    [csv_raw] = get_values("volume_transfers")  # noqa: F821
    # Expected csv file
    # 	csv_raw = '''
    # source_well,destination_well,transfer_volume
    # A1,A1,546
    # '''
    # csv parsing
    csv_data = csv_raw.splitlines()[1:]  # Discard the blank first line.
    field_names = ["source_well", "destination_well", "transfer_volume"]
    csv_reader = csv.DictReader(csv_data, fieldnames=field_names)

    # validation (since we are using 15mL falcon tubes,
    # we want the transfer volume to not surpass 5mL)
    max_cum_v = 5000
    cum_volumes = {}
    for csv_row in csv_reader:
        source_well = csv_row["source_well"]
        transfer_volume = float(csv_row["transfer_volume"])
        assert transfer_volume > 0
        if source_well not in cum_volumes:
            cum_volumes[source_well] = 0
        cum_volumes[source_well] += transfer_volume
        # ensure cumulative volume is less than 5mL
        if cum_volumes[source_well] > max_cum_v:
            raise Exception(
                f"Cumulative volume from well\
                    {source_well} should not surpass {max_cum_v}.\
                    Add more falcon tubes and modify csv."
            )

    # start protocol
    p300_multi.pick_up_tip(tiprack_300["H1"])
    for csv_row in csv_reader:
        source_well = csv_row["source_well"]
        destination_well = csv_row["destination_well"]

        v_left = float(csv_row["transfer_volume"])
        while v_left > 0:
            transfer_volume = min(p300_multi.max_volume, v_left)
            v_left -= transfer_volume
            p300_multi.move_to(h_falcon.wells(source_well)).top()
            p300_multi.aspirate(
                transfer_volume, h_falcon.wells(source_well).top(z=-40)
            )

            p300_multi.move_to(h_tubes.wells(destination_well).top())
            p300_multi.dispense(
                transfer_volume,
                h_tubes.wells_by_name()[destination_well].top(z=-15),
            )
            protocol.delay(seconds=0.5)
            p300_multi.blow_out(
                h_tubes.wells_by_name()[destination_well].top()
            )
    p300_multi.drop_tip()
    return
