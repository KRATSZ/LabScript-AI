"""Read-only skill markdown. No gate, no robot execution."""

from __future__ import annotations

from pathlib import Path

_SKILLS_DIR = Path(__file__).resolve().parents[1] / "plugins" / "skills"
AUTHORING_SKILLS = ("authoring-guide", "error-taxonomy")
LIVE_ONLY_SKILLS = ("safety-brief", "recovery-playbooks", "pressure-trace")


def list_skills() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if not _SKILLS_DIR.is_dir():
        return items
    for path in sorted(_SKILLS_DIR.glob("*.md")):
        name = path.stem
        kind = "authoring" if name in AUTHORING_SKILLS else "reference"
        if name in LIVE_ONLY_SKILLS:
            kind = "live_docs_only"
        items.append({"name": name, "kind": kind})
    return items


def read_skill(name: str) -> dict[str, str]:
    stem = (name or "").strip().removesuffix(".md")
    if not stem:
        return {"error": "skill name required", "skills": _join_names()}
    path = (_SKILLS_DIR / f"{stem}.md").resolve()
    try:
        path.relative_to(_SKILLS_DIR.resolve())
    except ValueError:
        return {"error": "skill path escaped plugins/skills"}
    if not path.is_file():
        return {"error": f"unknown skill {stem!r}", "skills": _join_names()}
    note = ""
    if stem in LIVE_ONLY_SKILLS:
        note = "This branch has no live Flex. Treat as documentation only."
    return {"name": stem, "kind": _kind(stem), "text": path.read_text(encoding="utf-8"), "note": note}


def _kind(name: str) -> str:
    if name in AUTHORING_SKILLS:
        return "authoring"
    if name in LIVE_ONLY_SKILLS:
        return "live_docs_only"
    return "reference"


def _join_names() -> str:
    return ", ".join(item["name"] for item in list_skills()) or "(none)"
