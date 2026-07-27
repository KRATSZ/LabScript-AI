"""Opentrons-specific checks: protocol AST vs deck_plan consistency."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Mapping

from .core import iter_plan_items
from .models import ValidationIssue


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _literal_slot(node: ast.AST | None) -> str | None:
    """Slot/location as str (accepts string or int constants like load_labware(..., 3))."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str) and node.value.strip():
            return node.value.strip()
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return str(int(node.value))
    return None


def _keyword_string(call: ast.Call, name: str) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return _literal_string(keyword.value)
    return None


def _keyword_slot(call: ast.Call, name: str) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return _literal_slot(keyword.value)
    return None


def extract_protocol_refs(path: Path) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set(), set()
    labware: set[tuple[str, str]] = set()
    instruments: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr == "load_labware":
            load_name = _literal_string(node.args[0]) if node.args else _keyword_string(node, "load_name")
            slot = (
                _literal_slot(node.args[1])
                if len(node.args) > 1
                else _keyword_slot(node, "location") or _keyword_slot(node, "slot")
            )
            if load_name and slot:
                labware.add((load_name, slot))
        elif func.attr == "load_instrument":
            instrument_name = (
                _literal_string(node.args[0]) if node.args else _keyword_string(node, "instrument_name")
            )
            mount = (
                _literal_string(node.args[1])
                if len(node.args) > 1
                else _keyword_string(node, "mount")
            )
            if instrument_name and mount:
                instruments.add((instrument_name, mount))
    return labware, instruments


def deck_labware_refs(deck_plan: Any) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for item in iter_plan_items(deck_plan, "labware"):
        slot = item.get("slot") or item.get("location")
        if isinstance(slot, int):
            slot = str(slot)
        if not isinstance(slot, str):
            continue
        for key in ("load_name", "definition", "name", "type"):
            name = item.get(key)
            if isinstance(name, str):
                refs.add((name, slot))
    return refs


def deck_instrument_refs(deck_plan: Any) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    if isinstance(deck_plan, Mapping):
        candidates = []
        for key in ("instruments", "pipettes"):
            value = deck_plan.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, Mapping))
            elif isinstance(value, Mapping):
                candidates.extend(item for item in value.values() if isinstance(item, Mapping))
        for item in candidates:
            mount = item.get("mount")
            if not isinstance(mount, str):
                continue
            for key in ("instrument_name", "name", "type"):
                name = item.get(key)
                if isinstance(name, str):
                    refs.add((name, mount))
    return refs


def validate_deck_plan(
    deck_plan: Any,
    path: Path,
    issues: list[ValidationIssue],
    *,
    protocol_path: Path | None = None,
) -> float:
    slot_owners_by_kind: dict[str, dict[str, str]] = {"labware": {}, "modules": {}}
    conflict = False
    for key in ("labware", "modules"):
        for item in iter_plan_items(deck_plan, key):
            slot = item.get("slot")
            name = item.get("name") or item.get("load_name") or item.get("module_type") or key
            if isinstance(slot, int):
                slot = str(slot)
            if not isinstance(slot, str):
                continue
            slot_owners = slot_owners_by_kind[key]
            if slot in slot_owners:
                conflict = True
                issues.append(
                    ValidationIssue(
                        code="deck_slot_conflict",
                        message=f"Deck slot {slot} is assigned to both {slot_owners[slot]} and {name}",
                        path=str(path),
                        critical_failure="deck_conflict",
                    )
                )
            else:
                slot_owners[slot] = str(name)
    mismatch = False
    if protocol_path and protocol_path.exists():
        protocol_labware, protocol_instruments = extract_protocol_refs(protocol_path)
        deck_labware = deck_labware_refs(deck_plan)
        deck_instruments = deck_instrument_refs(deck_plan)
        missing_labware = sorted(protocol_labware - deck_labware)
        missing_instruments = sorted(protocol_instruments - deck_instruments)
        for load_name, slot in missing_labware:
            mismatch = True
            issues.append(
                ValidationIssue(
                    code="deck_protocol_labware_mismatch",
                    message=f"protocol.py loads {load_name} in slot {slot}, but manifest.deck does not declare it",
                    path=str(path),
                    critical_failure="deck_conflict",
                )
            )
        for instrument_name, mount in missing_instruments:
            mismatch = True
            issues.append(
                ValidationIssue(
                    code="deck_protocol_instrument_mismatch",
                    message=f"protocol.py loads {instrument_name} on {mount}, but manifest.deck does not declare it",
                    path=str(path),
                    critical_failure="deck_conflict",
                )
            )
    return 0.0 if conflict or mismatch else 1.0
