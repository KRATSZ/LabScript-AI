#!/usr/bin/env python3
"""Search and reference bundled or external Opentrons protocol libraries."""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any, Mapping


def get_repo_root() -> Path:
    """Return the Opentrons-Lab-Agent repository root."""
    return Path(__file__).resolve().parents[3]


def get_default_library_candidates(repo_root: Path | None = None) -> list[tuple[str, Path]]:
    """Return library discovery candidates in precedence order."""
    root = repo_root or get_repo_root()
    return [
        ("bundled", root / "reference-protocols" / "Protocols-develop"),
        ("sibling", root.parent / "Protocols-develop"),
    ]


def resolve_library_path(
    explicit_path: Path | None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the protocol-library path with override-friendly precedence."""
    if explicit_path is not None:
        library_path = explicit_path.expanduser().resolve()
    else:
        env = environ if environ is not None else os.environ
        configured_path = env.get("OPENTRONS_PROTOCOL_LIBRARY_PATH")
        if configured_path:
            library_path = Path(configured_path).expanduser().resolve()
        else:
            library_path = None
            for _, candidate in get_default_library_candidates(repo_root):
                if candidate.exists():
                    library_path = candidate.resolve()
                    break
            if library_path is None:
                raise SystemExit(
                    "protocol library path is not configured; pass --library /path/to/Protocols-develop, "
                    "set OPENTRONS_PROTOCOL_LIBRARY_PATH, or vendor Protocols-develop into "
                    "reference-protocols/Protocols-develop"
                )

    if not library_path.exists():
        raise SystemExit(f"protocol library path does not exist: {library_path}")

    return library_path


def load_catalog(library_path: Path) -> dict[str, Any] | None:
    """Load protocol-catalog.json if available; return None otherwise."""
    catalog_path = library_path / "protocol-catalog.json"
    if not catalog_path.exists():
        return None
    try:
        return json.loads(safe_read_text(catalog_path))
    except (json.JSONDecodeError, Exception):
        return None


def get_protocol_directory(library_path: Path, slug: str) -> Path:
    """Resolve a protocol directory by slug."""
    protocol_dir = library_path / "protocols" / slug
    if not protocol_dir.exists():
        raise SystemExit(f"protocol slug does not exist: {slug}")
    if not protocol_dir.is_dir():
        raise SystemExit(f"protocol slug is not a directory: {slug}")
    return protocol_dir


def safe_read_text(path: Path) -> str:
    """Read a text file defensively."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def extract_summary_from_readme(readme_path: Path) -> str:
    """Extract a human-usable short description from README content."""
    content = safe_read_text(readme_path)
    lines = [line.rstrip() for line in content.splitlines()]

    in_description = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == "## description":
            in_description = True
            continue
        if in_description:
            if stripped.startswith("#"):
                break
            if stripped:
                return stripped[:200]

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("!"):
            return stripped[:200]

    return ""


def list_protocol_python_files(protocol_dir: Path) -> list[Path]:
    """Return protocol Python files for a protocol directory."""
    return sorted(path for path in protocol_dir.glob("*.py") if path.is_file())


def parse_literal_assignment(module: ast.Module, variable_name: str) -> Any | None:
    """Return a literal top-level assignment when available."""
    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if isinstance(target, ast.Name) and target.id == variable_name:
            try:
                return ast.literal_eval(statement.value)
            except Exception:
                return None
    return None


def infer_robot_types(
    requirements: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    python_path: Path,
) -> list[str]:
    """Infer robot type(s) from requirements, metadata, or filename."""
    robot_types: list[str] = []

    requirement_robot = requirements.get("robotType") if isinstance(requirements, dict) else None
    if isinstance(requirement_robot, str):
        robot_types.append(requirement_robot)

    metadata_robot = metadata.get("robot") if isinstance(metadata, dict) else None
    if isinstance(metadata_robot, str):
        robot_types.append(metadata_robot)
    elif isinstance(metadata_robot, list):
        robot_types.extend(item for item in metadata_robot if isinstance(item, str))

    filename = python_path.name.lower()
    if not robot_types:
        if ".ot2." in filename:
            robot_types.append("OT-2")
        elif "flex" in filename:
            robot_types.append("Flex")

    deduped: list[str] = []
    for robot_type in robot_types:
        if robot_type not in deduped:
            deduped.append(robot_type)
    return deduped


def extract_protocol_file_metadata(python_path: Path) -> dict[str, Any]:
    """Parse protocol metadata and requirements from a Python protocol file."""
    content = safe_read_text(python_path)
    parsed = ast.parse(content, filename=str(python_path))
    metadata = parse_literal_assignment(parsed, "metadata")
    requirements = parse_literal_assignment(parsed, "requirements")

    api_level = None
    if isinstance(requirements, dict):
        api_level = requirements.get("apiLevel")
    if api_level is None and isinstance(metadata, dict):
        api_level = metadata.get("apiLevel")

    return {
        "path": str(python_path),
        "apiLevel": api_level,
        "requirements": requirements if isinstance(requirements, dict) else None,
        "metadata": metadata if isinstance(metadata, dict) else None,
        "robotTypes": infer_robot_types(
            requirements if isinstance(requirements, dict) else None,
            metadata if isinstance(metadata, dict) else None,
            python_path,
        ),
    }


def build_protocol_document(protocol_dir: Path) -> tuple[str, dict[str, list[str]]]:
    """Build a search document and provenance map for a protocol directory."""
    sections: dict[str, list[str]] = {
        "directory": [protocol_dir.name],
        "readme": [],
        "python": [],
        "fields": [],
    }

    readme_path = protocol_dir / "README.md"
    if readme_path.exists():
        sections["readme"].append(safe_read_text(readme_path))

    for python_path in list_protocol_python_files(protocol_dir):
        sections["python"].append(safe_read_text(python_path))

    fields_path = protocol_dir / "fields.json"
    if fields_path.exists():
        sections["fields"].append(safe_read_text(fields_path))

    combined = "\n".join(
        piece.lower()
        for pieces in sections.values()
        for piece in pieces
    )
    return combined, sections


def search_protocols(
    library_path: Path,
    keywords: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search the protocol library across README, source, fields, and slug."""
    # Fast path: use catalog index when available
    catalog = load_catalog(library_path)
    if catalog is not None:
        return _search_via_catalog(catalog, keywords, limit)

    # Slow path: scan filesystem directly
    protocols_dir = library_path / "protocols"
    normalized_keywords = [keyword.lower() for keyword in keywords]
    results: list[dict[str, Any]] = []

    for proto_folder in sorted(protocols_dir.iterdir()):
        if not proto_folder.is_dir():
            continue

        search_document, sections = build_protocol_document(proto_folder)
        matched_keywords = [
            keyword for keyword in normalized_keywords if keyword in search_document
        ]
        if not matched_keywords:
            continue

        matched_in = [
            section_name
            for section_name, section_content in sections.items()
            if any(keyword in "\n".join(section_content).lower() for keyword in normalized_keywords)
        ]

        readme_path = proto_folder / "README.md"
        description = (
            extract_summary_from_readme(readme_path)
            if readme_path.exists()
            else f"Protocol at {proto_folder.name}"
        )

        results.append(
            {
                "name": proto_folder.name,
                "path": str(proto_folder),
                "description": description or f"Protocol at {proto_folder.name}",
                "matched_keywords": matched_keywords,
                "matched_in": matched_in,
            }
        )

    results.sort(key=lambda item: (-len(item["matched_keywords"]), item["name"]))
    return results[:limit]


def _search_via_catalog(
    catalog: dict[str, Any], keywords: list[str], limit: int
) -> list[dict[str, Any]]:
    """Fast search using pre-built catalog index."""
    normalized_keywords = [keyword.lower() for keyword in keywords]
    results: list[dict[str, Any]] = []

    for proto in catalog.get("protocols", []):
        if proto.get("hidden"):
            continue

        # Build search text from catalog fields
        searchable = " ".join([
            proto.get("slug", ""),
            proto.get("title", ""),
            proto.get("description", ""),
            " ".join(proto.get("method_tags", [])),
            " ".join(
                f"{cat} {' '.join(subs)}"
                for cat, subs in proto.get("categories", {}).items()
            ),
            " ".join(proto.get("pipettes", [])),
            " ".join(proto.get("labware", [])),
            " ".join(proto.get("reagents", [])),
            " ".join(
                param.get("name", "")
                for param in proto.get("parameters", [])
            ),
        ]).lower()

        matched_keywords = [kw for kw in normalized_keywords if kw in searchable]
        if not matched_keywords:
            continue

        # Determine match locations
        matched_in = []
        title_lower = proto.get("title", "").lower()
        desc_lower = proto.get("description", "").lower()
        slug_lower = proto.get("slug", "").lower()
        tags_text = " ".join(proto.get("method_tags", [])).lower()

        for kw in matched_keywords:
            if kw in slug_lower and "slug" not in matched_in:
                matched_in.append("slug")
            if kw in title_lower and "title" not in matched_in:
                matched_in.append("title")
            if kw in desc_lower and "readme" not in matched_in:
                matched_in.append("readme")
            if kw in tags_text and "tags" not in matched_in:
                matched_in.append("tags")

        results.append({
            "name": proto["slug"],
            "title": proto.get("title", ""),
            "path": proto.get("slug", ""),
            "description": proto.get("description", "")[:200],
            "matched_keywords": matched_keywords,
            "matched_in": matched_in,
            "method_tags": proto.get("method_tags", []),
        })

    results.sort(key=lambda item: (-len(item["matched_keywords"]), item["name"]))
    return results[:limit]


def get_cookbook_sections(library_path: Path) -> dict[str, Any]:
    """List cookbook sections when the snapshot includes a cookbook."""
    cookbook = library_path / "Cookbook.md"
    if not cookbook.exists():
        return {
            "available": False,
            "path": str(cookbook),
            "message": (
                "Cookbook.md is not present in this Protocols-develop snapshot. "
                "Use search/show/snippet against protocol folders instead."
            ),
            "sections": [],
        }

    sections = []
    for line in safe_read_text(cookbook).splitlines():
        if line.startswith("##"):
            sections.append(line.strip("#").strip())

    return {
        "available": True,
        "path": str(cookbook),
        "sections": sections,
    }


def list_categories(library_path: Path) -> list[str]:
    """Get unique categories from protocol READMEs."""
    protocols_dir = library_path / "protocols"
    categories = set()

    for proto_folder in protocols_dir.iterdir():
        if not proto_folder.is_dir():
            continue

        readme = proto_folder / "README.md"
        if not readme.exists():
            continue

        in_categories = False
        for line in safe_read_text(readme).splitlines():
            if "## Categories" in line or "## categories" in line:
                in_categories = True
                continue
            if in_categories:
                stripped = line.strip()
                if stripped.startswith("*"):
                    category = stripped.strip("*").strip()
                    if category:
                        categories.add(category)
                elif stripped.startswith("-"):
                    category = stripped.strip("-").strip()
                    if category:
                        categories.add(category)
                elif stripped and not stripped.startswith("#"):
                    break

    return sorted(categories)


def show_protocol(library_path: Path, slug: str) -> dict[str, Any]:
    """Return protocol directory details and parsed source metadata."""
    protocol_dir = get_protocol_directory(library_path, slug)
    readme_path = protocol_dir / "README.md"
    python_paths = list_protocol_python_files(protocol_dir)
    fields_path = protocol_dir / "fields.json"
    python_files = [extract_protocol_file_metadata(path) for path in python_paths]

    robot_types: list[str] = []
    for python_file in python_files:
        for robot_type in python_file["robotTypes"]:
            if robot_type not in robot_types:
                robot_types.append(robot_type)

    return {
        "slug": slug,
        "protocol_dir": str(protocol_dir),
        "summary": extract_summary_from_readme(readme_path) if readme_path.exists() else "",
        "readme_path": str(readme_path) if readme_path.exists() else None,
        "python_paths": [str(path) for path in python_paths],
        "fields_path": str(fields_path) if fields_path.exists() else None,
        "robot_types": robot_types,
        "python_files": python_files,
    }


def show_catalog_summary(library_path: Path) -> dict[str, Any]:
    """Return catalog metadata and statistics for agent consumption."""
    catalog = load_catalog(library_path)
    if catalog is None:
        return {
            "available": False,
            "message": (
                "No protocol-catalog.json found. Generate it with: "
                "python reference-protocols/Protocols-develop/scripts/generate_catalog.py"
            ),
        }

    # Collect tag statistics
    tag_counts: dict[str, int] = {}
    for proto in catalog.get("protocols", []):
        if proto.get("hidden"):
            continue
        for tag in proto.get("method_tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:20]

    return {
        "available": True,
        "generated_at": catalog.get("generated_at", ""),
        "total_protocols": catalog.get("total_protocols", 0),
        "total_categories": len(catalog.get("categories", {})),
        "top_method_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "category_names": sorted(catalog.get("categories", {}).keys()),
    }


def build_snippet(lines: list[str], line_number: int, context_lines: int) -> tuple[int, int, str]:
    """Build a line-based snippet around a 1-based line number."""
    start = max(1, line_number - context_lines)
    end = min(len(lines), line_number + context_lines)
    snippet = "\n".join(lines[start - 1:end])
    return start, end, snippet


def collect_keyword_snippets(
    file_path: Path,
    keywords: list[str],
    context_lines: int,
) -> list[dict[str, Any]]:
    """Collect contextual snippets for keyword matches in a file."""
    content = safe_read_text(file_path)
    lines = content.splitlines()
    normalized_keywords = [keyword.lower() for keyword in keywords]
    snippets: list[dict[str, Any]] = []
    seen_ranges: set[tuple[int, int]] = set()

    for index, line in enumerate(lines, start=1):
        matched_keywords = [keyword for keyword in normalized_keywords if keyword in line.lower()]
        if not matched_keywords:
            continue

        start, end, snippet = build_snippet(lines, index, context_lines)
        if (start, end) in seen_ranges:
            continue
        seen_ranges.add((start, end))
        snippets.append(
            {
                "path": str(file_path),
                "line_start": start,
                "line_end": end,
                "matched_keywords": matched_keywords,
                "snippet": snippet,
            }
        )

    return snippets


def snippet_protocol(
    library_path: Path,
    slug: str,
    keywords: list[str],
    limit: int = 5,
    context_lines: int = 3,
) -> dict[str, Any]:
    """Return reusable snippets from README and protocol sources."""
    protocol_dir = get_protocol_directory(library_path, slug)
    readme_path = protocol_dir / "README.md"
    candidate_files = [readme_path] if readme_path.exists() else []
    candidate_files.extend(list_protocol_python_files(protocol_dir))

    snippets: list[dict[str, Any]] = []
    if keywords:
        for candidate_file in candidate_files:
            snippets.extend(collect_keyword_snippets(candidate_file, keywords, context_lines))
    else:
        if readme_path.exists():
            readme_lines = safe_read_text(readme_path).splitlines()
            if readme_lines:
                start, end, snippet = build_snippet(readme_lines, 1, 12)
                snippets.append(
                    {
                        "path": str(readme_path),
                        "line_start": start,
                        "line_end": end,
                        "matched_keywords": [],
                        "snippet": snippet,
                    }
                )
        python_paths = list_protocol_python_files(protocol_dir)
        if python_paths:
            code_lines = safe_read_text(python_paths[0]).splitlines()
            if code_lines:
                start, end, snippet = build_snippet(code_lines, 1, 12)
                snippets.append(
                    {
                        "path": str(python_paths[0]),
                        "line_start": start,
                        "line_end": end,
                        "matched_keywords": [],
                        "snippet": snippet,
                    }
                )

    return {
        "slug": slug,
        "keywords": keywords,
        "snippet_count": min(len(snippets), limit),
        "snippets": snippets[:limit],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the Opentrons protocol library")
    parser.add_argument(
        "--library",
        type=Path,
        default=None,
        help="Path to a Protocols-develop directory. Defaults to env, bundled, then sibling discovery.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search protocols by keywords")
    search.add_argument("keywords", nargs="+", help="Search keywords")
    search.add_argument("--limit", type=int, default=10, help="Maximum results")
    search.set_defaults(handler=lambda args: search_protocols(args.library, args.keywords, args.limit))

    show = subparsers.add_parser("show", help="Show a protocol's files and parsed metadata")
    show.add_argument("slug", help="Protocol folder name")
    show.set_defaults(handler=lambda args: show_protocol(args.library, args.slug))

    snippet = subparsers.add_parser("snippet", help="Extract README or code snippets from a protocol")
    snippet.add_argument("slug", help="Protocol folder name")
    snippet.add_argument("keywords", nargs="*", help="Optional keywords used to find focused snippets")
    snippet.add_argument("--limit", type=int, default=5, help="Maximum snippets to return")
    snippet.add_argument("--context-lines", type=int, default=3, help="Context lines before and after a match")
    snippet.set_defaults(
        handler=lambda args: snippet_protocol(
            args.library,
            args.slug,
            args.keywords,
            limit=args.limit,
            context_lines=args.context_lines,
        )
    )

    cookbook = subparsers.add_parser("cookbook", help="List cookbook patterns when available")
    cookbook.set_defaults(handler=lambda args: get_cookbook_sections(args.library))

    categories_cmd = subparsers.add_parser("categories", help="List protocol categories")
    categories_cmd.set_defaults(handler=lambda args: list_categories(args.library))

    catalog_cmd = subparsers.add_parser("catalog", help="Show catalog summary and stats")
    catalog_cmd.set_defaults(handler=lambda args: show_catalog_summary(args.library))

    args = parser.parse_args()
    args.library = resolve_library_path(args.library)
    result = args.handler(args)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
