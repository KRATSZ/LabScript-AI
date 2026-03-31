from dataclasses import dataclass
from typing import List
from opentrons import protocol_api
from opentrons.protocol_api import InstrumentContext
from opentrons.protocol_api.labware import Labware

metadata = {
    "apiLevel": "2.12",
    "protocolName": "Standard Biotools Dynamic Array 192.24: Load 4 uL",
    "description": "Transfer Samples+Assays: 96-well plate to Dynamic Array",
    "author": "Standard Biotools",
    "source": "Standard Biotools Inc",
}

metadata2 = {
    "apiLevel": "2.12",
    "protocolName": "Singular BioTools Transfer Method Test V1.0.9",
    "description": (
        """This method replaces /
        adds functionality to the Opentrons transfer method.
        This allows full contol of dispense steps / processes, speeds, etc"""
    ),
    "author": "Standard Biotols",
}

# V1.0.5
# from pydantic import BaseModel
# from pydantic.dataclasses import dataclass

# NOTE Tip Change Never is over-ridden if mixing multiple dispense wells
# need to do multiple transfers of single wells


@dataclass(frozen=True)
class Source:
    """
    Define a liquid source
    Args:
        - plate (Labware): source plate for the aspirate
        - well (list[str]): a single well for the aspirate (e.g., ['A1']).
        Maximum of one well
        - safe_z (float): safe height above top of plate for travel
    Returns:
        None
    Raises:
        None
    """

    plate: Labware = None
    well: List[str] = None  # max length is 1
    safe_z = 3


@dataclass(frozen=True)
class Destination:
    """
    Define a liquid source
    Args:
        - plate (Labware): source plate for the aspirate
        - well (list[str]): a single well for the aspirate (e.g., ['A1']).
        Maximum of one well
        - safe_z (float): safe height above top of plate for travel
    Returns:
        None
    Raises:
        None
    """

    plate: Labware = None
    wells: List[str] = None
    safe_z = 3


@dataclass(frozen=True)
class Aspirate:
    """
    Defines parameters for the aspirate
    - Volume is dictated by the dispense
    - Will aspirate from only 1 source well
    (new step required for mulitple sources)
    Args:
        - flow_rate (float): flow rate is percentage of default. 0.5 is half,
            2 is double
        - z_offset (float): offset (mm) from bottom of well/tube/vessel.
            Negative values OK but
            might hit the bottom of the tube
        - reverse_pipette_dead_vol (float): additional volume aspirated ahead
            of desired volume.
            note this plays a role in max transfer volume of a pipette.
            If this is 10 uL, a p20
            has a max transfer vol of 10 uL and a p200 has max of 190 uL
        - retract_distance (float): distance (mm) the tip will retract after
            the aspirate
        - positive value is retract, negative allowed but will move into tube
        - distance = 0 means no retract
        - retract_speed (float): speed (mm/sec?) to retract. Speed = 0
            means no retract
    Returns:
        None
    Raises:
        - TODO verify dead vol is >0
    """

    # volume: float = 0 aspirate volume is auto calulated //
    # only use if dispense not present
    reverse_pipette_dead_vol: float = 0
    flow_rate: float = 1  # % of default which is 100 uL / sec for p300
    z_offset: float = 0
    retract_distance: float = 0
    retract_speed: float = 2


@dataclass(frozen=True)
class Dispense:
    """
    Defines parameters for the dispense
    - Will aspirate from only 1 source well
        (new step required for mulitple sources)
    Args:
        - volume (float): Total volume to be transferred to each well defined
            in destination.
            The physical transfer volumes are auto calculated.
        - z_offset (float): offset (mm) from bottom of well/tube/vessel.
            Negative values OK but
            might hit the bottom of the tube
        - retract_distance (float): distance (mm) the tip will retract after
            the dispense
            positive value is retract, negative allowed but will move into tube
            distance = 0 means no retract
        - retract_speed (float): speed (mm/sec?) to retract.
            Speed = 0 means no retract
        - air_purge (bool): True uses air to purge residual volume from tip
        - air_purge_z_offset (float): Distance from bottom of tube to perform
            air purge
        - method (str): Options:
            - 'auto': automatically determines one-to-one or
                one-to-many based on volume
            - 'one-to-one': Single Transfer source->dest | source->dest |
                source |destination.
                This method is forced it transfer volume > tip volum
            - 'one-to-many': Distribute Transfer source->dest->dest->dest |
                source->dest->dest
                This method is only supported if dispense_volume*2+asp_dead_vol
                < tip_max_vol
                if p200 and dispense is 100 uL and dead vol is 5, this will
                default to one-to-one
    Returns:
        None
    Raises:
        None
    """

    volume: float = 0
    flow_rate: float = 1
    z_offset: float = 0
    retract_distance: float = 2
    retract_speed: float = 2
    air_purge: bool = False
    air_purge_z_offset: float = 2
    method: str = "auto"  # 'auto', 'one-to-one', 'one-to-many'


@dataclass(frozen=True)
class Mix:
    """
    Defines parameters for the dispense
    - Will aspirate from only 1 source well
    (new step required for mulitple sources)
    Args:
        - mix_location (str): Options = 'source' or 'destination'
        - volume (float): Total volume to be mixed
        - cycles (int): Quantity of mix cycles
        - aspirate_z_offset (float): Distance from bottom of well for Aspirate
            OK to be same as Dispense
        - aspirate_flow_rate (float): Flow rate (% default) for apsirate
        - dispense_z_offset (float): Distance from bottom of well for Dispense.
            OK to be same as Aspirate
        - dispense_flow_rate (float): Flow rate (% default) for dispense

        - retract_distance (float):
            distance (mm) the tip will retract after the aspirate
            - positive value is retract, negative allowed but will crash
            - distance = 0 means no retract
        - retract_speed (float): speed (mm/sec?) to retract.
            Speed = 0 means no retract
        - air_purge (bool): True uses air to purge residual volume from tip
        - air_purge_z_offset (float): Distance from bottom to perform air purge
        - allow_repeat_mix (bool): True: allows a 'dirty' tip to remix this
            source well. False means
            source well will only be mixed on first aspirate,
            unless a new tip is used for
            subsequent aspirates
    Returns:
        None
    Raises:
        None
    """

    # TODO check if pipette is same as current pipette
    mix_location: str = None  # 'source' or 'destination'
    cycles: int = 0
    volume: float = None
    aspirate_z_offset: float = 0
    aspirate_flow_rate: float = 1
    dispense_z_offset: float = 0
    dispense_flow_rate: float = 1
    air_purge: bool = False
    air_purge_z_offset: int = 2  # this is relative to well bottom
    retract_distance: float = 0
    retract_speed: float = 2
    allow_repeat_mix = False


def sbi_transfer(
    pipette: InstrumentContext,
    workflow: List[object],
    robot_protocol: protocol_api.ProtocolContext,
    new_tip: str = "once",
    trash: bool = False,
):
    """
    Transfer step to give more control of the transfer such as mix steps,
        dispense / aspirate speeds
        and pipette retract distance to support low volumnes and
        non-uniform tube heights

    Args:
        - pipette (InstrumentContext): Pipette object
        - workflow (List[object]): List of steps. Examples
            1) Source, Mix
            2) Mix, Destination
            3) Source, Aspirate, Dispense, Destination
            4) Source, Aspirate, Mix, Dispense, Destination
            * Order doesn't matter, either a source or destination is required
        - robot_protocol (protocol_api.ProtocolContext):
            Used for debug, to use protocol features
            such as comment, or pause
        - new_tip (str): defines when to get new tips. Options:
        1) 'once': get's new tip as start and used for entire step, ejected
        2) 'per_destination': ejects tip after each destination
        3) 'always': ejects tip after every step (including mix steps)
        4) 'never': never ejects the tip, keeps it for next step
        - trash (bool): Defines location to eject the tip
        - Not Implemented: dump_liquid (str): 'trash', 'source', 'never'
    Returns:
        None
    Raises:
        None
    """
    # new_tip: 'once', 'per_destination', 'always', 'never'
    # Define max volume pipette
    # Opentrons max_volume doesn't account for filters
    if "10ul" in pipette.tip_racks[0].load_name:
        max_volume = 10
    elif "200ul" in pipette.tip_racks[0].load_name:
        max_volume = 200
    else:
        max_volume = pipette.max_volume

    # pull out the individual events and track the sequence order
    source = mix_1 = aspirate = dispense = mix_2 = destination = None
    for step in workflow:
        if isinstance(step, type(Source())) and not source:
            source: Source = step

        elif (
            isinstance(step, type(Mix()))
            and step.mix_location == "source"
            and not mix_1
        ):
            # TODO check if we need and not aspirate
            mix_1: Mix = step

        elif isinstance(step, type(Aspirate())) and not aspirate:
            aspirate: Aspirate = step

        elif isinstance(step, type(Dispense())) and not dispense:
            dispense: Dispense = step

        elif (
            isinstance(step, type(Mix()))
            and step.mix_location == "destination"
            and not mix_2
        ):
            mix_2: Mix = step

        elif isinstance(step, type(Destination())) and not destination:
            destination: Destination = step
        else:
            raise TypeError("Step is either a duplicate or not recognized")

    # check for proper sequence of events
    if not source or not destination:
        raise TypeError("Source and Destination must be provided")
    if not (aspirate and dispense):
        if (aspirate and not dispense) or (dispense and not aspirate):
            raise TypeError("Aspirate and Dispense must both be present")
            # TODO enable aspirate without dispense to trash liquid
        if not (mix_1 or mix_2):
            raise TypeError(
                "Must have a liquid handling step \
                (either: mix or aspirate+dispsense"
            )
        is_distribute = False
        volumes_to_aspirate = [0]
        volumes_to_dispense = [0]

    if aspirate and dispense:
        if (
            (dispense.method in ["auto", "one-to-many"])
            and
            # Determine if this is a distribute approach
            # Asp -> Disp -> Disp -> Disp
            len(destination.wells) > 1
            and (dispense.volume * 2 + aspirate.reverse_pipette_dead_vol)
            <= max_volume
        ):
            is_distribute = True
            current_aspirate_step = 0
            volumes_to_aspirate = [
                dispense.volume
            ]  # Initial Aspirate is Full Volume
            aspirate_from_source = [True]
            volumes_to_dispense = [dispense.volume]
            effective_max_vol = max_volume - aspirate.reverse_pipette_dead_vol
            # Builds two list defining dispense for each well:
            # Aspirate: [180,  0,  0, 120, 00]
            # Dispense: [ 60, 60, 60,  60, 60]
            for i in range(len(destination.wells)):
                if i == 0:
                    continue
                if (
                    volumes_to_aspirate[current_aspirate_step]
                    + dispense.volume
                    <= effective_max_vol
                ):
                    volumes_to_aspirate[
                        current_aspirate_step
                    ] += dispense.volume
                    volumes_to_aspirate.append(0)
                    aspirate_from_source.append(False)
                else:
                    volumes_to_aspirate.append(dispense.volume)
                    current_aspirate_step = i
                volumes_to_dispense.append(dispense.volume)

        elif (
            dispense.method == "one-to-one"
            or
            # Define a 1-to-1 approach
            # Two modes:
            # Asp -> Disp
            # Aspirate: [120]
            # Dispense: [120]
            # Asp -> Disp | Asp -> Disp | Asp -> Disp All asp will be equal vol
            # Aspirate: [180, 180, 180]
            # Dispense: [180, 180, 180]
            # builds lists, but defines the asp/disp steps for a single well
            # This is done this way so mixing can be done after the transfer
            (dispense.volume * 2 + aspirate.reverse_pipette_dead_vol)
            > max_volume
            or len(destination.wells) == 1
        ):
            is_distribute = False
            effective_max_vol = max_volume - aspirate.reverse_pipette_dead_vol

            qty_dispense_per_destination = int(
                dispense.volume // effective_max_vol
            )
            if dispense.volume % effective_max_vol != 0:
                qty_dispense_per_destination += 1
            # TODO Address rounding error
            equal_dispense_volume = round(
                dispense.volume / qty_dispense_per_destination, 1
            )
            volumes_to_aspirate = [
                equal_dispense_volume
                for _ in range(qty_dispense_per_destination)
            ]
            volumes_to_dispense = [
                equal_dispense_volume
                for _ in range(qty_dispense_per_destination)
            ]
        else:
            raise TypeError("Dispense Method Not Recognized")

    # Process the transfer
    destination_iterator = 1  # 1 based
    # Use while because one-to-many dispense iterates the destination_iterator
    volumes = list(zip(volumes_to_aspirate, volumes_to_dispense))
    while destination_iterator <= len(destination.wells):
        dispense_counter = 0
        # TODO check if i is needed in for loop below, switched to _
        for i, _ in enumerate(volumes_to_dispense):
            current_aspirate_vol = volumes_to_aspirate[i]
            current_dispense_vol = volumes_to_dispense[i]

            current_destination_name = destination.wells[
                destination_iterator - 1
            ]

            if not pipette.has_tip:
                pipette.pick_up_tip()
                fresh_tip = True
            else:
                fresh_tip = False

            if current_aspirate_vol > 0:
                pipette.move_to(
                    source.plate.wells_by_name()[source.well[0]].top(
                        source.safe_z
                    ),
                    force_direct=False,
                )

            force_new_tip = False
            if mix_1 and (fresh_tip or mix_1.allow_repeat_mix):
                # TODO check if this is needed in the conditional above
                # and current_aspirate_vol>0
                if mix_1.volume + pipette.current_volume > max_volume:
                    mix_1_vol = max_volume - (
                        mix_1.volume + pipette.current_volume
                    )
                else:
                    mix_1_vol = mix_1.volume

                if new_tip == "always":
                    force_new_tip = True

                for _ in range(mix_1.cycles):
                    pipette.aspirate(
                        mix_1_vol,
                        source.plate.wells_by_name()[source.well[0]].bottom(
                            mix_1.aspirate_z_offset
                        ),
                        rate=mix_1.aspirate_flow_rate,
                    )

                    if mix_1.retract_distance > 0 and mix_1.retract_speed > 0:
                        # TODO Added V1.0.6 -- verify this
                        pipette.move_to(
                            # TODO turn this into a method
                            location=source.plate.wells_by_name()[
                                source.well[0]
                            ].bottom(
                                mix_1.aspirate_z_offset
                                + mix_1.retract_distance
                            ),
                            force_direct=True,
                            speed=mix_1.retract_speed,
                        )

                    pipette.dispense(
                        mix_1_vol,
                        source.plate.wells_by_name()[source.well[0]].bottom(
                            mix_1.dispense_z_offset
                        ),
                        rate=mix_1.dispense_flow_rate,
                    )

                if mix_1.air_purge:
                    pipette.blow_out(
                        source.plate.wells_by_name()[source.well[0]].bottom(
                            mix_1.air_purge_z_offset
                        )
                    )

            if (
                current_aspirate_vol > 0
                and pipette.current_volume <= aspirate.reverse_pipette_dead_vol
            ):
                if aspirate.reverse_pipette_dead_vol > 0 and fresh_tip:
                    current_aspirate_vol += aspirate.reverse_pipette_dead_vol
                pipette.aspirate(
                    current_aspirate_vol,
                    source.plate.wells_by_name()[source.well[0]].bottom(
                        aspirate.z_offset
                    ),
                    rate=aspirate.flow_rate,
                )
                if (
                    aspirate.retract_distance > 0
                    and aspirate.retract_speed > 0
                ):
                    pipette.move_to(
                        source.plate.wells_by_name()[source.well[0]].bottom(
                            aspirate.z_offset + aspirate.retract_distance
                        ),
                        force_direct=True,
                        speed=aspirate.retract_speed,
                    )
                if source.plate.highest_z > destination.plate.highest_z:
                    pipette.move_to(
                        source.plate.wells_by_name()[source.well[0]].top(
                            source.safe_z
                        ),
                        force_direct=True,
                        minimum_z_height=source.plate.highest_z,
                        speed=pipette.default_speed,
                    )
                else:
                    pipette.move_to(
                        source.plate.wells_by_name()[source.well[0]].top(
                            source.safe_z
                        ),
                        force_direct=True,
                        minimum_z_height=destination.plate.highest_z,
                        speed=pipette.default_speed,
                    )
                if aspirate.reverse_pipette_dead_vol > 0 and fresh_tip:
                    current_aspirate_vol = (
                        current_aspirate_vol
                        - aspirate.reverse_pipette_dead_vol
                    )
                fresh_tip = False

            if current_dispense_vol > 0:
                pipette.dispense(
                    current_dispense_vol,
                    destination.plate.wells_by_name()[
                        current_destination_name
                    ].bottom(dispense.z_offset),
                    rate=dispense.flow_rate,
                )
                if is_distribute:
                    destination_iterator += 1
                else:
                    dispense_counter += 1

            if (
                current_dispense_vol > 0
                and dispense.retract_distance > 0
                and dispense.retract_speed > 0
            ):
                pipette.move_to(
                    # TODO turn this into a method
                    location=destination.plate.wells_by_name()[
                        current_destination_name
                    ].bottom(dispense.z_offset + dispense.retract_distance),
                    force_direct=True,
                    speed=dispense.retract_speed,
                )

            if (
                current_dispense_vol > 0
                and dispense.air_purge
                and not is_distribute
            ):
                if pipette.current_volume > 0:
                    raise ValueError(
                        "AirPurge can not be performed because "
                        f"tip has volume{pipette.current_volume}"
                    )
                pipette.blow_out(
                    destination.plate.wells_by_name()[
                        current_destination_name
                    ].bottom(dispense.z_offset + dispense.air_purge_z_offset)
                )

            if (
                mix_2
                and not is_distribute
                and dispense_counter == len(volumes)
                or mix_2
                and not (mix_1 and aspirate and dispense)
            ):
                # destination mix not allowed for distribute

                if pipette.current_volume > 0:
                    raise RuntimeError("TODO")

                if mix_2.volume > max_volume:
                    mix_2_vol = max_volume
                else:
                    mix_2_vol = mix_2.volume

                if (
                    current_destination_name != destination.wells[-1]
                    or new_tip == "always"
                ):
                    force_new_tip = True
                # TODO move to destination well in case this is a mix only
                for _ in range(mix_2.cycles):
                    pipette.aspirate(
                        mix_2_vol,
                        destination.plate.wells_by_name()[
                            current_destination_name
                        ].bottom(mix_2.aspirate_z_offset),
                        rate=mix_2.aspirate_flow_rate,
                    )

                    if mix_2.retract_distance > 0 and mix_2.retract_speed > 0:
                        # TODO Added V1.0.6 -- verify this
                        pipette.move_to(
                            # TODO turn this into a method
                            location=destination.plate.wells_by_name()[
                                current_destination_name
                            ].bottom(
                                mix_2.aspirate_z_offset
                                + mix_2.retract_distance
                            ),
                            force_direct=True,
                            speed=mix_2.retract_speed,
                        )

                    pipette.dispense(
                        mix_2_vol,
                        destination.plate.wells_by_name()[
                            current_destination_name
                        ].bottom(mix_2.dispense_z_offset),
                        rate=mix_2.dispense_flow_rate,
                    )

                if mix_2.air_purge:
                    pipette.blow_out(
                        destination.plate.wells_by_name()[
                            current_destination_name
                        ].bottom(mix_2.air_purge_z_offset)
                    )

            # TODO REMOVED CONDITIONSIONAL height V1.0.4 -> V1.0.5
            # If collision with plate, use plate.highest_z to define heigh a
            if dispense or mix_2:
                pipette.move_to(
                    destination.plate.wells_by_name()[
                        current_destination_name
                    ].top(destination.safe_z),
                    force_direct=True,
                    minimum_z_height=destination.plate.highest_z,
                    speed=pipette.default_speed,
                )

            # eject tip
            # handle new tips on one_to_many
            if (
                (new_tip == "always" and not is_distribute)
                or (
                    new_tip == "once"
                    and is_distribute
                    and current_destination_name == destination.wells[-1]
                )
                or (
                    new_tip == "once"
                    and (not is_distribute)
                    and current_destination_name == destination.wells[-1]
                    and dispense_counter == len(volumes)
                )
                or (
                    new_tip == "per_destination"
                    and dispense_counter == len(volumes)
                )
                or (mix_1 and not (mix_2) and not (aspirate and dispense))
                or force_new_tip is True
            ):
                if trash:
                    pipette.drop_tip()
                else:
                    pipette.return_tip()
            elif new_tip in ("never", "once", "per_destination"):
                pass
            else:
                raise RuntimeError("Trash method not recognzied")
        if mix_1 and not (mix_2 and aspirate and dispense):
            # only source is being mixed and no transfer fluid,
            # ignore destination cound
            # TODO TEST THIS
            break
        destination_iterator += 1


def run(protocol: protocol_api.ProtocolContext):
    # SETUP
    protocol.set_rail_lights(False)

    # LABWARE / CONSUMABLES
    sample_plate_1 = protocol.load_labware(
        "opentrons_96_aluminumblock_nest_wellplate_100ul", "1"
    )
    ifc_plate = protocol.load_labware("dynamic_array_192_24", "2")
    sample_plate_2 = protocol.load_labware(
        "opentrons_96_aluminumblock_nest_wellplate_100ul", "3"
    )
    p20_tip_s1_to_ifc = protocol.load_labware(
        "opentrons_96_filtertiprack_20ul", "4"
    )
    assay_plate = protocol.load_labware(
        "opentrons_96_aluminumblock_nest_wellplate_100ul", "5"
    )
    p20_tip_s2_to_ifc = protocol.load_labware(
        "opentrons_96_filtertiprack_20ul", "6"
    )
    tube_rack = protocol.load_labware(
        "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", "7"
    )
    p20_tip_assay_to_ifc = protocol.load_labware(
        "opentrons_96_filtertiprack_20ul", "8"
    )
    p200_tip = protocol.load_labware("opentrons_96_filtertiprack_200ul", "11")

    # PIPETTES
    p300 = protocol.load_instrument(
        "p300_single_gen2", "left", tip_racks=[p200_tip]
    )
    p20 = protocol.load_instrument(
        "p20_multi_gen2", "right", tip_racks=[p20_tip_s2_to_ifc]
    )

    # RUN
    protocol.set_rail_lights(True)

    # PREPARE REAGENTS

    # ACTUATION FLUID -> IFC
    # A1 Vol = 150+20
    sbi_transfer(
        pipette=p300,
        workflow=[
            Source(tube_rack, ["A1"]),
            Aspirate(
                z_offset=0,
                reverse_pipette_dead_vol=5,
                retract_distance=6,
                retract_speed=0.75,
            ),
            Dispense(
                volume=150,
                method="auto",
                z_offset=3,
                retract_distance=2,
                retract_speed=0.75,
            ),
            Destination(ifc_plate, ["A7"]),
        ],
        robot_protocol=protocol,
        new_tip="once",
        trash=True,
    )

    # PRESSURE FLUID -> IFC
    # A2 Vol = 370
    p300.pick_up_tip()
    sbi_transfer(
        pipette=p300,
        workflow=[
            Source(tube_rack, ["A2"]),
            Aspirate(
                z_offset=0,
                reverse_pipette_dead_vol=10,
                retract_distance=14,
                retract_speed=2,
            ),
            Dispense(
                volume=150,
                method="auto",
                z_offset=3,
                retract_distance=2,
                retract_speed=2,
            ),
            Destination(ifc_plate, ["R7", "R14"]),
        ],
        robot_protocol=protocol,
        new_tip="never",
        trash=True,
    )

    sbi_transfer(
        pipette=p300,
        workflow=[
            Source(tube_rack, ["A2"]),
            Aspirate(
                z_offset=0,
                reverse_pipette_dead_vol=10,
                retract_distance=14,
                retract_speed=2,
            ),
            Dispense(
                volume=20,
                method="auto",
                z_offset=1,
                retract_distance=2,
                retract_speed=2,
            ),
            Destination(ifc_plate, ["C10", "P11"]),
        ],
        robot_protocol=protocol,
        new_tip="never",
        trash=True,
    )
    p300.drop_tip()

    # ASSAY PLATE 1 -> IFC PLATE
    p20.tip_racks = [p20_tip_assay_to_ifc]
    p20.starting_tip = p20_tip_assay_to_ifc.well("A1")
    plate_wells = ["A1", "A2", "A3"]
    ifc_wells = ["B1", "B20", "C1"]
    for plate_well, ifc_well in list(zip(plate_wells, ifc_wells)):
        sbi_transfer(
            pipette=p20,
            workflow=[
                Source(assay_plate, [plate_well]),
                Aspirate(
                    z_offset=0,
                    retract_distance=3,
                    retract_speed=2,
                    reverse_pipette_dead_vol=0.75,
                ),
                Dispense(
                    volume=3,
                    flow_rate=0.75,
                    method="auto",
                    z_offset=1,
                    retract_distance=3,
                    retract_speed=1,
                ),
                Destination(ifc_plate, [ifc_well]),
            ],
            robot_protocol=protocol,
            new_tip="once",
            trash=True,
        )

    # SAMPLE PLATE 1 -> IFC PLATE
    p20.tip_racks = [p20_tip_s1_to_ifc]
    p20.starting_tip = p20_tip_s1_to_ifc.well("A1")
    plate_wells = [
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "A10",
        "A11",
        "A12",
    ]
    ifc_wells = [
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
    ]
    for plate_well, ifc_well in list(zip(plate_wells, ifc_wells)):
        sbi_transfer(
            pipette=p20,
            workflow=[
                Source(sample_plate_1, [plate_well]),
                Aspirate(
                    z_offset=0,
                    retract_distance=3,
                    retract_speed=2,
                    reverse_pipette_dead_vol=0.75,
                ),
                Dispense(
                    volume=3,
                    flow_rate=0.75,
                    method="auto",
                    z_offset=1,
                    retract_distance=3,
                    retract_speed=1,
                ),
                Destination(ifc_plate, [ifc_well]),
            ],
            robot_protocol=protocol,
            new_tip="once",
            trash=False,
        )

    # SAMPLE PLATE 2 -> IFC PLATE
    p20.tip_racks = [p20_tip_s2_to_ifc]
    p20.starting_tip = p20_tip_s2_to_ifc.well("A1")
    plate_wells = [
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "A10",
        "A11",
        "A12",
    ]
    ifc_wells = [
        "B14",
        "B15",
        "B16",
        "B17",
        "B18",
        "B19",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
    ]
    for plate_well, ifc_well in list(zip(plate_wells, ifc_wells)):
        sbi_transfer(
            pipette=p20,
            workflow=[
                Source(sample_plate_2, [plate_well]),
                Aspirate(
                    z_offset=0,
                    retract_distance=3,
                    retract_speed=2,
                    reverse_pipette_dead_vol=0.75,
                ),
                Dispense(
                    volume=3,
                    flow_rate=0.75,
                    method="auto",
                    z_offset=1,
                    retract_distance=3,
                    retract_speed=1,
                ),
                Destination(ifc_plate, [ifc_well]),
            ],
            robot_protocol=protocol,
            new_tip="once",
            trash=False,
        )

    protocol.set_rail_lights(False)
