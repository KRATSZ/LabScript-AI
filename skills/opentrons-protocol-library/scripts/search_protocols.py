#!/usr/bin/env python3
"""Search and reference the Opentrons Protocol Library."""

import argparse
import json
from pathlib import Path


def search_protocols(
    library_path: Path,
    keywords: list[str],
    limit: int = 10,
) -> list[dict[str, str]]:
    """Search protocol library by keywords in README files."""
    protocols_dir = library_path / "protocols"
    results = []

    for proto_folder in protocols_dir.iterdir():
        if not proto_folder.is_dir():
            continue

        readme = proto_folder / "README.md"
        if not readme.exists():
            continue

        try:
            content = readme.read_text().lower()
        except Exception:
            continue

        # Check if any keyword matches
        if any(keyword.lower() in content for keyword in keywords):
            # Get protocol name and extract description
            proto_name = proto_folder.name
            description = ""

            # Try to extract description from README
            for line in readme.read_text().split("\n"):
                line = line.strip()
                if line.startswith("## Description") or line.startswith("## description"):
                    # Get next few lines as description
                    break
                if line and not line.startswith("#"):
                    description = line[:100]
                    break

            results.append({
                "name": proto_name,
                "path": str(proto_folder),
                "description": description or f"Protocol at {proto_name}",
            })

        if len(results) >= limit:
            break

    return results


def get_cookbook_sections(library_path: Path) -> dict[str, str]:
    """Get section headings from the Cookbook."""
    cookbook = library_path / "Cookbook.md"
    if not cookbook.exists():
        return {}

    sections = {}
    for line in cookbook.read_text().split("\n"):
        if line.startswith("##"):
            title = line.strip("#").strip()
            sections[title] = f"See {cookbook} for '{title}' pattern"
    return sections


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

        # Look for Categories section
        in_categories = False
        for line in readme.read_text().split("\n"):
            if "## Categories" in line or "## categories" in line:
                in_categories = True
                continue
            if in_categories:
                if line.strip().startswith("*"):
                    category = line.strip("*").strip()
                    if category:
                        categories.add(category)
                elif line.strip().startswith("-"):
                    category = line.strip("-").strip()
                    if category:
                        categories.add(category)
                elif line.strip() and not line.startswith("#"):
                    break

    return sorted(categories)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search Opentrons Protocol Library"
    )
    parser.add_argument(
        "--library",
        type=Path,
        default=Path(__file__).parent.parent.parent.parent / "Protocols-develop",
        help="Path to Protocols-develop directory",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search command
    search = subparsers.add_parser("search", help="Search protocols by keywords")
    search.add_argument("keywords", nargs="+", help="Search keywords")
    search.add_argument("--limit", type=int, default=10, help="Maximum results")
    search.set_defaults(handler=lambda args: search_protocols(args.library, args.keywords, args.limit))

    # Cookbook command
    cookbook = subparsers.add_parser("cookbook", help="List Cookbook patterns")
    cookbook.set_defaults(handler=lambda args: get_cookbook_sections(args.library))

    # Categories command
    categories_cmd = subparsers.add_parser("categories", help="List protocol categories")
    categories_cmd.set_defaults(handler=lambda args: list_categories(args.library))

    args = parser.parse_args()
    result = args.handler(args)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
