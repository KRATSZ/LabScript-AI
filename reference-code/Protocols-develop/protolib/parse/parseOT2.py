import json
from inspect import signature, Parameter
import time
import sys
from opentrons import robot, labware, modules
from opentrons.legacy_api.instruments import Pipette as BasePipette

all_labware = []
all_modules = []
orig_labware_load = labware.load
orig_module_load = modules.load


# labware.load spy
def load_labware_spy(labware_name, slot, label=None, share=False):
    # module.load() calls labware.load() to get the "labware" for the modules
    # so we have to filter out modules from this labware spy somehow...
    if labware_name not in modules.SUPPORTED_MODULES:
        all_labware.append({
            'type': labware_name,
            'slot': slot,
            'name': label or labware_name,
            'share': share
            })
    return orig_labware_load(labware_name, slot, label, share)


# modules.load spy
def load_module_spy(module_name, slot):
    all_modules.append({
        'name': module_name,
        'slot': slot})
    return orig_module_load(module_name, slot)


# monkeypatch the spies in
labware.load = load_labware_spy
modules.load = load_module_spy
# TODO: Ian 2018-09-13 avoid these spies altogether once there's a solid way
# to get labware and modules (eg after major Session refactor)


def parse(protocol_path):

    if not protocol_path:
        return {}
    print('Parsing protocol: {}'.format(protocol_path))

    # reset is needed to reset tip tracking, other states may also interfere
    robot.reset()

    global all_labware
    global all_modules
    # new protocol. start with no containers
    all_labware = []
    all_modules = []
    orig_time_sleep = time.sleep

    def fake_sleep(*args, **kwargs):
        # equivalent to pre-monkeypatched `time.sleep(0)`
        orig_time_sleep(0)

    def fake_delay(self, *args, **kwargs):
        # allow chaining
        fake_sleep(*args, **kwargs)
        return self

    # monkeypatch fake delay/sleep
    # time.sleep
    fake_time = time
    fake_time.sleep = fake_sleep

    PatchedPipette = BasePipette
    PatchedPipette.delay = fake_delay

    # do the same opentrons/__init__.py trick to monkeypatch delays
    class InstrumentsWrapper(object):
        def __init__(self, robot):
            self.robot = robot

        # Use old pipette constructor to create the monkeypatch
        # Will need to be updated once instrument wrapper is changed
        def Pipette(self, *args, **kwargs):
            return PatchedPipette(self.robot, *args, **kwargs)

    _globals = {
        'robot': robot,
        'opentrons.instruments': InstrumentsWrapper(robot),
        'time': fake_time
    }

    with open(protocol_path) as f:
        protocol_text = f.read()

    exec(
        compile(protocol_text, protocol_path, 'exec'),
        _globals
    )

    # Mini-parametric protocols have `def run_custom_protocol(...)` fn
    # in global scope
    protocol_function = _globals.get('run_custom_protocol')

    if protocol_function is not None:
        # call it with default args,
        # in case there are any container.load commands.
        # The default args will thus determine what the deck map looks like.
        protocol_function()

    return get_result_dict(
        robot, protocol_function, all_labware, all_modules)


def get_result_dict(robot, protocol_function, all_labware, all_modules):
    return {
        'instruments': get_instruments(robot),
        'labware': all_labware,
        'modules': all_modules,
        'parameters': get_parameters(protocol_function)
        if protocol_function else []
    }


def get_parameters(protocol_function):
    """
    Inspect the run_custom_protocol fn arg annotations to determine
    what customizable fields should be
    """
    def get_annotation(annotation):
        try:
            # For normal annotations like float and int:
            name = annotation.__name__
            return {'type': name}
        except AttributeError:
            # annotation must implement get_json interface:
            return annotation.get_json()

    return [
        {
         'name': param.name,
         'annotation': get_annotation(param.annotation)
         if param.annotation != Parameter.empty else None,
         'default': param.default
         }
        for param in signature(protocol_function).parameters.values()
    ]


def get_instruments(robot):
    return [
        {
         'name': instr.name,
         'mount': axis.lower()
         }
        for axis, instr in robot.get_instruments()
    ]


if __name__ == '__main__':
    sourceFilePath = sys.argv[1]
    destFilePath = sys.argv[2]
    print('OT2: parsing {} to {}'.format(sourceFilePath, destFilePath))

    result = parse(sourceFilePath)
    with open(destFilePath, 'w') as f:
        json.dump(result, f)
