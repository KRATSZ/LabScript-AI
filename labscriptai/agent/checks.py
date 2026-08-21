"""Authoring checks stuffed into the same edit / simulate_protocol tool result.

Pipeline: SimPass → LogicPass → llmreview (flash). llmreview is NOT LogicPass.
Sim fail → skip LogicPass and reviewer, unless the same error class repeats
``STUCK_REVIEW_STREAK`` times (unstick flash, once per class per turn).
LogicPass ``fail`` → zero reviewer API calls. Missing LogicPass package → skip
review too (cannot distinguish fail vs pass). Caller may set ``skip_review``
(one green flash review per user turn is enough). Stuck-review does not set
that flag.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from labscriptai.agent.llmreview import run_llmreview

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
STUCK_REVIEW_STREAK = 3
_ERROR_CLASS_RE = re.compile(r"\b([A-Z][A-Za-z]+Error)\b")


def looks_like_opentrons_protocol(path: str | Path, source: str) -> bool:
    return str(path).endswith(".py") and "def run(" in source and "protocol_api" in source


def _import_logicpass() -> tuple[Any, Any] | tuple[None, None]:
    """Public copy only: ``labscriptai/benchmark/logicpass``. No ``src/`` bind."""
    try:
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json

        return evaluate_logicpass, load_analyze_json
    except ImportError:
        return None, None


def _protocol_python() -> str:
    env = os.environ.get("LABSCRIPTAI_PROTOCOL_PYTHON")
    if env and Path(env).expanduser().is_file():
        return str(Path(env).expanduser())
    for candidate in (
        _REPO_ROOT / ".venv-protocol" / "bin" / "python",
        _PACKAGE_ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _try_dev_a_analyze(path: Path) -> dict[str, Any] | None:
    """Prefer ``local_simulation.py analyze --json-output``; None → secondary CLI."""
    script = (
        _PACKAGE_ROOT
        / "plugins"
        / "mcp"
        / "opentrons-mcp"
        / "scripts"
        / "local_simulation.py"
    )
    if not script.is_file():
        return None
    try:
        with tempfile.TemporaryDirectory(prefix="labscriptai-helper-analyze-") as tmp:
            out_json = Path(tmp) / "analyze.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "analyze",
                    str(path),
                    "--json-output",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            if out_json.is_file():
                payload = json.loads(out_json.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            # Helper ran but wrote no analyze JSON (e.g. opentrons probe miss) → secondary.
            return None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, UnicodeError):
        return None
    return None


def _sim_ok_from_analyze(payload: Mapping[str, Any]) -> tuple[bool, list[Any]]:
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
    result = payload.get("result")
    if result in {"not-ok", "error", "failed"}:
        return False, list(errors)
    return not errors, list(errors)


def _run_simpass(path: Path) -> dict[str, Any]:
    helper = _try_dev_a_analyze(path)
    if isinstance(helper, dict) and ("ok" in helper or "errors" in helper or "commands" in helper):
        if "ok" in helper and "commands" not in helper and helper.get("ok") is False:
            reason = str(helper.get("reason") or helper.get("error") or "sim_failed")
            if "opentrons" in reason.lower() or "unavailable" in reason.lower():
                return {"ok": False, "reason": "opentrons_unavailable", "detail": reason}
            return {"ok": False, "reason": reason, "errors": helper.get("errors") or []}
        ok, errors = _sim_ok_from_analyze(helper)
        if helper.get("ok") is False:
            ok = False
            errors = list(helper.get("errors") or errors)
        out: dict[str, Any] = {"ok": ok, "analyze": helper}
        if not ok:
            out["errors"] = errors
            out.setdefault("reason", "sim_failed")
        return out

    python = _protocol_python()
    probe = subprocess.run(
        [python, "-c", "import opentrons.cli"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if probe.returncode != 0:
        return {"ok": False, "reason": "opentrons_unavailable"}

    with tempfile.TemporaryDirectory(prefix="labscriptai-analyze-") as tmp:
        out_json = Path(tmp) / "analyze.json"
        completed = subprocess.run(
            [
                python,
                "-m",
                "opentrons.cli",
                "analyze",
                "--json-output",
                str(out_json),
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=180,
        )
        if not out_json.is_file():
            stderr = (completed.stderr or completed.stdout or "").strip()[:800]
            return {
                "ok": False,
                "reason": "sim_failed",
                "errors": [stderr or f"analyze exit {completed.returncode}"],
            }
        payload = json.loads(out_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "sim_failed", "errors": ["analyze JSON was not an object"]}
    ok, errors = _sim_ok_from_analyze(payload)
    result: dict[str, Any] = {"ok": ok, "analyze": payload}
    if not ok:
        result["errors"] = errors
        result["reason"] = "sim_failed"
    return result


def _physical_setup_from_adapter(adapter: Any) -> tuple[Any | None, str | None, str]:
    """Assumed volumes from loadLiquid leaves. No volume → volume_rules=skipped."""
    volumes: dict[str, float] = {}
    for cmd in getattr(adapter, "commands", ()) or ():
        if getattr(cmd, "command_type", None) != "loadLiquid":
            continue
        labware_id = getattr(cmd, "labware_id", None)
        by_well = getattr(cmd, "volume_by_well", None) or {}
        if not labware_id or not isinstance(by_well, dict):
            continue
        for well, vol in by_well.items():
            try:
                volumes[f"{labware_id}:{well}"] = float(vol)
            except (TypeError, ValueError):
                continue
    if not volumes:
        return None, "skipped", "none"
    try:
        from labscriptai.benchmark.logicpass import PhysicalSetup
    except ImportError:
        return None, "skipped", "none"
    return PhysicalSetup(initial_volumes=volumes), None, "assumed"


def _logicpass_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "to_dict"):
        payload = result.to_dict()
    elif isinstance(result, dict):
        payload = dict(result)
    else:
        payload = {
            "outcome": getattr(result, "outcome", "unevaluable"),
            "logic_pass": bool(getattr(result, "logic_pass", False)),
            "issues": getattr(result, "issues", []),
        }
    return {
        "outcome": payload.get("outcome"),
        "logic_pass": bool(payload.get("logic_pass")),
        "issues": payload.get("issues") or [],
        "sim_pass": payload.get("sim_pass"),
        "coverage": payload.get("coverage"),
    }


def _error_item_text(item: Any) -> str:
    if isinstance(item, dict):
        for key in ("detail", "errorMessage", "message", "errorCode", "title"):
            val = item.get(key)
            if val:
                return str(val)[:400]
        return str({k: item[k] for k in list(item)[:4]})[:400]
    return str(item)[:400]


def _short_errors(errors: Any) -> list[str]:
    if not isinstance(errors, list):
        return [_error_item_text(errors)] if errors else []
    return [_error_item_text(item) for item in errors[:5]]


def _public_sim(sim_result: Mapping[str, Any]) -> dict[str, Any]:
    """Author-facing sim: ok/reason/short errors, never the analyze dump."""
    public: dict[str, Any] = {"ok": bool(sim_result.get("ok"))}
    if sim_result.get("reason"):
        public["reason"] = str(sim_result["reason"])[:300]
    errors = sim_result.get("errors")
    if not errors and isinstance(sim_result.get("analyze"), dict):
        errors = sim_result["analyze"].get("errors")
    if errors:
        public["errors"] = _short_errors(errors)
    return public


def sim_error_class(public_sim: Mapping[str, Any]) -> str:
    """Stable class for streaking (ignore line numbers)."""
    blob = " ".join(str(item) for item in (public_sim.get("errors") or [])[:2])
    blob = blob or str(public_sim.get("reason") or "")
    match = _ERROR_CLASS_RE.search(blob)
    if match:
        return match.group(1)
    return blob[:80]


def _sim_error_text(sim_result: Mapping[str, Any]) -> str:
    public = _public_sim(sim_result) if "ok" in sim_result else dict(sim_result)
    bits = [str(public.get("reason") or "sim_failed")]
    bits.extend(str(item) for item in public.get("errors") or [])
    return " | ".join(bits)[:800]


def stuck_llmreview(
    *,
    user_intent: str,
    protocol_source: str,
    sim: Mapping[str, Any],
    review_client: Any | None = None,
) -> dict[str, Any]:
    """Flash unstick on a short sim error. Does not run LogicPass."""
    return run_llmreview(
        user_intent=user_intent,
        protocol_source=protocol_source,
        client=review_client,
        sim_error=_sim_error_text(sim),
    )


def _review(
    *,
    user_intent: str,
    protocol_source: str,
    review_client: Any | None,
    sim_error: str | None = None,
) -> dict[str, Any]:
    return run_llmreview(
        user_intent=user_intent,
        protocol_source=protocol_source,
        client=review_client,
        sim_error=sim_error,
    )


def run_authoring_checks(
    path: str | Path,
    *,
    user_intent: str,
    protocol_source: str,
    review_client: Any | None = None,
    sim: dict[str, Any] | None = None,
    analyze_payload: dict[str, Any] | None = None,
    skip_review: bool = False,
    stuck_review: bool = False,
) -> dict[str, Any]:
    """Return ``{sim, logicpass?, llmreview?}``. LP fail / missing package omit review."""
    path = Path(path)
    if not looks_like_opentrons_protocol(path, protocol_source):
        return {"sim": {"ok": False, "reason": "not_opentrons_protocol"}}

    sim_result = dict(sim) if sim is not None else _run_simpass(path)
    out: dict[str, Any] = {"sim": _public_sim(sim_result)}
    if not sim_result.get("ok"):
        if stuck_review and not skip_review:
            out["llmreview"] = _review(
                user_intent=user_intent,
                protocol_source=protocol_source,
                review_client=review_client,
                sim_error=_sim_error_text(sim_result),
            )
        return out

    evaluate_logicpass, load_analyze_json = _import_logicpass()
    if evaluate_logicpass is None or load_analyze_json is None:
        # Cannot tell fail vs pass — skip review. See module docstring.
        out["logicpass"] = {
            "outcome": "unevaluable",
            "reason": "logicpass_package_missing",
            "logic_pass": False,
        }
        return out

    payload = analyze_payload if analyze_payload is not None else sim_result.get("analyze")
    if not isinstance(payload, dict):
        out["logicpass"] = {
            "outcome": "unevaluable",
            "reason": "missing_analyze_artifact",
            "logic_pass": False,
        }
        # Real missing-analyze is unevaluable ≠ fail → reviewer still runs.
        if not skip_review:
            out["llmreview"] = _review(
                user_intent=user_intent,
                protocol_source=protocol_source,
                review_client=review_client,
            )
        return out

    adapter = load_analyze_json(payload=payload, protocol_path=path)
    setup, volume_rules, setup_basis = _physical_setup_from_adapter(adapter)
    lp_result = evaluate_logicpass(sim_pass=True, adapter=adapter, physical_setup=setup)
    lp_payload = _logicpass_dict(lp_result)
    if setup_basis != "none":
        lp_payload["setup_basis"] = setup_basis
    if volume_rules == "skipped":
        lp_payload["volume_rules"] = "skipped"
    out["logicpass"] = lp_payload

    if lp_payload.get("outcome") == "fail":
        return out

    if not skip_review:
        out["llmreview"] = _review(
            user_intent=user_intent,
            protocol_source=protocol_source,
            review_client=review_client,
        )
    return out
