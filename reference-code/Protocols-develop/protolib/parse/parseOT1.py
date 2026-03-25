from inspect import signature, Parameter
import json
import time
import shutil
from opentrons import robot, containers
from opentrons.instruments import Pipette as BasePipette
from opentrons.instruments import Magbead as BaseMagbead
from opentrons.util.environment import settings as opentrons_settings

import sys

# HACK to get pipette type
pipetteType = type(BasePipette(robot, 'a'))

# monkeypatch containers.load with the load_container_spy fn,
# use global all_containers to track containers per protocol
global all_containers
orig_containers_load = containers.load


def load_container_spy(container_name, slot, label=None):
    all_containers.append({
        'type': container_name,
        'slot': slot,
        'name': label or container_name
        })
    return orig_containers_load(container_name, slot, label)


containers.load = load_container_spy


def parse(protocol_path):

    if not protocol_path:
        return {}
    print('Parsing protocol: {}'.format(protocol_path))

    # Calibration data overrides settings sometimes,
    # making protocols interfere with each other and sometimes throw errors.
    # This HACK works around issues with calibration.

    try:
        shutil.rmtree(
            opentrons_settings.get('CALIBRATIONS_DIR', 'calibrations'))
    except FileNotFoundError:
        pass

    # reset is needed to reset tip tracking, other states may also interfere
    robot.reset()

    global all_containers
    # new protocol. start with no containers
    all_containers = []

    orig_time_sleep = time.sleep

    def fake_sleep(*args, **kwargs):
        # equivalent to pre-monkeypatched `time.sleep(0)`
        orig_time_sleep(0)

    def fake_delay(self, *args, **kwargs):
        # allow chaining
        fake_sleep(*args, **kwargs)
        return self

    # time.sleep
    fake_time = time
    fake_time.sleep = fake_sleep

    # monkeypatch fake delay/sleep
    PatchedPipette = BasePipette
    PatchedPipette.delay = fake_delay

    PatchedMagbead = BaseMagbead
    PatchedMagbead.delay = fake_delay

    # do the same opentrons/__init__.py trick to monkeypatch delays
    class InstrumentsWrapper(object):
        def __init__(self, robot):
            self.robot = robot

        def Pipette(self, *args, **kwargs):
            return PatchedPipette(self.robot, *args, **kwargs)

        def Magbead(self, *args, **kwargs):
            return PatchedMagbead(self.robot, *args, **kwargs)

    _globals = {
        'robot': robot,
        'opentrons.containers': containers,
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
        robot, protocol_function, all_containers)


def get_result_dict(robot, protocol_function, all_containers):
    return {
        'instruments': get_instruments(robot),
        'containers': all_containers,
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
        {'name': instr.name,
         'axis': axis.lower(),
         'channels': getattr(instr, 'channels', None),
         'type': instr.__class__.__name__.lower(),
         'min_volume': getattr(instr, 'min_volume', None),
         'max_volume': getattr(instr, 'max_volume', None)
         }
        for axis, instr in robot.get_instruments()
    ]


if __name__ == '__main__':
    sourceFilePath = sys.argv[1]
    destFilePath = sys.argv[2]
    print('OT1: parsing {} to {}'.format(sourceFilePath, destFilePath))

    result = parse(sourceFilePath)
    with open(destFilePath, 'w') as f:
        json.dump(result, f)
