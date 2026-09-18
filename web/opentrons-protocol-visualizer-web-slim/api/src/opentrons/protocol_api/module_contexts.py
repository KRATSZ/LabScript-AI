# ruff: noqa: I001
from __future__ import annotations

import logging
from typing import Dict, Iterator, List, Optional, Sequence, Union, cast

from opentrons_shared_data.errors.exceptions import CommandPreconditionViolated
from opentrons_shared_data.labware.types import LabwareDefinition
from opentrons_shared_data.module.types import ModuleModel, ModuleType

from .core.common import (
    AbsorbanceReaderCore,
    FlexStackerCore,
    HeaterShakerCore,
    LabwareCore,
    MagneticBlockCore,
    MagneticModuleCore,
    ModuleCore,
    ProtocolCore,
    TemperatureModuleCore,
    ThermocyclerCore,
    VacuumModuleCore,
)
from .core.core_map import LoadedCoreMap
from .core.engine import ENGINE_CORE_API_VERSION
from .core.legacy.legacy_labware_core import LegacyLabwareCore as LegacyLabwareCore
from .core.legacy.legacy_module_core import LegacyModuleCore
from .core.legacy.module_geometry import ModuleGeometry as LegacyModuleGeometry
from .labware import Labware
from .module_validation_and_errors import (
    validate_heater_shaker_speed,
    validate_heater_shaker_temperature,
)
from opentrons.drivers.thermocycler.driver import BLOCK_VOL_MAX, BLOCK_VOL_MIN
from opentrons.legacy_broker import LegacyBroker
from opentrons.legacy_commands import module_commands as cmds
from opentrons.legacy_commands.publisher import CommandPublisher, publish
from opentrons.protocol_engine.types import ABSMeasureMode
from opentrons.protocols.api_support.types import APIVersion, ThermocyclerStep
from opentrons.protocols.api_support.util import (
    APIVersionError,
    UnsupportedAPIError,
    requires_version,
)

from . import (
    validation,
)  # isort: skip  # noqa: I001  # Imported after other protocol_api imports to avoid circular import
from .tasks import Task  # isort: skip

_MAGNETIC_MODULE_HEIGHT_PARAM_REMOVED_IN = APIVersion(2, 14)


_log = logging.getLogger(__name__)


class ModuleContext(CommandPublisher):
    """A connected module in the protocol.

    *New in version 2.0*
    """

    def __init__(
        self,
        core: ModuleCore,
        protocol_core: ProtocolCore,
        core_map: LoadedCoreMap,
        api_version: APIVersion,
        broker: LegacyBroker,
    ) -> None:
        super().__init__(broker=broker)
        self._core = core
        self._protocol_core = protocol_core
        self._core_map = core_map
        self._api_version = api_version

    @property
    @requires_version(2, 0)
    def api_version(self) -> APIVersion:
        return self._api_version

    @property
    @requires_version(2, 14)
    def model(self) -> ModuleModel:
        """Get the module's model identifier."""
        return cast(ModuleModel, self._core.get_model().value)

    @property
    @requires_version(2, 14)
    def type(self) -> ModuleType:
        """Get the module's general type identifier."""
        return self._get_type()

    def _get_type(self) -> ModuleType:
        return self._core.MODULE_TYPE.value

    @requires_version(2, 0)
    def load_labware_object(self, labware: Labware) -> Labware:
        """
        Specify the presence of a piece of labware on the module.

        Args:
            labware: The labware object. This object should be already
                initialized and its parent should be set to this module's
                geometry. To initialize and load a labware onto the module in
                one step, see `load_labware()`.

        Returns:
            The properly-linked labware object.

        *Deprecated in version 2.14:* Use `load_labware()` or `load_labware_by_definition()`.
        """
        if not isinstance(self._core, LegacyModuleCore):
            raise UnsupportedAPIError(
                api_element="`ModuleContext.load_labware_object`",
                since_version="2.14",
                extra_message="Use `ModuleContext.load_labware` or `load_labware_by_definition` instead.",
            )

        _log.warning(
            "`ModuleContext.load_labware_object` is an internal, deprecated method. Use `ModuleContext.load_labware` or `load_labware_by_definition` instead."
        )

        assert labware.parent == self._core.geometry, (
            "Labware is not configured with this module as its parent"
        )

        return self._core.geometry.add_labware(labware)

    def load_labware(  # noqa: C901
        self,
        name: str,
        label: Optional[str] = None,
        namespace: Optional[str] = None,
        version: Optional[int] = None,
        adapter: Optional[str] = None,
        lid: Optional[str] = None,
        *,
        adapter_namespace: Optional[str] = None,
        adapter_version: Optional[int] = None,
        lid_namespace: Optional[str] = None,
        lid_version: Optional[int] = None,
    ) -> Labware:
        """
        Load a labware onto the module using its load parameters.

        The parameters of this function behave like those of
        [`load_labware()`][opentrons.protocol_api.ProtocolContext.load_labware]
        (which loads labware directly onto the deck). Note that the parameter
        `name` here corresponds to `load_name` on the `ProtocolContext`
        function.

        Returns:
            The initialized and loaded labware object.

        *New in version 2.1:* The `label`, `namespace`, and `version` parameters.

        *New in version 2.26:* The `adapter_namespace`, `adapter_version`,
        `lid_namespace`, and `lid_version` parameters.
        """
        if self._api_version < APIVersion(2, 1) and (
            label is not None or namespace is not None or version != 1
        ):
            _log.warning(
                f"You have specified API {self.api_version}, but you "
                "are trying to utilize new load_labware parameters in 2.1"
            )

        if self._api_version < validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE:
            if adapter_namespace is not None:
                raise APIVersionError(
                    api_element="The `adapter_namespace` parameter",
                    until_version=str(
                        validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE
                    ),
                    current_version=str(self._api_version),
                )
            if adapter_version is not None:
                raise APIVersionError(
                    api_element="The `adapter_version` parameter",
                    until_version=str(
                        validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE
                    ),
                    current_version=str(self._api_version),
                )
            if lid_namespace is not None:
                raise APIVersionError(
                    api_element="The `lid_namespace` parameter",
                    until_version=str(
                        validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE
                    ),
                    current_version=str(self._api_version),
                )
            if lid_version is not None:
                raise APIVersionError(
                    api_element="The `lid_version` parameter",
                    until_version=str(
                        validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE
                    ),
                    current_version=str(self._api_version),
                )

        load_location: Union[ModuleCore, LabwareCore]
        if adapter is not None:
            if self._api_version < APIVersion(2, 15):
                raise APIVersionError(
                    api_element="Loading a labware on an adapter",
                    until_version="2.15",
                    current_version=f"{self._api_version}",
                )

            if (
                self._api_version
                < validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE
            ):
                checked_adapter_namespace = namespace
                checked_adapter_version = None
            else:
                checked_adapter_namespace = adapter_namespace
                checked_adapter_version = adapter_version

            loaded_adapter = self.load_adapter(
                name=adapter,
                namespace=checked_adapter_namespace,
                version=checked_adapter_version,
            )
            load_location = loaded_adapter._core
        else:
            load_location = self._core

        name = validation.ensure_lowercase_name(name)

        # todo(mm, 2024-11-08): This check belongs in opentrons.protocol_api.core.engine.deck_conflict.
        # We're currently doing it here, at the ModuleContext level, for consistency with what
        # ProtocolContext.load_labware() does. (It should also be moved to the deck_conflict module.)
        if self._get_type() == "absorbanceReaderType":
            if cast(AbsorbanceReaderCore, self._core).is_lid_on():
                raise CommandPreconditionViolated(
                    f"Cannot load {name} onto the Absorbance Reader Module when its lid is closed."
                )

        labware_core = self._protocol_core.load_labware(
            load_name=name,
            label=label if label is None else str(label),
            namespace=namespace,
            version=version,
            location=load_location,
        )
        if lid is not None:
            if self._api_version < validation.LID_STACK_VERSION_GATE:
                raise APIVersionError(
                    api_element="Loading a lid on a Labware",
                    until_version="2.23",
                    current_version=f"{self._api_version}",
                )

            if (
                self._api_version
                < validation.NAMESPACE_VERSION_ADAPTER_LID_VERSION_GATE
            ):
                checked_lid_namespace = namespace
                checked_lid_version = None
            else:
                checked_lid_namespace = lid_namespace
                checked_lid_version = lid_version

            self._protocol_core.load_lid(
                load_name=lid,
                location=labware_core,
                namespace=checked_lid_namespace,
                version=checked_lid_version,
            )

        if isinstance(self._core, LegacyModuleCore) and isinstance(
            labware_core, LegacyLabwareCore
        ):
            labware = self._core.add_labware_core(labware_core)
        else:
            labware = Labware(
                core=labware_core,
                api_version=self._api_version,
                protocol_core=self._protocol_core,
                core_map=self._core_map,
            )

        self._core_map.add(labware_core, labware)

        return labware

    @requires_version(2, 0)
    def load_labware_from_definition(
        self, definition: LabwareDefinition, label: Optional[str] = None
    ) -> Labware:
        """Load a labware onto the module using an inline definition.

        Args:
            definition: The labware definition.
            label (str): An optional special name to give the labware. If
                specified, this is the name the labware will appear as in the
                run log and the calibration view in the Opentrons App.

        Returns:
            The initialized and loaded labware object.
        """
        load_params = self._protocol_core.add_labware_definition(definition)

        return self.load_labware(
            name=load_params.load_name,
            namespace=load_params.namespace,
            version=load_params.version,
            label=label,
        )

    @requires_version(2, 1)
    def load_labware_by_name(
        self,
        name: str,
        label: Optional[str] = None,
        namespace: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Labware:
        """
        *Deprecated in version 2.0:*
            Use `load_labware` instead.
        """
        _log.warning("load_labware_by_name is deprecated. Use load_labware instead.")
        return self.load_labware(
            name=name,
            label=label,
            namespace=namespace,
            version=version,
        )

    @requires_version(2, 15)
    def load_adapter(
        self,
        name: str,
        namespace: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Labware:
        """Load an adapter onto the module using its load parameters.

        The parameters of this function behave like those of
        [`load_adapter()`][opentrons.protocol_api.ProtocolContext.load_adapter]
        (which loads adapters directly onto the deck). Note that the parameter
        `name` here corresponds to `load_name` on the `ProtocolContext`
        function.

        Returns:
            The initialized and loaded adapter object.
        """
        labware_core = self._protocol_core.load_adapter(
            load_name=name,
            namespace=namespace,
            version=version,
            location=self._core,
        )

        if isinstance(self._core, LegacyModuleCore) and isinstance(
            labware_core, LegacyLabwareCore
        ):
            adapter = self._core.add_labware_core(labware_core)
        else:
            adapter = Labware(
                core=labware_core,
                api_version=self._api_version,
                protocol_core=self._protocol_core,
                core_map=self._core_map,
            )

        self._core_map.add(labware_core, adapter)

        return adapter

    @requires_version(2, 15)
    def load_adapter_from_definition(self, definition: LabwareDefinition) -> Labware:
        """
        Load an adapter onto the module using an inline definition.

        Args:
            definition: The labware definition.

        Returns:
            The initialized and loaded labware object.
        """
        load_params = self._protocol_core.add_labware_definition(definition)

        return self.load_adapter(
            name=load_params.load_name,
            namespace=load_params.namespace,
            version=load_params.version,
        )

    @property
    @requires_version(2, 0)
    def labware(self) -> Optional[Labware]:
        """The labware (if any) present on this module."""
        labware_core = self._protocol_core.get_labware_on_module(self._core)
        return self._core_map.get(labware_core)

    @property
    @requires_version(2, 14)
    def parent(self) -> str:
        """The name of the slot the module is on.

        On a Flex, this will be like `"D1"`. On an OT-2, this will be like `"1"`.
        See [Deck Slots](../deck-slots.md).
        """
        return self._core.get_deck_slot_id()

    @property
    @requires_version(2, 0)
    def geometry(self) -> LegacyModuleGeometry:
        """The object representing the module as an item on the deck.

        *Deprecated in version 2.14:*
            Use properties of the `ModuleContext` instead,
            like `model` and `type`.
        """
        if isinstance(self._core, LegacyModuleCore):
            return self._core.geometry

        raise UnsupportedAPIError(
            api_element="`ModuleContext.geometry`",
            since_version="2.14",
            extra_message="Use properties of the `ModuleContext` itself.",
        )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        display_name = self._core.get_display_name()
        location = self._core.get_deck_slot().id

        return f"{class_name} at {display_name} on {location} lw {self.labware}"


class TemperatureModuleContext(ModuleContext):
    """
    An object representing a connected Temperature Module.

    It should not be instantiated directly; instead, it should be
    created through [`ProtocolContext.load_module()`][opentrons.protocol_api.ProtocolContext.load_module].

    *New in version 2.0*
    """

    _core: TemperatureModuleCore

    @property
    @requires_version(2, 14)
    def serial_number(self) -> str:
        """Get the module's unique hardware serial number."""
        return self._core.get_serial_number()

    @publish(command=cmds.tempdeck_set_temp)
    @requires_version(2, 0)
    def set_temperature(self, celsius: float) -> None:
        """Set a target temperature and wait until the module reaches the target.

        No other protocol commands will execute while waiting for the temperature.

        Args:
            celsius: A value between 4 and 95, representing the target temperature in °C.
        """
        self._core.set_target_temperature(celsius)
        self._core.wait_for_target_temperature()

    @publish(command=cmds.tempdeck_set_temp)
    @requires_version(2, 3)
    def start_set_temperature(self, celsius: float) -> Task:
        """Sets the Temperature Module's target temperature and returns immediately without waiting for the module to reach the target. Allows the protocol to proceed while the Temperature Module heats.

        *Changed in version 2.27:* Returns a task object that represents
        concurrent heating. Pass the task object to
        [`wait_for_tasks()`][opentrons.protocol_api.ProtocolContext.wait_for_tasks]
        to wait for the module to finish heating.

        In API version 2.26 or below, this function returns `None`.

        Args:
            celsius: A value between 4 and 95, representing the target
                temperature in °C.
        """
        task = self._core.set_target_temperature(celsius)
        if self._api_version >= APIVersion(2, 27):
            return Task(api_version=self._api_version, core=task)
        else:
            return cast(Task, None)

    @publish(command=cmds.tempdeck_await_temp)
    @requires_version(2, 3)
    def await_temperature(self, celsius: float) -> None:
        """Wait until module reaches temperature.

        Args:
            celsius: A value between 4 and 95, representing the target temperature
                in °C.
        """
        self._core.wait_for_target_temperature(celsius)

    @publish(command=cmds.tempdeck_deactivate)
    @requires_version(2, 0)
    def deactivate(self) -> None:
        """Stop heating or cooling, and turn off the fan."""
        self._core.deactivate()

    @property
    @requires_version(2, 0)
    def temperature(self) -> float:
        """The current temperature of the Temperature Module's deck in °C.

        Returns `0` in simulation if no target temperature has been set.
        """
        return self._core.get_current_temperature()

    @property
    @requires_version(2, 0)
    def target(self) -> Optional[float]:
        """The target temperature of the Temperature Module's deck in °C.

        Returns `None` if no target has been set.
        """
        return self._core.get_target_temperature()

    @property
    @requires_version(2, 3)
    def status(self) -> str:
        """One of four possible temperature statuses:

        - `holding at target`: The module has reached its target temperature
          and is actively maintaining that temperature.
        - `cooling`: The module is cooling to a target temperature.
        - `heating`: The module is heating to a target temperature.
        - `idle`: The module has been deactivated.
        """
        return self._core.get_status().value


class MagneticModuleContext(ModuleContext):
    """
    An object representing a connected Magnetic Module.

    It should not be instantiated directly; instead, it should be
    created through [`ProtocolContext.load_module()`][opentrons.protocol_api.ProtocolContext.load_module].

    *New in version 2.0*
    """

    _core: MagneticModuleCore

    @property
    @requires_version(2, 14)
    def serial_number(self) -> str:
        """Get the module's unique hardware serial number."""
        return self._core.get_serial_number()

    @publish(command=cmds.magdeck_calibrate)
    @requires_version(2, 0)
    def calibrate(self) -> None:
        """Calibrate the Magnetic Module.

        *Deprecated in version 2.14:* This method is unnecessary; remove any usage.
        """
        if self._api_version < ENGINE_CORE_API_VERSION:
            _log.warning(
                "`MagneticModuleContext.calibrate` doesn't do anything useful"
                " and will be removed in Protocol API version 2.14 and higher."
            )
            self._core._sync_module_hardware.calibrate()  # type: ignore[attr-defined]
        else:
            raise UnsupportedAPIError(
                api_element="`MagneticModuleContext.calibrate`",
                since_version="2.14",
            )

    @publish(command=cmds.magdeck_engage)
    @requires_version(2, 0)
    def engage(
        self,
        height: Optional[float] = None,
        offset: Optional[float] = None,
        height_from_base: Optional[float] = None,
    ) -> None:
        """
        Raise the Magnetic Module's magnets. You can specify how high the magnets
        should move:

        - No parameter: Move to the default height for the loaded labware. If
          the loaded labware has no default, or if no labware is loaded, this will
          raise an error.

        - `height_from_base`: Move this many millimeters above the bottom
          of the labware. Acceptable values are between `0` and `25`.

            This is the recommended way to adjust the magnets' height.

            *New in version 2.2*

        - `offset`: Move this many millimeters above (positive value) or below
          (negative value) the default height for the loaded labware. The sum of
          the default height and `offset` must be between 0 and 25.

        - `height`: Intended to move this many millimeters above the magnets'
          home position. However, depending on the generation of module and the loaded
          labware, this may produce unpredictable results. You should normally use
          `height_from_base` instead.

            *Removed in version 2.14*

        You shouldn't specify more than one of these parameters. However, if you do,
        their order of precedence is `height`, then `height_from_base`, then `offset`.
        """
        if height is not None:
            if self._api_version >= _MAGNETIC_MODULE_HEIGHT_PARAM_REMOVED_IN:
                raise UnsupportedAPIError(
                    api_element="The height parameter of MagneticModuleContext.engage()",
                    since_version=f"{_MAGNETIC_MODULE_HEIGHT_PARAM_REMOVED_IN}",
                    current_version=f"{self._api_version}",
                    extra_message="Use offset or height_from_base.",
                )
            self._core.engage(height_from_home=height)

        # This version check has a bug:
        # if the caller sets height_from_base in an API version that's too low,
        # we will silently ignore it instead of raising APIVersionError.
        # Leaving this unfixed because we haven't thought through
        # how to do backwards-compatible fixes to our version checking itself.
        elif height_from_base is not None and self._api_version >= APIVersion(2, 2):
            self._core.engage(height_from_base=height_from_base)

        else:
            self._core.engage_to_labware(
                offset=offset or 0,
                preserve_half_mm=self._api_version < APIVersion(2, 3),
            )

    @publish(command=cmds.magdeck_disengage)
    @requires_version(2, 0)
    def disengage(self) -> None:
        """Lower the magnets back into the Magnetic Module."""
        self._core.disengage()

    @property
    @requires_version(2, 0)
    def status(self) -> str:
        """The status of the module, either `engaged` or `disengaged`."""
        return self._core.get_status().value


class ThermocyclerContext(ModuleContext):
    """An object representing a connected Thermocycler Module.

    It should not be instantiated directly; instead, it should be
    created through [`ProtocolContext.load_module()`][opentrons.protocol_api.ProtocolContext.load_module].

    *New in version 2.0*
    """

    _core: ThermocyclerCore

    @property
    @requires_version(2, 14)
    def serial_number(self) -> str:
        """Get the module's unique hardware serial number."""
        return self._core.get_serial_number()

    @publish(command=cmds.thermocycler_open)
    @requires_version(2, 0)
    def open_lid(self) -> str:
        """Open the lid."""
        return self._core.open_lid().value

    @publish(command=cmds.thermocycler_close)
    @requires_version(2, 0)
    def close_lid(self) -> str:
        """Close the lid."""
        return self._core.close_lid().value

    @publish(command=cmds.thermocycler_set_block_temp)
    @requires_version(2, 0)
    def set_block_temperature(
        self,
        temperature: float,
        hold_time_seconds: Optional[float] = None,
        hold_time_minutes: Optional[float] = None,
        ramp_rate: Optional[float] = None,
        block_max_volume: Optional[float] = None,
    ) -> None:
        """
                Set the target temperature for the well block, in °C.

                Args:
                    temperature: A value between 4 and 99, representing the target
                        temperature in °C.
                    hold_time_minutes: The number of minutes to hold, after reaching
                        `temperature`, before proceeding to the next command. If
                        `hold_time_seconds` is also specified, the times are added
                        together.
                    hold_time_seconds: The number of seconds to hold, after reaching
                        `temperature`, before proceeding to the next command. If
                        `hold_time_minutes` is also specified, the times are added
                        together.
                    block_max_volume: The greatest volume of liquid contained in any
                        individual well of the loaded labware, in µL. If not specified,
                        the default is 25 µL.
                    ramp_rate: The rate to heat or cool the Thermocycler Module's block,
                        in °C/second. The acceptable range is 0.01–2 °C/second
                        to cool the block, and 0.01–4.25 °C/second to heat the block. If not specified,
                        the block will heat or cool as quickly as possible to reach the set temperature.

                        *Changed in version 2.27:* In API version
                        2.27 and newer, the API will first attempt to use the liquid tracking in labware, then default to 25 µL if the protocol lacks probed or loaded
                        liquid information.

                                *Changed in version 2.28:* Use the optional `ramp_rate` parameter to control how quickly
        