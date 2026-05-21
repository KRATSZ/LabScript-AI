"""Progressive-disclosure skill loader for authoring guidance."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillEntry:
    name: str
    path: Path
    description: str

    def load_content(self) -> str:
        return self.path.read_text(encoding="utf-8")


class SkillLoader:
    def __init__(self, skills_dir: Path | str | None = None) -> None:
        if skills_dir is None:
            skills_dir = Path(__file__).resolve().parent / "skills"
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, SkillEntry] = {}
        self.reload()

    def reload(self) -> None:
        self.skills.clear()
        if not self.skills_dir.exists():
            return
        for path in sorted(self.skills_dir.glob("*.md")):
            self.skills[path.stem] = SkillEntry(
                name=path.stem,
                path=path,
                description=self._extract_description(path),
            )

    def list_skills(self) -> list[str]:
        return sorted(self.skills)

    def get_content(self, name: str) -> str | None:
        entry = self.skills.get(name)
        return entry.load_content() if entry else None

    def get_catalog(self) -> str:
        return "\n".join(
            f"- {name}: {self.skills[name].description}" for name in sorted(self.skills)
        )

    @staticmethod
    def _extract_description(path: Path) -> str:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
            return stripped[:120]
        return "(no description)"
