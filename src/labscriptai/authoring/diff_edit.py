"""SEARCH/REPLACE DiffEdit helpers for localized protocol repair."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


SEARCH_START_RE = re.compile(r"^\s*-{7,}\s*SEARCH\s*$")
SEARCH_END_RE = re.compile(r"^\s*={7,}\s*$")
REPLACE_END_RE = re.compile(r"^\s*\+{7,}\s*REPLACE\s*$")


class DiffEditError(ValueError):
    """DiffEdit blocks could not be applied safely."""

    def __init__(self, message: str, *, rejected_count: int = 1) -> None:
        super().__init__(message)
        self.rejected_count = rejected_count


@dataclass(frozen=True)
class DiffEditResult:
    content: str
    applied_count: int
    rejected_count: int = 0


@dataclass(frozen=True)
class _Replacement:
    start: int
    end: int
    content: str


def apply_search_replace_diff(original_content: str, diff_content: str) -> DiffEditResult:
    """Apply SEARCH/REPLACE blocks using progressive matching fallbacks."""

    blocks = _parse_blocks(diff_content)
    replacements: list[_Replacement] = []
    for index, (search_content, replace_content) in enumerate(blocks, start=1):
        if not search_content:
            raise DiffEditError(f"block {index} has empty SEARCH content")
        match = _find_match(original_content, search_content)
        if match is None:
            raise DiffEditError(f"block {index} SEARCH content did not match")
        replacements.append(_Replacement(match[0], match[1], replace_content))

    _reject_overlaps(replacements)
    patched = original_content
    for replacement in sorted(replacements, key=lambda item: item.start, reverse=True):
        patched = patched[: replacement.start] + replacement.content + patched[replacement.end :]
    return DiffEditResult(patched, applied_count=len(replacements), rejected_count=0)


def _parse_blocks(diff_content: str) -> list[tuple[str, str]]:
    lines = diff_content.splitlines()
    blocks: list[tuple[str, str]] = []
    in_search = False
    in_replace = False
    search_lines: list[str] = []
    replace_lines: list[str] = []

    for line in lines:
        if SEARCH_START_RE.match(line):
            if in_search or in_replace:
                raise DiffEditError("nested SEARCH marker")
            in_search = True
            search_lines = []
            replace_lines = []
            continue
        if SEARCH_END_RE.match(line):
            if not in_search:
                raise DiffEditError("separator found outside SEARCH block")
            in_search = False
            in_replace = True
            continue
        if REPLACE_END_RE.match(line):
            if not in_replace:
                raise DiffEditError("REPLACE marker found outside REPLACE block")
            blocks.append(("\n".join(search_lines), "\n".join(replace_lines)))
            in_replace = False
            continue
        if in_search:
            search_lines.append(line)
        elif in_replace:
            replace_lines.append(line)
        elif line.strip():
            raise DiffEditError("unexpected text outside SEARCH/REPLACE blocks")

    if in_search or in_replace:
        raise DiffEditError("unterminated SEARCH/REPLACE block")
    if not blocks:
        raise DiffEditError("no SEARCH/REPLACE blocks found")
    return blocks


def _find_match(original_content: str, search_content: str) -> tuple[int, int] | None:
    exact_index = original_content.find(search_content)
    if exact_index != -1:
        return exact_index, exact_index + len(search_content)

    fuzzy = _fuzzy_match(original_content, search_content)
    if fuzzy is not None:
        return fuzzy

    line_trimmed = _line_trimmed_match(original_content, search_content)
    if line_trimmed is not None:
        return line_trimmed

    return _block_anchor_match(original_content, search_content)


def _fuzzy_match(original_content: str, search_content: str) -> tuple[int, int] | None:
    original_lines = original_content.splitlines(True)
    search_lines = search_content.splitlines(True)
    if not search_lines:
        return None
    matcher = SequenceMatcher(None, original_lines, search_lines, autojunk=False)
    match = matcher.find_longest_match(0, len(original_lines), 0, len(search_lines))
    if match.size == 0 or match.size / len(search_lines) < 0.6:
        return None
    start_line = match.a - match.b
    end_line = start_line + len(search_lines)
    if start_line < 0 or end_line > len(original_lines):
        return None
    start = sum(len(line) for line in original_lines[:start_line])
    end = start + sum(len(line) for line in original_lines[start_line:end_line])
    return start, end


def _line_trimmed_match(original_content: str, search_content: str) -> tuple[int, int] | None:
    original_lines = original_content.splitlines(True)
    search_lines = search_content.splitlines()
    if not search_lines:
        return None
    stripped_search = [line.strip() for line in search_lines]
    for start_line in range(0, len(original_lines) - len(search_lines) + 1):
        window = original_lines[start_line : start_line + len(search_lines)]
        if [line.strip() for line in window] == stripped_search:
            return _line_range_to_span(original_lines, start_line, start_line + len(search_lines))
    return None


def _block_anchor_match(original_content: str, search_content: str) -> tuple[int, int] | None:
    original_lines = original_content.splitlines(True)
    search_lines = search_content.splitlines()
    if len(search_lines) < 3:
        return None
    first = search_lines[0].strip()
    last = search_lines[-1].strip()
    size = len(search_lines)
    for start_line in range(0, len(original_lines) - size + 1):
        if original_lines[start_line].strip() != first:
            continue
        if original_lines[start_line + size - 1].strip() != last:
            continue
        return _line_range_to_span(original_lines, start_line, start_line + size)
    return None


def _line_range_to_span(lines: list[str], start_line: int, end_line: int) -> tuple[int, int]:
    start = sum(len(line) for line in lines[:start_line])
    end = start + sum(len(line) for line in lines[start_line:end_line])
    if end_line > start_line and lines[end_line - 1].endswith("\n"):
        end -= 1
    return start, end


def _reject_overlaps(replacements: list[_Replacement]) -> None:
    previous_end = -1
    for replacement in sorted(replacements, key=lambda item: item.start):
        if replacement.start < previous_end:
            raise DiffEditError("SEARCH/REPLACE blocks overlap")
        previous_end = replacement.end
