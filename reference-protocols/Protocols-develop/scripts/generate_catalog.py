#!/usr/bin/env python3
"""Generate a searchable catalog of all Opentrons protocols.

Reads every protocol folder under protocols/, extracts structured metadata
from README.md / fields.json / .py source, and writes:
  - protocol-catalog.json  (machine-readable, full metadata)
  - protocol-catalog.md    (human-readable, grouped by category)

Usage:
    python scripts/generate_catalog.py [--protocols-dir protocols/] [--output-dir .]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# README section parser
# ---------------------------------------------------------------------------

def parse_readme(readme_path: Path) -> dict:
    """Extract structured metadata from a protocol README.md."""
    content = readme_path.read_text(encoding="utf-8", errors="replace")
    sections: dict[str, list[str]] = defaultdict(list)
    current_section = "_preamble"
    first_heading_found = False
    for line in content.splitlines():
        # Detect headings
        m = re.match(r"^#{1,6}\s+(.+)", line)
        if m:
            heading = m.group(1).strip()
            # The first # heading is always the title — store it, don't make a section
            if not first_heading_found and line.startswith("# ") and not line.startswith("## "):
                sections["_title_raw"].append(heading)
                first_heading_found = True
                current_section = "_preamble"
                continue
            first_heading_found = True
            heading = m.group(1).strip().lower()
            # Normalize common headings
            if "categories" in heading:
                current_section = "categories"
            elif "description" in heading:
                current_section = "description"
            elif "labware" in heading:
                current_section = "labware"
            elif "pipette" in heading:
                current_section = "pipettes"
            elif "module" in heading:
                current_section = "modules"
            elif "robot" in heading:
                current_section = "robot"
            elif "reagent" in heading:
                current_section = "reagents"
            elif "process" in heading:
                current_section = "process"
            elif "additional note" in heading:
                current_section = "notes"
            elif "deck setup" in heading or "deck layout" in heading:
                current_section = "deck"
            elif "internal" in heading:
                current_section = "internal"
            else:
                current_section = heading
            continue
        sections[current_section].append(line.rstrip())

    # Title from first heading
    title = ""
    if sections.get("_title_raw"):
        title = sections["_title_raw"][0]
    if not title:
        for line in sections["_preamble"]:
            m = re.match(r"^#\s+(.+)", line)
            if m:
                title = m.group(1).strip()
                break

    # Description: first non-empty, non-image paragraph
    description_lines = []
    for line in sections.get("description", []):
        stripped = line.strip()
        if not stripped or stripped.startswith("!["):
            if description_lines:
                break
            continue
        description_lines.append(stripped)
    description = " ".join(description_lines)

    # Categories: parse nested bullet structure
    categories: dict[str, list[str]] = {}
    current_cat = None
    for line in sections.get("categories", []):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("*") or stripped.startswith("-"):
            # Level 1 bullet (category)
            cat_name = stripped.lstrip("*- ").strip()
            if cat_name:
                current_cat = cat_name
                categories.setdefault(current_cat, [])
        elif stripped.startswith("\t") and current_cat:
            # Level 2 bullet (subcategory) — tab-indented
            sub = stripped.strip().lstrip("*- ").strip()
            if sub and sub not in categories[current_cat]:
                categories[current_cat].append(sub)

    # Labware: extract names from bullet list / links
    labware = _extract_bullet_items(sections.get("labware", []))

    # Pipettes: extract names
    pipettes = _extract_bullet_items(sections.get("pipettes", []))

    # Modules
    modules = _extract_bullet_items(sections.get("modules", []))

    # Robot
    robot = _extract_bullet_items(sections.get("robot", []))

    # Reagents
    reagents = _extract_bullet_items(sections.get("reagents", []))

    # Internal code (last line of internal section)
    internal = ""
    for line in reversed(sections.get("internal", [])):
        stripped = line.strip()
        if stripped:
            internal = stripped
            break

    return {
        "title": title,
        "description": description[:500] if description else "",
        "categories": categories,
        "labware": labware,
        "pipettes": pipettes,
        "modules": modules,
        "robot": robot,
        "reagents": reagents,
        "internal_code": internal,
    }


def _extract_bullet_items(lines: list[str]) -> list[str]:
    """Extract cleaned text from bullet list items, stripping markdown links."""
    items = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("*") or stripped.startswith("-"):
            text = stripped.lstrip("*- ").strip()
            # Strip markdown links: [name](url) -> name
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            if text:
                items.append(text)
    return items


# ---------------------------------------------------------------------------
# fields.json parser
# ---------------------------------------------------------------------------

def parse_fields(fields_path: Path) -> list[dict]:
    """Extract parameter definitions from fields.json."""
    if not fields_path.exists():
        return []
    try:
        data = json.loads(fields_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    if not isinstance(data, list):
        return []
    params = []
    for field in data:
        if isinstance(field, dict):
            params.append({
                "name": field.get("name", ""),
                "label": field.get("label", ""),
                "type": field.get("type", ""),
            })
    return params


# ---------------------------------------------------------------------------
# Protocol folder scanner
# ---------------------------------------------------------------------------

def scan_protocol(protocol_dir: Path) -> dict | None:
    """Build a catalog entry for one protocol folder."""
    readme_path = protocol_dir / "README.md"
    fields_path = protocol_dir / "fields.json"

    # Find python file
    py_files = sorted(p for p in protocol_dir.glob("*.py") if p.is_file())
    py_file = py_files[0].name if py_files else ""

    # Custom labware
    labware_dir = protocol_dir / "labware"
    custom_labware = sorted(p.name for p in labware_dir.glob("*.json")) if labware_dir.exists() else []

    # Hidden flags
    hidden = (protocol_dir / ".hide-from-search").exists() or (protocol_dir / ".ignore").exists()

    readme_meta = parse_readme(readme_path) if readme_path.exists() else {}
    fields = parse_fields(fields_path)

    # Derive a short "method type" tag from categories + folder name
    method_tags = _derive_method_tags(protocol_dir.name, readme_meta.get("categories", {}))

    return {
        "slug": protocol_dir.name,
        "title": readme_meta.get("title", ""),
        "description": readme_meta.get("description", ""),
        "categories": readme_meta.get("categories", {}),
        "method_tags": method_tags,
        "pipettes": readme_meta.get("pipettes", []),
        "labware": readme_meta.get("labware", []),
        "modules": readme_meta.get("modules", []),
        "robot": readme_meta.get("robot", []),
        "reagents": readme_meta.get("reagents", []),
        "parameters": fields,
        "python_file": py_file,
        "custom_labware_count": len(custom_labware),
        "hidden": hidden,
        "internal_code": readme_meta.get("internal_code", ""),
    }


def _derive_method_tags(folder_name: str, categories: dict[str, list[str]]) -> list[str]:
    """Derive searchable method tags from folder name and categories."""
    tags = set()

    # From categories
    for cat, subs in categories.items():
        tags.add(cat.lower())
        for sub in subs:
            tags.add(sub.lower())

    # From folder name keywords
    name_lower = folder_name.lower()
    keyword_map = {
        "pcr": "pcr",
        "extraction": "extraction",
        "normali": "normalization",
        "pooling": "pooling",
        "cherrypick": "cherrypicking",
        "dilut": "dilution",
        "cleanup": "cleanup",
        "magbead": "magnetic_beads",
        "elisa": "elisa",
        "library": "library_prep",
        "sequenc": "sequencing",
        "rna": "rna",
        "dna": "dna",
        "protein": "protein",
        "assay": "assay",
        "sample": "sample_prep",
        "transfer": "transfer",
        "aliquot": "aliquoting",
        "wash": "wash",
        "bead": "beads",
        "synthesis": "synthesis",
        "amplif": "amplification",
        "fragment": "fragmentation",
        "ligat": "ligation",
        "quantif": "quantification",
        "index": "indexing",
    }
    for key, tag in keyword_map.items():
        if key in name_lower:
            tags.add(tag)

    return sorted(tags)


# ---------------------------------------------------------------------------
# Catalog generation
# ---------------------------------------------------------------------------

def generate_catalog(protocols_dir: Path, output_dir: Path) -> dict:
    """Scan all protocols and build the full catalog."""
    protocols = []
    all_categories: dict[str, set[str]] = defaultdict(set)

    folders = sorted(p for p in protocols_dir.iterdir() if p.is_dir())
    total = len(folders)

    for i, folder in enumerate(folders, 1):
        if i % 100 == 0:
            print(f"  scanning {i}/{total}: {folder.name}", file=sys.stderr)
        entry = scan_protocol(folder)
        if entry:
            protocols.append(entry)
            for cat, subs in entry["categories"].items():
                all_categories[cat].update(subs)

    # Convert category sets to sorted lists
    categories = {cat: sorted(subs) for cat, subs in sorted(all_categories.items())}

    catalog = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_protocols": len(protocols),
        "categories": categories,
        "protocols": protocols,
    }

    # Write JSON
    json_path = output_dir / "protocol-catalog.json"
    json_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {json_path} ({len(protocols)} protocols)", file=sys.stderr)

    # Write Markdown
    md_path = output_dir / "protocol-catalog.md"
    md_content = _generate_markdown(catalog)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"wrote {md_path}", file=sys.stderr)

    return catalog


def _generate_markdown(catalog: dict) -> str:
    """Generate a human-readable Markdown catalog grouped by category."""
    lines = [
        "# Protocol Catalog",
        "",
        f"Auto-generated index of **{catalog['total_protocols']}** protocols.",
        f"Generated: {catalog['generated_at'][:10]}",
        "",
        "---",
        "",
        "## Categories Overview",
        "",
    ]

    # Category summary table
    lines.append("| Category | Subcategories | Protocol Count |")
    lines.append("|----------|--------------|----------------|")

    # Build category -> protocol mapping
    cat_protocols: dict[str, list[dict]] = defaultdict(list)
    uncategorized: list[dict] = []
    for proto in catalog["protocols"]:
        if proto["hidden"]:
            continue
        if proto["categories"]:
            for cat in proto["categories"]:
                cat_protocols[cat].append(proto)
        else:
            uncategorized.append(proto)

    for cat, subs in catalog["categories"].items():
        count = len(cat_protocols.get(cat, []))
        sub_str = ", ".join(subs[:3])
        if len(subs) > 3:
            sub_str += f" (+{len(subs)-3})"
        lines.append(f"| {cat} | {sub_str} | {count} |")

    if uncategorized:
        lines.append(f"| Uncategorized | - | {len(uncategorized)} |")
    lines.append("")

    # Detailed sections by category
    lines.append("---")
    lines.append("")
    lines.append("## Protocols by Category")
    lines.append("")

    for cat in sorted(cat_protocols.keys()):
        protos = cat_protocols[cat]
        lines.append(f"### {cat}")
        lines.append("")
        lines.append("| Slug | Title | Key Tags |")
        lines.append("|------|-------|----------|")
        for proto in sorted(protos, key=lambda p: p["slug"]):
            title = proto["title"][:60]
            tags = ", ".join(proto["method_tags"][:4])
            lines.append(f"| `{proto['slug']}` | {title} | {tags} |")
        lines.append("")

    # Method tag index
    tag_protos: dict[str, list[str]] = defaultdict(list)
    for proto in catalog["protocols"]:
        if proto["hidden"]:
            continue
        for tag in proto["method_tags"]:
            tag_protos[tag].append(proto["slug"])

    lines.append("---")
    lines.append("")
    lines.append("## Method Tag Index")
    lines.append("")
    for tag in sorted(tag_protos.keys()):
        slugs = tag_protos[tag]
        slug_list = ", ".join(f"`{s}`" for s in slugs[:8])
        if len(slugs) > 8:
            slug_list += f" (+{len(slugs)-8})"
        lines.append(f"- **{tag}** ({len(slugs)}): {slug_list}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate protocol catalog")
    parser.add_argument(
        "--protocols-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "protocols",
        help="Path to the protocols/ directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Where to write protocol-catalog.json and .md",
    )
    args = parser.parse_args()

    if not args.protocols_dir.exists():
        print(f"error: {args.protocols_dir} does not exist", file=sys.stderr)
        return 1

    generate_catalog(args.protocols_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
