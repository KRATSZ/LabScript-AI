from opentrons import protocol_api
from opentrons.protocol_api.labware import Well
import re
from collections import Counter
from typing import Union, Sequence
from math import pi

metadata = {
    'protocolName': 'Advanced cherrypicking',
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def get_tube_liquid_level(
        tube: Well,
        volume: float) -> float:
    radius = (tube.diameter/2) * 0.94
    # 0.95 is a fudge factor because height seems too low
    # for the actual tube volume marks given a volume
    cone_height = 0.171 * tube.depth
    liquid_height = 0

    # Calculate the liquid height in the tube given its volume in mL
    cone_max_vol = (pi*radius**2*cone_height)/3
    # Case where the liquid height extends beyond the tube cone
    if volume > cone_max_vol:
        liquid_height = cone_height
        # Calculate the height of the volume in the cylinder and add it up
        volume -= cone_max_vol
        cylinder_height = volume/(pi*radius**2)
        liquid_height += cylinder_height
        return liquid_height
    else:  # Volume is only inside the cone
        h_cone_calc = 3*volume/(pi*radius**2)
        return h_cone_calc


def aspirate_liq_level(
        pip,
        initial_tube_volume: float,
        aspiration_volume: float,
        tube: Well,
        tip_length: float) -> float:

    liq_height = get_tube_liquid_level(tube, initial_tube_volume)
    # Never aspirate below 1 mm offset
    aspiration_height = round(max(1, liq_height-3/(4*tip_length)), 2)
    aspiration_locn = tube.bottom(aspiration_height)
    pip.aspirate(aspiration_volume, aspiration_locn)
    return aspiration_height


def dispense_liq_level(
        pip,
        initial_tube_volume: float,
        dispensing_volume: float,
        tube: Well) -> float:
    dispensing_height = get_tube_liquid_level(tube, initial_tube_volume)
    dispensing_height += 10
    dispensing_locn = tube.bottom(dispensing_height)
    pip.dispense(dispensing_volume, dispensing_locn)
    return dispensing_height


def get_instruction_param_val(
        params_string: str, param_name: str, type: str) -> Union[
        int, float, str]:
    # Split the comma separated parameters string into individual parameters.
    # Parameters are not case or leading/trailing whitespace sensitive
    params_string = params_string.strip().lower()
    params = params_string.split(',')
    param = ''
    # Look up the parameter/value pair e.g. pause=5m10s
    for p in params:
        if param_name in p:
            param = p
            break
    # Return False if the parameter isn't in the instruction parameters
    if param == '':
        return False
    # Check if there's a value associated with the parameter
    if '=' in param:
        if type == "int":
            return int(param.split('=')[1])
        elif type == "float":
            return float(param.split('=')[1])
        elif type == "str":
            return param.split('=')[1]
        else:
            raise Exception(f"Unrecognized type argument: {type}")
    # Raise an exception if there's no associated value with the parameter
    else:
        err_msg = "There was no associated value with the parameter {}"
        err_msg = err_msg.format(param)
        raise Exception(err_msg)


def reply_to_bool(reply_string: str) -> bool:
    """ Takes a yes/no reply to a question in the form of a string and
    returns a True/False boolean value or None for blank entries. None should
    be treated as an implicit no generally, but it sometimes has special
    meaning in the code, for example if a labware definition has a module
    a blank response at some other point should not be interpreted as a
    conflicting answer, but rather as a subordinate no that is overriden
    by a yes at some other point.
    """

    reply_string = reply_string.strip().lower()
    if reply_string == "yes":
        return True
    if reply_string == "no":
        return False
    if reply_string == "":
        return False
    raise Exception(
        "Unrecognized reply, should be yes or no, or blank. "
        "Blank responses are interpreted as 'no'")


def read_var(input: str, var_type: str) -> Union[str, int, float]:
    """
    Takes an input and checks if it is a blank string.
    If the string is blank it is returned as is, otherwise
    the function converts it to an int or a float depending on
    the value of var_type. Returns a blank string if the input was a blank str.
    """

    if input == '':
        return ''

    if var_type == "int":

        try:
            return int(input)
        except ValueError:
            err_msg = "Error converting the input '{}' to an integer value"
            err_msg = err_msg.format(input)
            raise ValueError(err_msg)

    if var_type == "float":
        try:
            return float(input)
        except ValueError:
            err_msg = "Error converting the input '{}' to a floating value"
            err_msg = err_msg.format(input)
            raise ValueError(err_msg)

    err_msg = f"Unrecognized variable type argument: {var_type}"
    raise Exception(err_msg)


def run(ctx: protocol_api.ProtocolContext):

    [transfer_csv,
     left_mount_pipette_type,
     right_mount_pipette_type,
     left_tip_type,
     right_tip_type,
     left_pip_tiprack_slots,
     right_pip_tiprack_slots,
     tip_reusage_strategy] = get_values(  # noqa: F821
     "transfer_csv",
     "left_mount_pipette_type",
     "right_mount_pipette_type",
     "left_tip_type",
     "right_tip_type",
     "left_pip_tiprack_slots",
     "right_pip_tiprack_slots",
     "tip_reusage_strategy")

    tiprack_map = {
        'p20_single_gen2': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p300_single_gen2': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single_gen2': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        }
    }

    # Tiprack parameter validation e.g. "1, 5, 8, 11"
    # Any whitespace in the string is removed before the comparison
    valid_tiprack_string_regex = re.compile(
        r"^(10|11|[1-9])(,(10|11|[1-9]))*$")
    # regex for matching all kinds of whitespace
    whitespace_re = re.compile(r"\s+")
    # Validate tiprack strings, and create list of tiprack slots
    left_tiprack_slot_list, right_tiprack_slot_list = [], []
    for mount, tiprack_string, slot_list in zip(
            ["left", "right"],
            [left_pip_tiprack_slots, right_pip_tiprack_slots],
            [left_tiprack_slot_list, right_tiprack_slot_list]):
        # Remove all whitespaces in the tiprack parameter string
        tiprack_string_no_ws = re.sub(whitespace_re, '', tiprack_string)
        # Check format validity
        if valid_tiprack_string_regex.match(tiprack_string_no_ws) is None:
            msg = ("The {} pipette tiprack slot list format is invalid, a "
                   "valid specification uses comma separated integers between "
                   "1-11 e.g. \"5, 6, 7\", your string was \"{}\"")
            msg = msg.format(mount, tiprack_string)
            raise Exception(msg)
        # Create a list of tiprack slots
        for slot in tiprack_string_no_ws.split(','):
            slot_list.append(int(slot))
        # Check for duplicates in the list
        if max(Counter(slot_list).values()) > 1:
            msg = "There are duplicates in the {} pipette tiprack slot list {}"
            msg = msg.format(mount, tiprack_string)
            raise Exception(msg)

    # Check for overlap between left and right tiprack slot lists
    # by taking the set intersection (&: Set intersection operator)
    intersection = set(left_tiprack_slot_list) & set(right_tiprack_slot_list)
    if len(intersection) > 0:
        msg = ("There are overlaps between your left and right pipette "
               "tiprack slots in position(s) {}")
        msg = msg.format(intersection)
        raise Exception(msg)

    # Load the CSV
    # ENUMERATED HEADERS:
    # 0. step_id, 1. instruction, 2. instruction_parameters, 3. source_labware,
    # 4. magnetic_module,5. temperature_module, 6. source_slot, 7. source_well,
    # 8. source_well_starting_volume, 9. transfer_volume, 10. air_gap_volume,
    # 11. dest_labware, 12. dest_magnetic_module, 13. dest_temperature_module,
    # 14. dest_slot, 15. dest_well, 16. dest_well_starting_volume,
    # 17. touch_tip, 18. blow_out
    csv_rows = transfer_csv.split("\n")
    csv_list = []
    # Remove any empty lines in the CSV.
    for i, row in enumerate(csv_rows):
        if not row or not row.split(',')[0].strip():
            del csv_rows[i]
        else:
            csv_list.append(row.split(','))

    slot_dict = {}
    for i in range(1, 12):
        slot_dict[i] = []

    instruction_rows = []
    # A well formed well index consists of a letter (A-P) and a number 1-24
    # (because the largest standard labware is the 384 well plate whose indices
    # go from A1 to P24)
    # Regex: Match from the start of the string, then a letter from A to P
    # followed by 0 or 1 instances of [1-2] followed by a number between 0-9,
    # followed by the end of the string.
    correct_well_index_regex = re.compile(r"^[A-P][1-2]?[0-9]$")
    for row in csv_list[1:]:
        step_id = read_var(row[0], "int")
        instruction = row[1].strip().lower()
        instruction_parameters = row[2].strip().lower()
        source_lw = row[3].strip().lower()
        # column 4 and 5 are read below in the `try:` sections
        # 4: is_source_magmod
        # 5: is_source_tempmod
        source_slot = read_var(row[6], "int")
        source_well = row[7].strip().upper()
        source_well_starting_volume = read_var(row[8], "float")
        if source_well_starting_volume == '':
            source_well_starting_volume = 0
        transfer_volume = read_var(row[9], "float")
        air_gap_volume = read_var(row[10], "float")
        if air_gap_volume == '':
            air_gap_volume = 0
        dest_lw = row[11]
        # 12. and 13. loaded below (yes/no) type
        # 12. is_dest_magmod
        # 13. is_dest_tempmod
        dest_slot = read_var(row[14], "int")
        dest_well = row[15].strip().upper()
        dest_well_starting_volume = read_var(row[16], "float")
        # 17., 18., loaded below, yes/no type

        # Check that the well indices are well formed:
        for well_index, designation in zip(
                [source_well, dest_well],
                ["source", "destination"]):
            match = correct_well_index_regex.match(well_index)
            if not match and well_index != '':
                err_msg = ("The {} well {} index for step_id {} is "
                           "invalid. It should start with a letter from A to "
                           "P followed by a number between 1 to 24, e.g. B8")
                err_msg = err_msg.format(
                    designation, source_well, step_id)
                raise Exception(err_msg)

        # Check that the slots are valid:
        for slot, designation in zip(
                [source_slot, dest_slot],
                ["source", "destination"]):
            if slot != '' and not (0 < slot < 12):
                err_msg = ("The {} labware slot ({}) for step_id {} is "
                           "invalid. It should be a number from 1 to 11")
                err_msg = err_msg.format(
                    designation, slot, step_id)
                raise Exception(err_msg)

        # Read the module loading choices (columm 4, 5, 12, and 13)
        try:
            is_source_magmod = reply_to_bool(row[4])
            is_source_tempmod = reply_to_bool(row[5])
        except Exception:
            err_msg = ("Step id {}: Unrecognized option for the source "
                       "labware modules. Valid options are 'yes' or 'no' "
                       "or a blank entry")
            err_msg = err_msg.format(step_id)
            raise Exception(err_msg)
        try:
            is_dest_magmod = reply_to_bool(row[12])
            is_dest_tempmod = reply_to_bool(row[13])
        except Exception:
            err_msg = ("Step id {}: Unrecognized option for the destination "
                       "labware modules. Valid options are 'yes' or 'no'. "
                       "Please correct your CSV file.")
            err_msg = err_msg.format(step_id)
            raise Exception(err_msg)

        # Create an entry for the given slots labware and add it to slot_dict
        for slot, labware, magmod, tmod in zip(
                [source_slot, dest_slot],
                [source_lw, dest_lw],
                [is_source_magmod, is_dest_magmod],
                [is_source_tempmod, is_dest_tempmod]):

            if type(slot) is int:  # slot could be a blank string, should skip.
                slot_dict[slot].append((step_id, labware, magmod, tmod))
        try:
            is_touch_tip = reply_to_bool(row[17])
            is_blowout = reply_to_bool(row[18])
        except Exception:
            err_msg = ("Step id {}: Unrecognized option for touch tip and/or "
                       "blow out options. Valid options are 'yes' or 'no', "
                       "or a blank value. Please correct your CSV file.")
            err_msg = err_msg.format(step_id)
            raise Exception(err_msg)

        # Check for error where both temperature and magnetic modules are
        # loaded for the same labware/slot.
        for is_magmod, is_tempmod, type_string in zip(
                [is_source_magmod, is_dest_magmod],
                [is_source_tempmod, is_dest_tempmod],
                ["source", "destination"]):
            if is_magmod and is_tempmod:
                err_msg = ("Error in {} labware module options with "
                           "step_id {}: " "You cannot use both a magnetic "
                           "module and a temperature module with the same "
                           "labware/slot, please inspect your CSV file.")
                err_msg = err_msg.format(type_string, step_id)
                raise Exception(err_msg)

        # Check that labware used with the temperature module uses alum. blocks
        for is_tempmod, labware, type_string in zip(
                [is_source_tempmod, is_dest_tempmod],
                [source_lw, dest_lw],
                ["Source", "Destination"]):
            if is_tempmod and "aluminum" not in labware:
                err_msg = ("Step id {}: {} labware must be of an aluminum "
                           "block type to be used with a temperature module")
                err_msg = err_msg.format(step_id, type_string)
                raise Exception(err_msg)

        # Make sure the well indices are well formed
        for well_index in zip(
                [source_well, dest_well],
                ["source", "destination"]):
            pass

        instruction_rows.append(
            (step_id,  # 0
             instruction,  # 1
             instruction_parameters,  # 2
             source_lw,  # 3
             is_source_magmod,  # 4
             is_source_tempmod,  # 5
             source_slot,  # 6
             source_well,  # 7
             source_well_starting_volume,  # 8
             transfer_volume,  # 9
             air_gap_volume,  # 10
             dest_lw,  # 11
             is_dest_magmod,  # 12
             is_dest_tempmod,  # 13
             dest_slot,  # 14
             dest_well,  # 15
             dest_well_starting_volume,  # 16
             is_touch_tip,  # 17
             is_blowout  # 18
             ))

    # Check that the step_ids are continous
    last_step_id = instruction_rows[0][0]
    # Save the first step id so we can convert from step_id to list index
    # later
    first_step_id = last_step_id
    if first_step_id < 0:
        raise Exception(
            "Negative step id:s are reserved, please inspect your CSV")
    # Skip the first row, last_step_id is already set and we don't want to
    # compare it to itself
    for row in instruction_rows[1:]:
        id = row[0]
        if not id == last_step_id + 1:
            err_msg = "Discontinuity in step id:s between step_id {} and {}"
            err_msg = err_msg.format(last_step_id, id)
            raise Exception(err_msg)
        last_step_id = id

    def step_id_to_index(step_id: int) -> int:
        """Converts a given step id to an index in the instruction_rows list
        """

        nonlocal first_step_id
        return step_id - first_step_id

    # Check that there are no mismatching entries in the labware definitions
    # Algorithm:
    # 1. Add the tiprack entries to the slot dicts as well
    # 2. Go through the dictionary entry for each slot in slots_dict and:
    # 3. Treat the first labware entry as canon and require that it is well
    # formed. It should have a labware API name, a slot, and should give
    # complete answers about what modules it is using and not using.
    # 4. Compare the 'canonical' definition to the subseqent ones for that slot
    # 5. If the the subst. defns. are identical continue looping
    # 6. If they are not: Raise an error and point out what the conflicting
    # step_id:s are, (unless it's a conflict with a tiprack which don't have
    # step_id:s), what labware API names, which slot
    # After the canonical entry is properly entered
    # it is allowed to specify only the slot as long
    # as the other fields are just blank strings ('').
    # 7. If there are no mismatching data the labware and tipracks
    # can be loaded.

    # Implementation
    # 1.1 Add the  pipette tipracks to their respective slot lists
    left_tips_lname = False
    if left_mount_pipette_type:
        left_tips_lname = tiprack_map[
            left_mount_pipette_type][left_tip_type]
        for slot in left_tiprack_slot_list:
            slot_dict[slot].append((-1, left_tips_lname, "left_mount"))

    right_tips_lname = False
    if right_mount_pipette_type:
        right_tips_lname = tiprack_map[
            right_mount_pipette_type][right_tip_type]
        for slot in right_tiprack_slot_list:
            slot_dict[slot].append((-1, right_tips_lname, "right_mount"))

    # 2. Iterate over the dictionary entries
    for slot in slot_dict.keys():
        # Check for cases where there's no labware definitions for the slot
        # and continue to the next slot.
        if len(slot_dict[slot]) == 0:
            continue
        # Skip tipracks (they are given step_id=-1):
        if slot_dict[slot][0][0] == -1:
            continue
        # Canonical labware entry, must be well formed
        canonical_lw_entry = slot_dict[slot][0]
        canonical_step_id = canonical_lw_entry[0]
        canonical_lw_name = canonical_lw_entry[1]
        canonical_magmod = canonical_lw_entry[2]
        canonical_tempmod = canonical_lw_entry[3]

        # Check that the canonical entry is well defined
        if canonical_lw_name == '' or canonical_magmod is None \
                or canonical_tempmod is None:
            err_msg = ("The initial labware definition for slot {} on the "
                       "row with step_id {} is not well defined. It must "
                       "include the labware API name and definite yes/no "
                       "answers to the questions asking whether they are "
                       "using either the Magnetic- or the Temperature module. "
                       "Please inspect your CSV file.")
            err_msg = err_msg.format(slot, canonical_step_id)
            raise Exception(err_msg)

        for lw_entry in slot_dict[slot][1:]:

            entry_step_id = lw_entry[0]
            entry_lw_name = lw_entry[1]
            entry_magmod = lw_entry[2]
            entry_tempmod = lw_entry[3]
            slot

            if canonical_lw_name != entry_lw_name and entry_lw_name != '':
                err_msg = ("There is a mismatch between the labware API names "
                           "for slot {}, the initial labware API name was {} "
                           "and it was defined in the row with step_id {} "
                           "but there is a mismatching API name ({}) on the "
                           "row with step_id {}. Please inspect your CSV.")
                err_msg = err_msg.format(
                    slot, canonical_lw_name, canonical_step_id,
                    entry_lw_name, entry_step_id)
                raise Exception(err_msg)

            # Check for magnetic module setting mismatches
            if canonical_magmod != entry_magmod and entry_magmod is not None:
                err_msg = ("There is a mismatch between the Magnetic module "
                           "setting for {} on slot {} on the row with "
                           "step_id {}, and the Magnetic module setting on "
                           "the row with step id {}. Please inspect your "
                           "CSV input file.")
                err_msg = err_msg.format(
                    canonical_lw_name, slot, canonical_step_id, entry_step_id)

            # Check for Temperature module setting mismatches
            if canonical_tempmod != entry_tempmod \
                    and entry_tempmod is not None:
                err_msg = ("There is a mismatch between the Temperature "
                           "module setting for {} on slot {} on the row with "
                           "step_id {}, and the Temperature module setting on "
                           "the row with step id {}. Please inspect your "
                           "CSV input file.")
                err_msg = err_msg.format(
                    canonical_lw_name, slot, canonical_step_id, entry_step_id)

    # Check that 'dispense parked tip operations' are well formed. This means:
    # 1. Not attempting to dispense an already dispensed parked tip
    # 2. There must be minimally complete instructions for dispensing the tip
    # meaning: dispensing volume, destination- slot and well.
    # 3. dispense_parked_tip instructions must refer to step_id:s of
    # aspirate_and_park_tip instructions

    # 1. Check that all step_id instruction_rows for selecting a parked tip are
    # unique
    dispense_parked_tip_step_id_list = []
    for instruction in instruction_rows:
        disp_step_id = instruction[0]
        if instruction[1] == 'dispense_parked_tip':
            # Fetch the reference to the instruction where the tip was parked
            # earlier
            parking_instruction_id = get_instruction_param_val(
                instruction[2], "step_id", "int")
            dispense_parked_tip_step_id_list.append(parking_instruction_id)
            # 3rd point Make sure the fetched step_id refers to an
            # instruction to and aspirate_and_park_tip instruction.
            trial_park_instrn_row = instruction_rows[
                step_id_to_index(parking_instruction_id)]
            possible_park_instrn = trial_park_instrn_row[1]
            if possible_park_instrn != "aspirate_and_park_tip":
                err_msg = ("The dispense_parked_tip instruction with step "
                           "id {} refers to step_id {} which is not an "
                           "aspirate_and_park_tip instruction, "
                           "inspect your CSV")
                err_msg = err_msg.format(disp_step_id, parking_instruction_id)
                raise Exception(err_msg)

            # For 2: check the presence of the parameters
            # transfer_volume index: 9
            # Destination slot: 14
            # Destination well: 15
            transfer_vol = instruction[9]
            dest_slot = instruction[14]
            dest_well = instruction[15]
            for val, designation in zip(
                    [transfer_vol, dest_slot, dest_well],
                    ["transfer volume", "destination slot",
                     "destination well"]):
                if val == '':
                    err_msg = ("The {} value is blank for the "
                               "dispense_parked_tip instruction with "
                               "step_id {}.")
                    err_msg = err_msg.format(designation, disp_step_id)
                    raise Exception(err_msg)

    # For point 1: Count the occurences of each step_id, make sure there
    # are only singular references so no double dispenses are tried.
    step_id_occurences = Counter(dispense_parked_tip_step_id_list)
    # Check the length of the list first, there might not be any entries
    if len(dispense_parked_tip_step_id_list) > 0 \
            and max(step_id_occurences.values()) > 1:
        err_msg = ("There are multiples references to the same step_id for "
                   "dispensing a parked tip. Can't dispense an already "
                   "dispensed tip. Please inspect your input CSV file.")
        raise Exception(err_msg)

    # Check 'aspirate_and_park_tip' instructions for validity
    # A complete instruction must include the following (besides the
    # instruction name which is aspirate_and_park_tip):
    # 1. A source slot 2. A source well. 3. An aspiration volume (and a step
    # id but step_id:s are validated elsewhere)
    for instruction in instruction_rows:
        asp_step_id = instruction[0]
        if instruction[1] == 'aspirate_and_park_tip':

            # Check the presence of the required parametere
            # transfer_volume index: 9
            # Source slot: 6
            # Source well: 7
            transfer_vol = instruction[9]
            source_slot = instruction[6]
            source_well = instruction[7]
            for val, designation in zip(
                    [transfer_vol, source_slot, source_well],
                    ["transfer volume", "source slot",
                     "source well"]):
                if val == '':
                    err_msg = ("The {} value is blank for the "
                               "aspirate_and_park_tip instruction "
                               "with step_id {}.")
                    err_msg = err_msg.format(designation, asp_step_id)
                    raise Exception(err_msg)

    # Check well-formness of pause entries
    # Pause entries need to match at least one unit of time entry, i.e.
    # hours, minutes or seconds.
    hour_match_regex = re.compile(r"[0-9]+\.?[0-9]*h")
    minute_match_regex = re.compile(r"[0-9]+\.?[0-9]*m")
    second_match_regex = re.compile(r"[0-9]+\.?[0-9]*s")
    for instruction in instruction_rows:
        if instruction[1] == 'pause':
            pause_step_id = instruction[0]
            pause_time_str = get_instruction_param_val(
                instruction[2], "time", "str")
            if pause_time_str is False:
                err_msg = ("Could not find an associated pause time "
                           "instruction parameter for the pause instruction "
                           "with step_id {}. Please inspect your CSV input. "
                           "A Proper instruction parameter is e.g. "
                           "time=5m30s or time=1h10m")
                err_msg = err_msg.format(pause_step_id)
                raise Exception(err_msg)
            hour_match = hour_match_regex.search(pause_time_str)
            minute_match = minute_match_regex.search(pause_time_str)
            second_match = second_match_regex.search(pause_time_str)
            if not hour_match and not minute_match and not second_match:
                err_msg = ("The pause instruction parameter for step_id {} "
                           "does not seem to define a pause time. "
                           "The instruction was {}. The proper format is "
                           "some combination of [<x>h][<y>m][<z>s] "
                           "e.g. '5m30s' or '10s' or '1h10m30s'")
                err_msg = err_msg.format(
                    pause_step_id, pause_time_str)

    # Check the transfer instructions for validity
    # A valid transfer instruction must minimally consist of
    # 1,2. A source slot and well, 3: A transfer volume, 4,5 A destination slot
    # and a destination well.
    for instruction in instruction_rows:
        asp_step_id = instruction[0]
        if instruction[1] == 'transfer':

            # Check the presence of the required parametere
            # transfer_volume index: 9
            # Source slot: 6
            # Source well: 7
            # Destination slot: 14
            # Destination well: 15
            dest_slot = instruction[14]
            transfer_vol = instruction[9]
            source_slot = instruction[6]
            source_well = instruction[7]
            for val, designation in zip(
                    [transfer_vol, source_slot, source_well],
                    ["transfer volume", "source slot",
                     "source well"]):
                if val == '':
                    err_msg = ("The {} value is blank for the "
                               "transfer instruction "
                               "with step_id {}.")
                    err_msg = err_msg.format(designation, asp_step_id)
                    raise Exception(err_msg)

    temp_mods = {}
    mag_mods = {}

    # load labware and tipracks from the slot_dict entries
    labware_dict = {}
    labware_dict["left_mount"] = {}
    labware_dict["right_mount"] = {}
    labware_dict["labware"] = {}
    for slot_number, entry in zip(slot_dict.keys(), slot_dict.values()):
        if len(entry) > 0:  # Skip empty deck slots
            # Tiprack identifier is step_id==-1, load the tiprack in the entry
            first_entry = entry[0]
            if first_entry[0] == -1:
                tiprack_lname = first_entry[1]
                mount = first_entry[2]
                tiprack = ctx.load_labware(tiprack_lname, slot_number)
                labware_dict[mount][slot_number] = tiprack
            # Load on a Magnetic module?
            elif first_entry[2] is True:
                mag_mod = ctx.load_module('magnetic module gen2', slot_number)
                mag_mods[slot_number] = mag_mod
                labware_lname = first_entry[1]
                labware = mag_mod.load_labware(labware_lname)
                labware_dict["labware"][slot_number] = labware
            # Load on Temperature module?
            elif first_entry[3] is True:
                temp_mod = ctx.load_module(
                    'temperature module gen2', slot_number)
                temp_mods[slot_number] = temp_mod
                labware_lname = first_entry[1]
                labware = temp_mod.load_labware(labware_lname)
                labware_dict["labware"][slot_number] = labware
            # Load directly on the deck
            else:
                labware_lname = first_entry[1]
                labware = ctx.load_labware(labware_lname, slot_number)
                labware_dict["labware"][slot_number] = labware

    # Calculate final volumes for all wells, raise an Exception if the
    # operations in the CSV results in filling any well more than 80 % of
    # the max volume
    # Algoritm:
    # Read the transfer volume, destination well, and destination slot for
    # The transfer instructions, and the dispense pipette tip instructions.
    # When a new slot/well combo is encountered add it as a tuple key to a
    # dictionary. Before adding any combinations the dictionary is checked
    # to see if there's already an entry.
    # If there is not an entry: Use the starting volume as the value for the
    # key entry+the transfer volume.
    # If there is already an entry: Add the transfer volume to the entry
    # For each change of the entry check the entry against being above
    # 80 % of the well max volume. The dictionary contains a class with two
    # fields: current volume and max volume and a function to check itself
    # for overflows (is_overflow())

    class OverflowTracker:
        def __init__(self, well_max_vol, current_vol):
            self.well_max_vol = well_max_vol
            self.current_vol = current_vol

        def is_overflow(self) -> bool:
            return True if \
                self.current_vol > 0.8 * self.well_max_vol else False

        def add_vol(self, vol):
            self.current_vol += vol

    well_dict = {}
    overflow_list = []
    for instruction in instruction_rows:
        step_id = instruction[0]
        instr = instruction[1]
        if instr == "transfer" or instruction == "dispense_parked_tip":
            step_id = instruction[0]
            dest_slot = instruction[14]
            dest_well = instruction[15]
            transfer_volume = instruction[9]
            init_dest_well_vol = instruction[16]
            # Check if the tuple of (slot, well) is already in the dict.
            # otherwise create the entry
            entry: OverflowTracker = well_dict.get((dest_slot, dest_well))
            labware = labware_dict["labware"][dest_slot]
            try:
                well: Well = labware.wells_by_name()[dest_well]
            except KeyError:
                err_msg = (f"Could not retrieve well {dest_well} on {labware}."
                           " Does such a well exist on your labware?")
                raise Exception(err_msg)
            if entry:
                entry.add_vol(transfer_vol)
            else:
                # Retrieve the labware and get the max well volume
                current_vol = transfer_vol
                if init_dest_well_vol != '':
                    current_vol += init_dest_well_vol
                well_dict[(dest_slot, dest_well)] = \
                    OverflowTracker(well.max_volume, current_vol)

            # Check if there is overflow, if so add the step at which overflow
            # occurs and add it to a list
            entry: OverflowTracker = well_dict[(dest_slot, dest_well)]
            # Overflow entry: A tuple of step_id, slot, well, the max well vol
            # and the current volume
            if entry.is_overflow():
                overflow_list.append((
                    step_id,  # 0
                    dest_well,  # 1
                    dest_slot,  # 2
                    entry.current_vol,  # 3
                    entry.well_max_vol))  # 4

    # Loop through the overflow entries and report errors
    if len(overflow_list) > 0:
        msg = "\n"
        for entry in overflow_list:
            msg = (msg +
                   f"Step ID {entry[0]}: Overflow in well {entry[1]} on slot "
                   f"{entry[2]}, executing this step would cause the total "
                   f"volume to be {entry[3]} uL, while the well's 80 % of max "
                   f"volume is {0.8*entry[4]} uL\n")

    # load pipette(s)
    left_tipracks_dict_vals = labware_dict["left_mount"].values()
    right_tipracks_dict_vals = labware_dict["right_mount"].values()
    left_tipracks = [rack for rack in left_tipracks_dict_vals]
    right_tipracks = [rack for rack in right_tipracks_dict_vals]
    pip_left = False
    pip_right = False
    if left_mount_pipette_type:
        pip_left = ctx.load_instrument(
          left_mount_pipette_type, "left", tip_racks=left_tipracks)
    if right_mount_pipette_type:
        pip_right = ctx.load_instrument(
          right_mount_pipette_type, "right", tip_racks=right_tipracks)

    # Save the tip lengths for liquid height tracking/offset aspiration:
    tip_length_dict = {}
    if pip_left:
        tip_length_dict[pip_left] = left_tipracks[0].tip_length
    if pip_right:
        tip_length_dict[pip_right] = right_tipracks[0].tip_length

    def pick_up(pipette, is_reuse_tip):
        """`pick_up()` will pause the protocol when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the protocol will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the protocol (e.g. p300, m20).
        """
        if is_reuse_tip and pipette.has_tip:
            return
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    def drop_tip(pip, is_reuse_tip):
        """
        Drops the tip unless the strategy is to reuse the same tip.
        """
        if is_reuse_tip is True:
            return
        else:
            pip.drop_tip()

    def select_pip(volume, is_single_action=False):
        """ Returns the correct pipette for the transfer and its max volume
        :param volume: The (total) volume to use the pipette with
        :param is_single_action: True if the aspiration/dispense should be
        completed with a single aspiration or dispense (i.e. no splitting up
        of the operations into smaller volumes is allowed). Used for aspirate
        and park operations.
        """
        nonlocal pip_left, pip_right, left_mount_pipette_type
        nonlocal right_mount_pipette_type, left_tip_type, right_tip_type

        # Aspirate and park tip pipette selection
        if is_single_action:
            if volume < 20.01:
                if pip_left and "20" in left_mount_pipette_type:
                    return pip_left, 20
                elif pip_right and "20" in right_mount_pipette_type:
                    return pip_right, 20
                else:
                    raise Exception(
                        ("There is no 20 uL pipette loaded for aspirating and "
                         f"parking a volume of {volume} uL"))
            elif volume < 200.01:
                if pip_left and "300" in left_mount_pipette_type:
                    max_vol = 200 if left_tip_type == "filter" else 300
                    return pip_left, max_vol
                elif pip_right and "300" in right_mount_pipette_type:
                    max_vol = 200 if right_tip_type == "filter" else 300
                    return pip_right, max_vol
                else:
                    raise Exception(
                        ("There is no 300 uL pipette loaded for aspirating "
                         f"and parking a volume of {volume} uL"))
            elif volume < 300.01:
                if pip_left and "300" in left_mount_pipette_type \
                        and left_tip_type == "standard":
                    return pip_left, 300
                elif pip_right and "300" in right_mount_pipette_type \
                        and right_tip_type == "standard":
                    return pip_right, 300
                else:
                    raise Exception(
                        ("There is no 300 uL pipette loaded for aspirating "
                         f"and parking a volume of {volume} uL"))
            elif volume < 1000.01:
                if pip_left and "1000" in left_mount_pipette_type:
                    return pip_left, 1000
                elif pip_right and "1000" in right_mount_pipette_type:
                    return pip_right, 1000
                else:
                    raise Exception(
                        ("There is no 1000 uL pipette loaded for handling a "
                         f"transfer volume of {volume} uL"))
            else:
                raise Exception(
                    "Cannot aspirate and park a tip for an aspiration "
                    f"volume of {volume}")

        if volume < 100.01:
            if pip_left and "20" in left_mount_pipette_type:
                return pip_left, 20
            elif pip_right and "20" in right_mount_pipette_type:
                return pip_right, 20
            elif pip_left and "300" in left_mount_pipette_type:
                max_vol = 200 if left_tip_type == "filter" else 300
                return pip_left, max_vol
            elif pip_right and "300" in right_mount_pipette_type:
                max_vol = 200 if right_tip_type == "filter" else 300
                return pip_right, max_vol
            else:
                raise Exception(
                    ("There is no 20 uL pipette loaded for handling a "
                     f"transfer volume of {volume} uL"))
        elif volume < 1000.01:
            if pip_left and "300" in left_mount_pipette_type:
                max_vol = 200 if left_tip_type == "filter" else 300
                return pip_left, max_vol
            elif pip_right and "300" in right_mount_pipette_type:
                max_vol = 200 if right_tip_type == "filter" else 300
                return pip_right, max_vol
            elif pip_right and "1000" in right_mount_pipette_type:
                return pip_right, 1000
            elif pip_left and "1000" in left_mount_pipette_type:
                return pip_left, 1000
            else:
                raise Exception(
                    ("There is no 300 uL pipette loaded for handling a "
                     f"transfer volume of {volume} uL"))
        else:
            if pip_left and "1000" in left_mount_pipette_type:
                return pip_left, 1000
            elif pip_right and "1000" in right_mount_pipette_type:
                return pip_right, 1000
            else:
                raise Exception(
                    ("There is no 1000 uL pipette loaded for handling a "
                     f"transfer volume of {volume} uL"))

    tube_volume_track_dict = {}
    tube_regex = re.compile(r"(15|50)ml_conical")

    def track_tubes_liq_lvl(
            lnames: Sequence[str],
            wells: Sequence[Well],
            initial_volumes: Sequence[float],
            transfer_vol: float):
        # Liquid level tracking for 15/15mL conicals
        nonlocal tube_regex, tube_volume_track_dict
        is_source_tube = False
        is_dest_tube = False
        for lname, well, init_vol, is_source in zip(
                lnames, wells, initial_volumes, [True, False]):
            # Not all instructions will have both a source and a destination lw
            if not lname or lname == '':
                continue
            if tube_regex.search(lname):  # Match for 15/50 mL conicals
                # Store the well (key) and volume value pair
                # If the entry doesn't exist yet set the volume to
                # the initial volume +/- the transfer volume, that is
                # subtract if the well is a source, and add if it's a
                # destination.
                if is_source:
                    is_source_tube = True
                else:
                    is_dest_tube = True
                volume_change = -transfer_vol if is_source else \
                    transfer_vol
                if tube_volume_track_dict.get(well):
                    tube_volume_track_dict[well] += volume_change
                else:
                    # The dictionary entry doesn't exist because this is
                    # the first time we encountered this tube during
                    # execution.
                    tube_volume_track_dict[well] \
                        = init_vol + volume_change
        return is_source_tube, is_dest_tube

    # --- PROTOCOL EXECUTION STARTS HERE ---
    # Loop through the instructions and execute them
    parked_tip_dict = {}
    # Add slot, well tuples as keys and the well volume as the value when
    # carrying out operations involving tubes. Use the value for liquid height
    # tracking
    #
    for instruction in instruction_rows:
        step_id = instruction[0]
        instr = instruction[1]
        # Transfer instruction algorithm:
        # The source slot/well data [6,7] in the instruction is retrieves
        # The well to aspirate from, and the destination slot/well is used to
        # find what well to dispense into. Transfer volume informs how much vol
        # to aspirate and dispense.
        # The other parameters that matter are
        # step id [0]: Report what step is being done. air_gap_volume [10],
        # touch_tip [17] and blow_out [18]

        if instr == "transfer":
            source_slot = instruction[6]
            source_well = instruction[7]
            transfer_vol = instruction[9]
            source_initial_well_vol = instruction[8]
            air_gap_volume = instruction[10]
            dest_slot = instruction[14]
            dest_well = instruction[15]
            dest_initial_well_vol = instruction[16]
            is_touch_tip = instruction[17]
            is_blowout = instruction[18]

            # Retrieve the source and destn. labware and their wells:
            source_lw = labware_dict["labware"][source_slot]
            source_well = source_lw.wells_by_name()[source_well]
            dest_lw = labware_dict["labware"][dest_slot]
            dest_well = dest_lw.wells_by_name()[dest_well]
            source_lw_lname = source_lw.load_name
            dest_lw_lname = dest_lw.load_name
            is_source_tube = False
            is_dest_tube = False

            is_source_tube, is_dest_tube = track_tubes_liq_lvl(
                lnames=[source_lw_lname, dest_lw_lname],
                wells=[source_well, dest_well],
                initial_volumes=[
                    source_initial_well_vol, dest_initial_well_vol],
                transfer_vol=transfer_vol)

            ctx.comment(
                f"\n\nExecuting transfer instruction with step_id {step_id}\n")

            try:
                pip, max_pip_vol = select_pip(transfer_vol)
            except Exception:
                raise Exception(
                    f"Error in executing instruction at step_id {step_id}")
            ctx.comment(f"Selected the {pip} for the transfer")
            max_asp_vol = max_pip_vol - air_gap_volume

            pick_up(pip, tip_reusage_strategy)
            while transfer_vol > 0:
                aspiration_vol = min(transfer_vol, max_asp_vol)
                if is_source_tube:
                    height = aspirate_liq_level(
                        pip=pip,
                        initial_tube_volume=tube_volume_track_dict[
                            source_well],
                        aspiration_volume=aspiration_vol,
                        tube=source_well,
                        tip_length=tip_length_dict[pip])
                    ctx.comment(
                        f"Aspirated from tube {source_well} "
                        f"at a height offset of {height} mm")
                else:
                    pip.aspirate(aspiration_vol, source_well)
                if air_gap_volume > 0:
                    pip.air_gap(air_gap_volume)
                if is_dest_tube:
                    disp_height = dispense_liq_level(
                        pip=pip,
                        initial_tube_volume=tube_volume_track_dict[
                            dest_well],
                        dispensing_volume=aspiration_vol+air_gap_volume,
                        tube=dest_well)
                    ctx.comment(
                        f"Dispensed {aspiration_vol} uL to tube {dest_well} "
                        f"at a height offset of {disp_height} mm")
                else:
                    pip.dispense(aspiration_vol+air_gap_volume, dest_well)
                if is_touch_tip:
                    pip.touch_tip()
                if is_blowout:
                    pip.blow_out()
                transfer_vol -= aspiration_vol
            drop_tip(pip, tip_reusage_strategy)

        elif instr == "aspirate_and_park_tip":
            ctx.comment(
                "\n\nExecuting 'aspirate and park tip' instruction with "
                f"step_id {step_id}\n")
            source_slot = instruction[6]
            source_well = instruction[7]
            source_initial_well_vol = instruction[8]
            transfer_vol = instruction[9]
            air_gap_volume = instruction[10]
            is_touch_tip = instruction[17]
            is_blowout = instruction[18]
            source_lw_lname = source_lw.load_name
            is_source_tube = False

            # Retrieve wells:
            source_lw = labware_dict["labware"][source_slot]
            source_well = source_lw.wells_by_name()[source_well]

            # Check if tubes are involved and track liquid levels:
            track_tubes_liq_lvl(
                lnames=[source_lw_lname, None],
                wells=[source_well, None],
                initial_volumes=[source_initial_well_vol, 0],
                transfer_vol=[transfer_vol])

            pip, _ = select_pip(
                transfer_vol+air_gap_volume,
                is_single_action=True)
            ctx.comment(f"Selected the {pip} for the aspiration")
            pick_up(pip, tip_reusage_strategy)
            tip_parking_well = pip._last_tip_picked_up_from
            # Save the well where the tip was parked as well as the tip used
            # so that the protocol knows how to dispense it later.
            parked_tip_dict[step_id] = tip_parking_well, pip
            if is_source_tube:
                asp_height = aspirate_liq_level(
                    pip=pip,
                    initial_tube_volume=tube_volume_track_dict[
                        source_well],
                    aspiration_volume=transfer_vol,
                    tube=source_well,
                    tip_length=tip_length_dict[pip])
                tube_volume_track_dict[source_well] -= aspiration_vol
                ctx.comment(
                    f"Aspirated {transfer_vol} uL from tube {source_well} "
                    f"at a height offset of {asp_height} mm")
            else:
                pip.aspirate(transfer_vol, source_well)
            if air_gap_volume > 0:
                pip.air_gap(air_gap_volume)
            pip.return_tip()

        elif instr == "dispense_parked_tip":
            ctx.comment(
                "\n\nExecuting 'dispense parked tip' instruction with "
                f"step_id {step_id}\n")
            # Retrieve the step id for the action where the tip was parked
            aspiration_and_park_step_id = get_instruction_param_val(
                instruction[2], "step_id", "int")
            parked_tip_well, pip = parked_tip_dict[aspiration_and_park_step_id]
            ctx.comment(
                f"Selected the {pip} for the pick up parked tip and dispense")
            transfer_vol = instruction[9]
            air_gap_volume = instruction[10]
            dest_slot = instruction[14]
            dest_well = instruction[15]
            dest_initial_well_vol = instruction[16]
            is_touch_tip = instruction[17]
            is_blowout = instruction[18]

            # Retrieve target well:
            dest_lw = labware_dict["labware"][dest_slot]
            dest_well = dest_lw.wells_by_name()[dest_well]
            dest_lw_lname = dest_lw.load_name
            is_dest_tube = False

            # Check if the target well is a tube and track liquid height if so
            _, is_dest_tube = track_tubes_liq_lvl(
                lnames=[None, dest_lw_lname],
                wells=[None, dest_well],
                initial_volumes=[0, dest_initial_well_vol],
                transfer_vol=transfer_vol)

            if pip.has_tip:
                pip.drop_tip()
            pip.pick_up_tip(parked_tip_well)
            if is_dest_tube:
                disp_height = dispense_liq_level(
                    pip=pip,
                    initial_tube_volume=tube_volume_track_dict[
                        dest_well],
                    dispensing_volume=transfer_vol+air_gap_volume,
                    tube=dest_well)
                ctx.comment(
                    f"Dispensed {transfer_vol} uL to tube {dest_well} "
                    f"at a height offset of {disp_height} mm")
            else:
                pip.dispense(transfer_vol+air_gap_volume, dest_well)
            drop_tip(pip, tip_reusage_strategy)
        elif instr == "pause":
            ctx.comment(
                f"\n\nExecuting pause instruction with step_id {step_id}")
            time_param = get_instruction_param_val(
                instruction[2],
                "time",
                "str")
            hour_match = hour_match_regex.search(time_param)
            minute_match = minute_match_regex.search(time_param)
            second_match = second_match_regex.search(time_param)
            hours = 0
            minutes = 0
            seconds = 0
            # Decompose the time parameter into hours,
            minutes and seconds
            if hour_match:
                hours = float(time_param[
                    hour_match.start():hour_match.end()-1])
            if minute_match:
                minutes = float(
                    time_param[minute_match.start():minute_match.end()-1])
            if second_match:
                seconds = float(
                    time_param[second_match.start():second_match.end()-1])
            ctx.delay(minutes=minutes+hours*60, seconds=seconds)
        else:
            raise Exception(
                f"Unrecognized instruction '{instr}' with step_id {step_id}")
    # import pdb; pdb.set_trace()
    ctx.comment("\n\n~~~ Protocol finished ~~~\n")
