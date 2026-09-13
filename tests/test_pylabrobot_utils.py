"""Verified PyLabRobot / Tecan simulation fixes. Requires pylabrobot 0.2.x."""

from __future__ import annotations

import asyncio
import json

import pytest

from backend.pylabrobot_utils import (
    HARDWARE_PROFILES_DIR,
    parse_hardware_config_str,
    run_pylabrobot_simulation,
    setup_simulation_environment,
)

TECAN_YAML = """
robot_model: tecan_evo
deck_type: tecan_evo
deck_name: tecan_evo_deck
resources:
  tip_rack_200ul_evo:
    type: TipRack_200ul_Tecan
"""

MIN_PROTOCOL = """
async def protocol(lh):
    tips = lh.get_resource("tip_rack_200ul_evo")
    source = lh.get_resource("microplate_source")
    dest = lh.get_resource("microplate_dest")
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(source["A1"], vols=[20])
    await lh.dispense(dest["A1"], vols=[20])
    await lh.drop_tips()
    print("--- PROTOCOL_SUCCESS ---")
"""


def test_yaml_style_tecan_text_loads_tecan_profile() -> None:
    config = parse_hardware_config_str(TECAN_YAML)
    assert config["robot_model"] == "tecan_evo"
    assert "tip_rack_200ul_evo" in config["resources"]
    assert "microplate_source" in config["resources"]


def test_json_hardware_config_is_kept() -> None:
    raw = json.dumps({"robot_model": "tecan_evo", "resources": {"only": {"type": "plate"}}})
    config = parse_hardware_config_str(raw)
    assert config["resources"]["only"]["type"] == "plate"


def test_tecan_profile_file_exists() -> None:
    assert (HARDWARE_PROFILES_DIR / "pylabrobot_tecan_evo.json").is_file()


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pylabrobot") is None,
    reason="pylabrobot not installed",
)
def test_tecan_setup_places_named_resources() -> None:
    config = parse_hardware_config_str(TECAN_YAML)

    async def _run():
        lh = await setup_simulation_environment(config)
        try:
            tips = lh.get_resource("tip_rack_200ul_evo")
            plate = lh.get_resource("microplate_source")
            assert tips["A1"] is not None
            assert plate["A1"] is not None
        finally:
            await lh.stop()

    asyncio.run(_run())


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pylabrobot") is None,
    reason="pylabrobot not installed",
)
def test_tecan_min_protocol_simulates() -> None:
    config = json.loads((HARDWARE_PROFILES_DIR / "pylabrobot_tecan_evo.json").read_text())

    async def _run():
        return await run_pylabrobot_simulation(
            MIN_PROTOCOL,
            return_structured=True,
            hardware_config=config,
        )

    result = asyncio.run(_run())
    assert result["success"] is True, result


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pylabrobot") is None,
    reason="pylabrobot not installed",
)
def test_template_constructs_liquid_handler() -> None:
    from pylabrobot.liquid_handling import LiquidHandler
    from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
    from pylabrobot.resources import Deck

    deck = Deck(name="sim_deck", size_x=600, size_y=400, size_z=120)
    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=deck)
    assert lh.deck.name == "sim_deck"


def test_chatterbox_backend_is_deprecated() -> None:
    from pylabrobot.liquid_handling.backends import ChatterBoxBackend

    with pytest.raises(NotImplementedError):
        ChatterBoxBackend()
