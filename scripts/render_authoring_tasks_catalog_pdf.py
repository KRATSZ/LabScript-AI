#!/usr/bin/env python3
"""Render benchmarks/authoring/tasks.yaml to a printable PDF catalog (prompts + metadata)."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fpdf import FPDF  # type: ignore[import-untyped]

from labscriptai.benchmark.tasks import load_authoring_tasks

# macOS system font with wide Unicode coverage (em dash, quotes in prompts).
_ARIAL_UNICODE = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")


def _hard_wrap(text: str, width: int = 92) -> str:
    """Break very long unspaced runs so PDF line breaking never sees a glyph-wider-than-cell case."""
    out_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line
        while len(line) > width:
            out_lines.append(line[:width])
            line = line[width:]
        out_lines.append(line)
    return "\n".join(out_lines)


def _register_unicode_font(pdf: FPDF) -> str:
    if _ARIAL_UNICODE.is_file():
        pdf.add_font("TaskFont", "", str(_ARIAL_UNICODE))
        return "TaskFont"
    pdf.set_font("Helvetica", "", 10)
    return "Helvetica"


def _build_pdf(tasks_path: Path, *, title: str) -> FPDF:
    tasks = load_authoring_tasks(tasks_path)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 14, 14)
    font = _register_unicode_font(pdf)
    pdf.add_page()
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)
    pdf.set_font(font, "", 14)
    pdf.multi_cell(w, 7, title)
    pdf.set_x(pdf.l_margin)
    pdf.set_font(font, "", 9)
    pdf.ln(2)
    src_display = (
        str(tasks_path.relative_to(ROOT)) if tasks_path.is_relative_to(ROOT) else str(tasks_path)
    )
    pdf.multi_cell(
        w,
        4.5,
        f"Source: {src_display}\n"
        f"Generated: {date.today().isoformat()}\n"
        f"Tasks: {len(tasks)}",
    )
    pdf.ln(5)

    for task in tasks:
        pdf.set_x(pdf.l_margin)
        pdf.set_font(font, "", 10)
        head = (
            f"{task.task_id}   difficulty={task.difficulty}   "
            f"holdout={'yes' if task.holdout else 'no'}   source={task.source}   "
            f"contract={task.output_contract}"
        )
        pdf.multi_cell(w, 5, head)
        if task.spec.default_samples is not None or task.spec.expected_risk_flags:
            pdf.set_x(pdf.l_margin)
            pdf.set_font(font, "", 8.5)
            bits: list[str] = []
            if task.spec.default_samples is not None:
                bits.append(f"default_samples={task.spec.default_samples}")
            if task.spec.expected_risk_flags:
                bits.append("expected_risk_flags=" + "; ".join(task.spec.expected_risk_flags))
            if task.off_platform_handoff:
                bits.append("off_platform_handoff=" + ", ".join(task.off_platform_handoff))
            pdf.multi_cell(w, 4, " | ".join(bits))
        pdf.set_x(pdf.l_margin)
        pdf.set_font(font, "", 8.5)
        pdf.multi_cell(w, 4, _hard_wrap(task.prompt))
        pdf.ln(4)
    return pdf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks",
        type=Path,
        default=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
        help="Path to frozen authoring tasks manifest",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "benchmarks" / "authoring" / "tasks_catalog.pdf",
        help="Output PDF path",
    )
    parser.add_argument("--title", default="LabscriptAI authoring benchmark — task catalog")
    args = parser.parse_args()

    tasks_path: Path = args.tasks
    if not tasks_path.is_file():
        print(f"Missing tasks file: {tasks_path}", file=sys.stderr)
        return 1

    pdf = _build_pdf(tasks_path, title=args.title)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(args.output))
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
