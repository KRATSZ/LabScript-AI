"""Verified PyLabRobot / Tecan simulation fixes. Requires pylabrobot 0.2.x."""

from __future__ import annotations

import asyncio
import json

import pytest

from backend.pylabrobot_agent import (
    extract_protocol_logic,
    fill_template_with_logic,
    load_golden_template,
    build_pylabrobot_final_result,
)
from backend.pylabrobot_utils import (
    HARDWARE_PROFILES_DIR,
    generate_dynamic_pylabrobot_knowledge,
    parse_hardware_config_str,
    pick_transfer_resource_names,
    run_pylabrobot_simulation,
    setup_simulation_environment,
    validate_protocol_volumes,
)

TECAN_YAML = """
robot_model: tecan_evo
deck_type: tecan_evo
deck_name: tecan_evo_deck
resources:
  tip_rack_200ul_evo:
    type: TipRack_200ul_Tecan
"""

DISPLAY_NAME_YAML = """
robot_model: Tecan Freedom EVO
"""

EDITED_TECAN_YAML = """
robot_model: tecan_evo
resources:
  tip_rack_200ul_evo:
    type: TipRack_200ul_Tecan
    tip_volume: 200
  oops:
    type: banana
"""

SCALAR_OOPS_YAML = """
robot_model: Tecan Freedom EVO
resources:
  tip_rack_200ul_evo:
    type: TipRack_200ul_Tecan
    tip_volume: 200
  microplate_source:
    type: MicroPlate_96_Tecan
  microplate_dest:
    type: MicroPlate_96_Tecan
  oops: banana
"""

OVERFLOW_PROTOCOL = """
async def protocol(lh):
    tips = lh.get_resource("tip_rack_200ul_evo")
    source = lh.get_resource("microplate_source")
    dest = lh.get_resource("microplate_dest")
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(source["A1"], vols=[5000])
    await lh.dispense(dest["A1"], vols=[5000])
    await lh.drop_tips(tips["A1"])
    print("--- PROTOCOL_SUCCESS ---")
"""


MIN_PROTOCOL = """
async def protocol(lh):
    tips = lh.get_resource("tip_rack_200ul_evo")
    source = lh.get_resource("microplate_source")
    dest = lh.get_resource("microplate_dest")
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(source["A1"], vols=[20])
    await lh.dispense(dest["A1"], vols=[20])
    await lh.drop_tips(tips["A1"])
    print("--- PROTOCOL_SUCCESS ---")
"""


def test_yaml_style_tecan_text_loads_tecan_profile() -> None:
    config = parse_hardware_config_str(TECAN_YAML)
    assert config["robot_model"] == "tecan_evo"
    assert "tip_rack_200ul_evo" in config["resources"]
    assert "oops" not in config["resources"]


def test_display_name_yaml_loads_tecan_not_hamilton() -> None:
    config = parse_hardware_config_str(DISPLAY_NAME_YAML)
    assert config["robot_model"] == "tecan_evo"
    assert "tip_rack_200ul_evo" in config["resources"]
    assert config.get("deck_type") != "hamilton_star"


def test_yaml_resource_edits_are_kept() -> None:
    config = parse_hardware_config_str(EDITED_TECAN_YAML)
    assert "oops" in config["resources"]
    assert "microplate_source" not in config["resources"]
    assert config["resources"]["oops"]["type"] == "banana"


def test_scalar_oops_yaml_does_not_break_knowledge() -> None:
    config = parse_hardware_config_str(SCALAR_OOPS_YAML)
    assert config["robot_model"] == "tecan_evo"
    assert isinstance(config["resources"]["oops"], dict)
    assert config["resources"]["oops"]["type"] == "banana"
    assert "tip_rack_200ul_evo" in config["resources"]
    knowledge = generate_dynamic_pylabrobot_knowledge(config)
    assert "oops" in knowledge
    assert "tip_rack_200ul_evo" in knowledge


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
    config = json.loads((HARDWARE_PROFILES_DIR / "pylabrobot_tecan_evo.json").read_text())

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


def test_tecan_knowledge_uses_named_resources() -> None:
    config = json.loads((HARDWARE_PROFILES_DIR / "pylabrobot_tecan_evo.json").read_text())
    knowledge = generate_dynamic_pylabrobot_knowledge(config)
    assert "tip_rack_200ul_evo" in knowledge
    assert 'lh.get_resource("tip_rack_200ul_evo")' in knowledge
    assert "tip_rack_50ul" not in knowledge
    tip, source, dest = pick_transfer_resource_names(config)
    assert tip == "tip_rack_200ul_evo"
    assert source == "microplate_source"
    assert dest == "microplate_dest"


def test_extract_protocol_logic_strips_function_wrapper() -> None:
    raw = '''```python
async def protocol(lh):
    tips = lh.get_resource("tip_rack_200ul_evo")
    await lh.pick_up_tips(tips["A1"])

if __name__ == "__main__":
    pass
```'''
    body = extract_protocol_logic(raw)
    assert "async def protocol" not in body
    assert 'lh.get_resource("tip_rack_200ul_evo")' in body
    assert body.splitlines()[0].startswith("    ")
    filled = fill_template_with_logic(load_golden_template(), body)
    assert filled.count("async def protocol") == 1


def test_final_result_event_uses_status_success() -> None:
    event = build_pylabrobot_final_result({
        "python_code": 'tips = lh.get_resource("tip_rack_200ul_evo")',
        "attempts": 4,
        "final_outcome": "Success",
        "simulation_result": {"success": True, "has_warnings": False},
    })
    assert event["event_type"] == "final_result"
    assert event["status"] == "success"
    assert event["success"] is True
    assert "tip_rack_200ul_evo" in event["generated_code"]


def test_5000ul_transfer_fails_volume_check() -> None:
    config = json.loads((HARDWARE_PROFILES_DIR / "pylabrobot_tecan_evo.json").read_text())
    message = validate_protocol_volumes(OVERFLOW_PROTOCOL, config)
    assert message is not None
    assert "5000" in message

    result = asyncio.run(
        run_pylabrobot_simulation(
            OVERFLOW_PROTOCOL,
            return_structured=True,
            hardware_config=config,
        )
    )
    assert result["success"] is False
    assert "5000" in (result.get("error_details") or "")
