"""LogicPass public-package tests (no LLM, no robot, no DEEPSEEK)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from labscriptai.benchmark.logicpass import (
    PhysicalSetup,
    assumed_physical_setup_from_protocol,
    evaluate_logicpass,
    load_analyze_json,
)
from labscriptai.benchmark.logicpass.types import (
    MIX_STATE_HOLDING_COMMANDS,
    PARENT_OR_COMPOUND_COMMANDS,
    STATE_HOLDING_ZERO_TRANSFER_COMMANDS,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "logicpass"
HELPER = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "mcp"
    / "opentrons-mcp"
    / "scripts"
    / "local_simulation.py"
)


def _issue_codes(result) -> list[str]:
    return [issue.code for issue in result.issues]


def test_public_import_path() -> None:
    import inspect

    import labscriptai.benchmark.logicpass as logicpass_mod
    from labscriptai.benchmark.logicpass import evaluate_logicpass as ev
    from labscriptai.benchmark.logicpass import load_analyze_json as load

    resolved = Path(inspect.getfile(logicpass_mod)).resolve()
    text = str(resolved)
    assert "labscriptai/benchmark/logicpass" in text
    assert "/src/" not in text
    assert callable(ev)
    assert callable(load)


def test_dry_well_aspirate_fails() -> None:
    adapter = load_analyze_json(FIXTURES / "dry_well_aspirate.json")
    result = evaluate_logicpass(sim_pass=True, adapter=adapter)
    assert adapter.unevaluable is False
    assert result.outcome == "fail"
    assert result.logic_pass is False
    assert "LP-L1" in _issue_codes(result)


def test_clean_transfer_with_known_volumes_passes() -> None:
    adapter = load_analyze_json(FIXTURES / "static_transfer_min.json")
    result = evaluate_logicpass(sim_pass=True, adapter=adapter)
    assert adapter.unevaluable is False
    assert result.outcome == "pass"
    assert result.logic_pass is True
    assert result.final_pass_v2 is True


def test_mix_pe_expanded_not_unevaluable_because_mix() -> None:
    """PE 8.8.1 expands pipette.mix(reps=2, vol=20) to aspirate/dispense pairs.

    Observed analyze JSON: no ``mix`` parent. Sequence is
    aspirate 20 → dispense 20 (pushOut=0) → aspirate 20 → dispense 20.
    Outcome may pass or fail other rules; it must not be LP-L5 solely for mix.

    Tip-dirty limitation: a leftover ``mix`` *parent* is admitted as
    ``state_holding_zero_transfer`` like blowout and is not consumed by the
    ledger, so the parent does not mark the tip dirty. Expanded aspirate
    children still follow dirty_source L3 rules. Mix is liquid-contact, not
    touchTip.
    """

    adapter = load_analyze_json(FIXTURES / "mix_pe_expanded.json")
    result = evaluate_logicpass(sim_pass=True, adapter=adapter)
    types = [d.command_type for d in adapter.dispositions]
    assert "mix" not in types
    assert types.count("aspirate") == 2
    assert types.count("dispense") == 2
    assert adapter.unevaluable is False
    assert result.outcome != "unevaluable"
    assert "LP-L5" not in _issue_codes(result)
    assert result.outcome == "pass"


def test_mix_parent_does_not_nuke_whole_exam() -> None:
    """A leftover mix commandType is blowout-family, not compound/transfer."""

    assert "mix" not in PARENT_OR_COMPOUND_COMMANDS
    assert "mix" in MIX_STATE_HOLDING_COMMANDS
    assert "mix" in STATE_HOLDING_ZERO_TRANSFER_COMMANDS
    assert "transfer" in PARENT_OR_COMPOUND_COMMANDS

    adapter = load_analyze_json(FIXTURES / "mix_parent_with_transfer.json")
    result = evaluate_logicpass(sim_pass=True, adapter=adapter)
    mix = next(d for d in adapter.dispositions if d.command_type == "mix")
    assert mix.kind == "explicitly_allowlisted_non_state"
    assert mix.reason == "state_holding_zero_transfer"
    assert adapter.unevaluable is False
    assert result.outcome != "unevaluable"
    assert result.outcome == "pass"
    assert "LP-L5" not in _issue_codes(result)


def test_transfer_still_unevaluable() -> None:
    adapter = load_analyze_json(
        payload={
            "commands": [
                {
                    "id": "cmd-transfer",
                    "commandType": "transfer",
                    "status": "succeeded",
                    "params": {"pipetteId": "pipette-left"},
                }
            ]
        }
    )
    result = evaluate_logicpass(sim_pass=True, adapter=adapter)
    assert adapter.unevaluable is True
    assert result.outcome == "unevaluable"
    assert "LP-L5" in _issue_codes(result)
    assert adapter.dispositions[0].reason == "ambiguous_hierarchy_or_compound"


def test_missing_analyze_unevaluable() -> None:
    missing = evaluate_logicpass(sim_pass=True, missing_analyze=True)
    assert missing.outcome == "unevaluable"
    assert missing.logic_pass is False
    assert "LP-L5" in _issue_codes(missing)

    adapter = load_analyze_json(None)
    assert adapter.unevaluable is True
    assert "missing_analyze_artifact" in adapter.lp_l5_reasons
    loaded = evaluate_logicpass(sim_pass=True, adapter=adapter)
    assert loaded.outcome == "unevaluable"


def test_assumed_physical_setup_from_protocol_skips_missing_volume() -> None:
    source = """
from opentrons import protocol_api

def run(protocol):
    reservoir = protocol.load_labware("nest_1_reservoir_195ml", "D2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "C1")
    water = protocol.define_liquid("water", "", "#0000FF")
    reservoir["A1"].load_liquid(liquid=water, volume=3000)
    plate["B1"].load_liquid(liquid=water)
"""
    setup, meta = assumed_physical_setup_from_protocol(source)
    assert isinstance(setup, PhysicalSetup)
    assert setup.setup_basis == "assumed"
    assert setup.initial_volumes.get("reservoir:A1") == 3000.0
    assert "plate:B1" not in setup.initial_volumes
    assert "plate:B1" in meta["skipped_no_volume"]
    assert meta["setup_basis"] == "assumed"


def test_analyze_subcommand_writes_json_output_flag() -> None:
    spec = importlib.util.spec_from_file_location("local_simulation_helper", HELPER)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    parser = helper.build_parser()
    args = parser.parse_args(
        ["analyze", "protocol.py", "--json-output", "/tmp/analyze.json"]
    )
    assert args.command == "analyze"
    assert args.json_output == "/tmp/analyze.json"
    with pytest.raises(SystemExit):
        parser.parse_args(["analyze", "protocol.py"])
