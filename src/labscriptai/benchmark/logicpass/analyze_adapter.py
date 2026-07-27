"""Analyze-JSON adapter for LogicPass Phase 1.

Loads Opentrons Protocol Engine ``analyze --json-output`` payloads and
normalizes them into a typed consumed-leaf stream for the ledger.

Exhaustive disposition (locked Phase 0)::

    consumed_supported_atomic_leaf
        | explicitly_allowlisted_non_state
        | lp_l5

Unknown / unsupported / incomplete / ambiguous → ``LP-L5`` (unevaluable).
No silent ignore; no text/AST fallback for comparable LogicPass.

Shared types live in :mod:`labscriptai.benchmark.logicpass.types`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

from labscriptai.benchmark.logicpass.types import (
    ADAPTER_SCHEMA_VERSION,
    ALLOWLISTED_NON_STATE_COMMANDS,
    BLOWOUT_STATE_HOLDING_COMMANDS,
    LEGACY_CUSTOM_STATE_HOLDING_TYPES,
    OT_VERSION_PROBE_BASELINE,
    PARENT_OR_COMPOUND_COMMANDS,
    SUPPORTED_LEAF_COMMANDS,
    UNSUPPORTED_LIQUID_AFFECTING_EXAMPLES,
    AnalyzeAdapterResult,
    AnalyzeProvenance,
    CommandDisposition,
    NormalizedLeafCommand,
    SupportedLeafCommandType,
)

__all__ = [
    "ADAPTER_SCHEMA_VERSION",
    "OT_VERSION_PROBE_BASELINE",
    "load_analyze_json",
    "sha256_file",
]


def sha256_file(path: Path) -> str:
    """Return hex SHA-256 of a file's bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    return None


def _as_str(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _as_finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number != number:  # NaN
            return None
        return number
    return None


def _package_sha256(package_path: Path | None) -> str | None:
    """``null`` iff no package *file* artifact supplied.

    Directory presence alone does not select the string branch
    (``predicates_disjoint`` freeze).
    """
    if package_path is None:
        return None
    if not package_path.is_file():
        return None
    return sha256_file(package_path)


def _protocol_sha256(protocol_path: Path | None) -> str | None:
    if protocol_path is None:
        return None
    if not protocol_path.is_file():
        return None
    return sha256_file(protocol_path)


def _extract_api_level(payload: Mapping[str, Any]) -> str | None:
    config = _as_mapping(payload.get("config"))
    if config is not None:
        level = config.get("apiLevel") or config.get("api_level")
        if level is not None:
            return str(level)
    metadata = _as_mapping(payload.get("metadata"))
    if metadata is not None:
        level = metadata.get("apiLevel") or metadata.get("api_level")
        if level is not None:
            return str(level)
    return None


def _extract_parameter_values(
    payload: Mapping[str, Any],
    override: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if override is not None:
        return dict(override)
    for key in ("runTimeParameters", "runtime_parameters", "parameterValues", "parameters"):
        raw = payload.get(key)
        if isinstance(raw, Mapping):
            return dict(raw)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            collected: dict[str, Any] = {}
            for item in raw:
                item_map = _as_mapping(item)
                if item_map is None:
                    continue
                name = item_map.get("variableName") or item_map.get("name") or item_map.get("displayName")
                if name is None:
                    continue
                if "value" in item_map:
                    collected[str(name)] = item_map.get("value")
                elif "default" in item_map:
                    collected[str(name)] = item_map.get("default")
            if collected:
                return collected
    return {}


def _status_summary(raw_commands: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for command in raw_commands:
        status = command.get("status")
        key = str(status) if status is not None else "missing"
        summary[key] = summary.get(key, 0) + 1
    return summary


def _is_multichannel_params(params: Mapping[str, Any]) -> bool:
    """Fail-closed heuristics for unsupported multichannel mapping."""
    nozzles = params.get("nozzles")
    if isinstance(nozzles, str) and nozzles.upper() not in {"", "SINGLE", "PRIMARY"}:
        # ALL / COLUMN / ROW / etc. imply multi-nozzle layouts in PE.
        if nozzles.upper() != "ALL":
            return True
        # ALL on an 8-channel pipette is multichannel; Phase 1 rejects.
        return True
    if params.get("nozzleLayout") is not None or params.get("nozzle_layout") is not None:
        return True
    well_names = params.get("wellNames") or params.get("wells")
    if isinstance(well_names, (list, tuple)) and len(well_names) > 1:
        return True
    return False


def _normalize_volume_by_well(raw: Any) -> Mapping[str, float] | None:
    mapping = _as_mapping(raw)
    if mapping is None:
        return None
    out: dict[str, float] = {}
    for well, volume in mapping.items():
        number = _as_finite_number(volume)
        if number is None:
            return None
        out[str(well)] = number
    return out


def _normalize_leaf(
    *,
    index: int,
    command_id: str,
    command_type: SupportedLeafCommandType,
    status: str,
    params: Mapping[str, Any],
    result: Mapping[str, Any] | None,
) -> tuple[NormalizedLeafCommand | None, str | None]:
    if _is_multichannel_params(params):
        return None, "unsupported_multichannel"

    pipette_id = _as_str(params.get("pipetteId") or params.get("pipette_id"))
    labware_id = _as_str(params.get("labwareId") or params.get("labware_id"))
    well_name = _as_str(params.get("wellName") or params.get("well_name"))
    liquid_id = _as_str(params.get("liquidId") or params.get("liquid_id"))
    volume_ul = _as_finite_number(params.get("volume"))
    volume_by_well: Mapping[str, float] | None = None

    if command_type in {"aspirate", "dispense"}:
        if pipette_id is None or labware_id is None or well_name is None:
            return None, "unresolved_ids"
        if volume_ul is None:
            return None, "nonnumeric_volume"
    elif command_type == "loadLiquid":
        if liquid_id is None or labware_id is None:
            return None, "unresolved_ids"
        volume_by_well = _normalize_volume_by_well(params.get("volumeByWell") or params.get("volume_by_well"))
        if volume_by_well is None:
            return None, "nonnumeric_volume"
    elif command_type == "pickUpTip":
        if pipette_id is None or labware_id is None or well_name is None:
            return None, "unresolved_ids"
    elif command_type in {"dropTip", "dropTipInPlace"}:
        if pipette_id is None:
            return None, "unresolved_ids"
    else:
        return None, "unknown_commandType"

    return (
        NormalizedLeafCommand(
            step_index=index,
            command_id=command_id,
            command_type=command_type,
            status=status,
            params=dict(params),
            result=dict(result) if result is not None else None,
            pipette_id=pipette_id,
            labware_id=labware_id,
            well_name=well_name,
            volume_ul=volume_ul,
            liquid_id=liquid_id,
            volume_by_well=dict(volume_by_well) if volume_by_well is not None else None,
            tip_labware_id=labware_id if command_type == "pickUpTip" else None,
            tip_well_name=well_name if command_type == "pickUpTip" else None,
        ),
        None,
    )


def _dispose_command(
    command: Mapping[str, Any],
    *,
    index: int,
    seen_ids: MutableMapping[str, int],
) -> tuple[CommandDisposition, NormalizedLeafCommand | None]:
    command_id = _as_str(command.get("id"))
    command_type = command.get("commandType")
    if command_type is not None and not isinstance(command_type, str):
        command_type = str(command_type)
    status = command.get("status")
    params = _as_mapping(command.get("params")) or {}
    result = _as_mapping(command.get("result"))

    def _lp_l5(reason: str) -> tuple[CommandDisposition, None]:
        return (
            CommandDisposition(
                index=index,
                command_id=command_id,
                command_type=command_type if isinstance(command_type, str) else None,
                kind="lp_l5",
                reason=reason,
            ),
            None,
        )

    if command_id is not None:
        if command_id in seen_ids:
            return _lp_l5("duplicate_command_id")
        seen_ids[command_id] = index

    if not isinstance(command_type, str) or not command_type:
        return _lp_l5("missing_commandType")

    if command_type in PARENT_OR_COMPOUND_COMMANDS:
        return _lp_l5("ambiguous_hierarchy_or_compound")

    if command_type in SUPPORTED_LEAF_COMMANDS:
        if status is None:
            return _lp_l5("missing_status")
        if status != "succeeded":
            return _lp_l5("status_not_succeeded")
        if command_id is None:
            return _lp_l5("missing_command_id")
        leaf, reason = _normalize_leaf(
            index=index,
            command_id=command_id,
            command_type=command_type,  # type: ignore[arg-type]
            status=str(status),
            params=params,
            result=result,
        )
        if leaf is None:
            return _lp_l5(reason or "unresolved_ids")
        return (
            CommandDisposition(
                index=index,
                command_id=command_id,
                command_type=command_type,
                kind="consumed_supported_atomic_leaf",
                reason=None,
            ),
            leaf,
        )

    if command_type in ALLOWLISTED_NON_STATE_COMMANDS:
        # Frozen incomplete-status policy: missing / non-success status is
        # LP-L5 for allowlisted commands as well as supported leaves.
        if status is None:
            return _lp_l5("missing_status")
        if status != "succeeded":
            return _lp_l5("status_not_succeeded")
        return (
            CommandDisposition(
                index=index,
                command_id=command_id,
                command_type=command_type,
                kind="explicitly_allowlisted_non_state",
                reason=None,
            ),
            None,
        )

    if command_type in BLOWOUT_STATE_HOLDING_COMMANDS:
        # P0 policy: record blowout, but model it as zero transferred volume.
        # This preserves the surrounding leaf stream for L1-L4 while making
        # the approximation explicit in the disposition evidence.
        if status is None:
            return _lp_l5("missing_status")
        if status != "succeeded":
            return _lp_l5("status_not_succeeded")
        return (
            CommandDisposition(
                index=index,
                command_id=command_id,
                command_type=command_type,
                kind="explicitly_allowlisted_non_state",
                reason="state_holding_zero_transfer",
            ),
            None,
        )

    if command_type == "custom" and params.get(
        "legacyCommandType"
    ) in LEGACY_CUSTOM_STATE_HOLDING_TYPES:
        # Older API protocols emit delay/touch-tip as custom wrappers. Admit
        # only these explicit legacy types; every other custom command remains
        # LP-L5 because its liquid effect is unknown.
        if status is None:
            return _lp_l5("missing_status")
        if status != "succeeded":
            return _lp_l5("status_not_succeeded")
        return (
            CommandDisposition(
                index=index,
                command_id=command_id,
                command_type=command_type,
                kind="explicitly_allowlisted_non_state",
                reason=f"legacy_state_holding:{params['legacyCommandType']}",
            ),
            None,
        )

    if command_type in UNSUPPORTED_LIQUID_AFFECTING_EXAMPLES:
        return _lp_l5("unsupported_liquid_affecting")

    return _lp_l5("unknown_commandType")


def _unevaluable_result(
    *,
    reason: str,
    analyze_source_path: str | None,
    protocol_sha256: str | None,
    package_sha256: str | None,
    ot_version: str | None,
    api_level: str | None,
    parameter_values: Mapping[str, Any],
    command_count: int,
    command_status_summary: Mapping[str, int] | None = None,
    analyze_wall_time: float | None = None,
    liquids: tuple[Mapping[str, Any], ...] = (),
    labware: tuple[Mapping[str, Any], ...] = (),
    pipettes: tuple[Mapping[str, Any], ...] = (),
    raw_commands: tuple[Mapping[str, Any], ...] = (),
    dispositions: tuple[CommandDisposition, ...] = (),
) -> AnalyzeAdapterResult:
    if not dispositions:
        dispositions = (
            CommandDisposition(
                index=-1,
                command_id=None,
                command_type=None,
                kind="lp_l5",
                reason=reason,
            ),
        )
    reasons = tuple(
        d.reason for d in dispositions if d.kind == "lp_l5" and d.reason
    ) or (reason,)
    return AnalyzeAdapterResult(
        unevaluable=True,
        commands=(),
        dispositions=dispositions,
        provenance=AnalyzeProvenance(
            protocol_sha256=protocol_sha256,
            package_sha256=package_sha256,
            ot_version=ot_version,
            api_level=api_level,
            parameter_values=dict(parameter_values),
            adapter_schema_version=ADAPTER_SCHEMA_VERSION,
            command_status_summary=dict(command_status_summary or {}),
            analyze_source_path=analyze_source_path,
            command_count=command_count,
            analyze_wall_time=analyze_wall_time,
        ),
        lp_l5_reasons=reasons,
        liquids=liquids,
        labware=labware,
        pipettes=pipettes,
        raw_commands=raw_commands,
        error_code="LP-L5",
    )


def load_analyze_json(
    path: str | Path | None = None,
    *,
    payload: Mapping[str, Any] | None = None,
    protocol_path: str | Path | None = None,
    package_path: str | Path | None = None,
    ot_version: str | None = None,
    parameter_values: Mapping[str, Any] | None = None,
    analyze_wall_time: float | None = None,
) -> AnalyzeAdapterResult:
    """Load and normalize an analyze ``--json-output`` payload.

    Parameters
    ----------
    path:
        Path to analyze JSON. Required unless ``payload`` is supplied.
    payload:
        In-memory analyze dict (tests / callers that already parsed JSON).
    protocol_path:
        Optional protocol file used for ``protocol_sha256``.
    package_path:
        Optional *file* artifact for ``package_sha256``. ``None`` or a
        directory → ``package_sha256=null``.
    ot_version:
        Runtime OT version override; defaults to probe baseline when unknown.
    parameter_values:
        Evaluator-supplied parameter map override for provenance.
    analyze_wall_time:
        Optional wall-clock seconds for the analyze invocation.
    """
    analyze_path = Path(path) if path is not None else None
    protocol = Path(protocol_path) if protocol_path is not None else None
    package = Path(package_path) if package_path is not None else None

    protocol_digest = _protocol_sha256(protocol)
    package_digest = _package_sha256(package)
    source_path = str(analyze_path.resolve()) if analyze_path is not None else None
    resolved_ot = ot_version or OT_VERSION_PROBE_BASELINE

    if payload is None:
        if analyze_path is None:
            return _unevaluable_result(
                reason="missing_analyze_artifact",
                analyze_source_path=None,
                protocol_sha256=protocol_digest,
                package_sha256=package_digest,
                ot_version=resolved_ot,
                api_level=None,
                parameter_values=dict(parameter_values or {}),
                command_count=0,
                analyze_wall_time=analyze_wall_time,
            )
        if not analyze_path.is_file():
            return _unevaluable_result(
                reason="missing_analyze_artifact",
                analyze_source_path=source_path,
                protocol_sha256=protocol_digest,
                package_sha256=package_digest,
                ot_version=resolved_ot,
                api_level=None,
                parameter_values=dict(parameter_values or {}),
                command_count=0,
                analyze_wall_time=analyze_wall_time,
            )
        try:
            loaded = json.loads(analyze_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return _unevaluable_result(
                reason="invalid_analyze_json",
                analyze_source_path=source_path,
                protocol_sha256=protocol_digest,
                package_sha256=package_digest,
                ot_version=resolved_ot,
                api_level=None,
                parameter_values=dict(parameter_values or {}),
                command_count=0,
                analyze_wall_time=analyze_wall_time,
            )
        if not isinstance(loaded, Mapping):
            return _unevaluable_result(
                reason="invalid_analyze_json",
                analyze_source_path=source_path,
                protocol_sha256=protocol_digest,
                package_sha256=package_digest,
                ot_version=resolved_ot,
                api_level=None,
                parameter_values=dict(parameter_values or {}),
                command_count=0,
                analyze_wall_time=analyze_wall_time,
            )
        payload = loaded

    commands_raw = payload.get("commands")
    if not isinstance(commands_raw, list):
        return _unevaluable_result(
            reason="missing_commands",
            analyze_source_path=source_path,
            protocol_sha256=protocol_digest,
            package_sha256=package_digest,
            ot_version=resolved_ot,
            api_level=_extract_api_level(payload),
            parameter_values=_extract_parameter_values(payload, parameter_values),
            command_count=0,
            analyze_wall_time=analyze_wall_time,
        )

    raw_commands: list[Mapping[str, Any]] = []
    for item in commands_raw:
        item_map = _as_mapping(item)
        if item_map is None:
            return _unevaluable_result(
                reason="malformed_command_entry",
                analyze_source_path=source_path,
                protocol_sha256=protocol_digest,
                package_sha256=package_digest,
                ot_version=resolved_ot,
                api_level=_extract_api_level(payload),
                parameter_values=_extract_parameter_values(payload, parameter_values),
                command_count=len(commands_raw),
                analyze_wall_time=analyze_wall_time,
            )
        raw_commands.append(item_map)

    dispositions: list[CommandDisposition] = []
    leaves: list[NormalizedLeafCommand] = []
    seen_ids: dict[str, int] = {}
    for index, command in enumerate(raw_commands):
        disposition, leaf = _dispose_command(command, index=index, seen_ids=seen_ids)
        dispositions.append(disposition)
        if leaf is not None:
            leaves.append(leaf)

    liquids_raw = payload.get("liquids") if isinstance(payload.get("liquids"), list) else []
    labware_raw = payload.get("labware") if isinstance(payload.get("labware"), list) else []
    pipettes_raw = payload.get("pipettes") if isinstance(payload.get("pipettes"), list) else []

    liquids = tuple(dict(x) for x in liquids_raw if isinstance(x, Mapping))
    labware = tuple(dict(x) for x in labware_raw if isinstance(x, Mapping))
    pipettes = tuple(dict(x) for x in pipettes_raw if isinstance(x, Mapping))

    api_level = _extract_api_level(payload)
    params = _extract_parameter_values(payload, parameter_values)
    summary = _status_summary(raw_commands)
    provenance = AnalyzeProvenance(
        protocol_sha256=protocol_digest,
        package_sha256=package_digest,
        ot_version=resolved_ot,
        api_level=api_level,
        parameter_values=params,
        adapter_schema_version=ADAPTER_SCHEMA_VERSION,
        command_status_summary=summary,
        analyze_source_path=source_path,
        command_count=len(raw_commands),
        analyze_wall_time=analyze_wall_time,
    )

    lp_reasons = tuple(d.reason for d in dispositions if d.kind == "lp_l5" and d.reason)
    unevaluable = any(d.kind == "lp_l5" for d in dispositions)
    # Fail closed: every command must have exactly one disposition (guaranteed
    # by _dispose_command). If any lp_l5, suppress consumed stream for ledger
    # consumers that should not step an incomplete trace.
    return AnalyzeAdapterResult(
        unevaluable=unevaluable,
        commands=() if unevaluable else tuple(leaves),
        dispositions=tuple(dispositions),
        provenance=provenance,
        lp_l5_reasons=lp_reasons,
        liquids=liquids,
        labware=labware,
        pipettes=pipettes,
        raw_commands=tuple(dict(c) for c in raw_commands),
        error_code="LP-L5" if unevaluable else None,
    )
