#!/usr/bin/env python3
"""
gt-core/scripts/export-to-claude.py
Export GT skills to Claude Code CLAUDE.md format.

Usage:
    python export-to-claude.py [--watch] [--bundle skill1,skill2,...] [--cursorrules]
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (no external deps)
# ---------------------------------------------------------------------------


def _simple_yaml_load(text: str) -> dict:
    """Parse a simple flat YAML mapping. Handles strings, lists, nested dicts one level deep."""
    result: dict = {}
    lines = text.splitlines()
    i = 0
    current_key = None
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.endswith(":"):
            current_key = stripped[:-1].strip()
            result[current_key] = {}
            i += 1
            # peek next lines for nested dict
            j = i
            nested: dict = {}
            while j < len(lines):
                nl = lines[j]
                ns = nl.lstrip()
                if not ns or ns.startswith("#"):
                    j += 1
                    continue
                n_indent = len(nl) - len(ns)
                if n_indent <= indent:
                    break
                if ns.startswith("-"):
                    break
                if ": " in ns or ns.endswith(":"):
                    if ns.endswith(":"):
                        sub_key = ns[:-1].strip()
                        # look one more level
                        k = j + 1
                        sub_nested: dict = {}
                        while k < len(lines):
                            sl = lines[k]
                            ss = sl.lstrip()
                            if not ss or ss.startswith("#"):
                                k += 1
                                continue
                            s_indent = len(sl) - len(ss)
                            if s_indent <= n_indent:
                                break
                            if ss.startswith("-"):
                                break
                            if ": " in ss or ss.endswith(":"):
                                if ss.endswith(":"):
                                    sub_sub_key = ss[:-1].strip()
                                    m = k + 1
                                    sub_sub_nested: dict = {}
                                    while m < len(lines):
                                        tl = lines[m]
                                        ts = tl.lstrip()
                                        if not ts or ts.startswith("#"):
                                            m += 1
                                            continue
                                        t_indent = len(tl) - len(ts)
                                        if t_indent <= s_indent:
                                            break
                                        if ts.startswith("-"):
                                            # list under sub_sub_key
                                            lst: list = []
                                            while m < len(lines):
                                                ul = lines[m]
                                                us = ul.lstrip()
                                                if not us or us.startswith("#"):
                                                    m += 1
                                                    continue
                                                u_indent = len(ul) - len(us)
                                                if u_indent <= s_indent:
                                                    break
                                                if us.startswith("- "):
                                                    lst.append(_parse_yaml_value(us[2:].strip()))
                                                    m += 1
                                                else:
                                                    break
                                            sub_sub_nested[sub_sub_key] = lst
                                            break
                                        elif ": " in ts:
                                            sub_sub_nested[ts.split(":", 1)[0].strip()] = _parse_yaml_value(ts.split(":", 1)[1].strip())
                                            m += 1
                                        else:
                                            m += 1
                                    sub_nested[sub_sub_key] = sub_sub_nested if sub_sub_nested else {}
                                    k = m
                                    break
                                else:
                                    sub_nested[ss.split(":", 1)[0].strip()] = _parse_yaml_value(ss.split(":", 1)[1].strip())
                                    k += 1
                            else:
                                k += 1
                        j = k
                        nested[sub_key] = sub_nested if sub_nested else {}
                    else:
                        parts = ns.split(":", 1)
                        nested[parts[0].strip()] = _parse_yaml_value(parts[1].strip())
                        j += 1
                else:
                    break
            if nested:
                result[current_key] = nested
            else:
                # maybe list follows
                j = i
                lst: list = []
                while j < len(lines):
                    nl = lines[j]
                    ns = nl.lstrip()
                    if not ns or ns.startswith("#"):
                        j += 1
                        continue
                    n_indent = len(nl) - len(ns)
                    if n_indent <= indent:
                        break
                    if ns.startswith("- "):
                        lst.append(_parse_yaml_value(ns[2:].strip()))
                        j += 1
                    else:
                        break
                if lst:
                    result[current_key] = lst
            i = j
            continue
        if ": " in stripped:
            key, val = stripped.split(":", 1)
            result[key.strip()] = _parse_yaml_value(val.strip())
        i += 1
    return result


def _parse_yaml_value(val: str):
    val = val.strip()
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        if not inner.strip():
            return []
        items = []
        for item in inner.split(","):
            items.append(_parse_yaml_value(item.strip()))
        return items
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    if val == "null" or val == "~":
        return None
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        pass
    return val


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SKILLS_REPO = Path("/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo")
OUTPUT_DIR = Path("/Users/gt/Public/MyFiles/agent-home/gt-core/claude-export")
MASTER_FILE = OUTPUT_DIR / "CLAUDE.md"
MANIFEST_FILE = OUTPUT_DIR / "manifest.json"
SKILLS_DIR = OUTPUT_DIR / "skills"
CURSORRULES_FILE = OUTPUT_DIR / ".cursorrules"

# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from SKILL.md content."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    try:
        fm = _simple_yaml_load(match.group(1))
    except Exception:
        fm = {}
    body = content[match.end():]
    return fm if isinstance(fm, dict) else {}, body


def to_claude_skill_md(skill_name: str, frontmatter: dict, body: str, source_path: Path) -> str:
    """Convert a SKILL.md to Claude Code skill markdown format."""
    description = frontmatter.get("description", "")
    version = frontmatter.get("version", "")
    author = frontmatter.get("author", "")
    license_ = frontmatter.get("license", "")
    metadata = frontmatter.get("metadata", {})
    hermes_meta = metadata.get("hermes", {}) if isinstance(metadata, dict) else {}
    tags = hermes_meta.get("tags", [])
    related = hermes_meta.get("related_skills", [])
    prerequisites = frontmatter.get("prerequisites", {})

    lines: list[str] = []
    lines.append(f"# {skill_name}")
    lines.append("")
    if description:
        lines.append(f"> {description}")
        lines.append("")
    lines.append("## Metadata")
    lines.append("")
    if version:
        lines.append(f"- **Version:** {version}")
    if author:
        lines.append(f"- **Author:** {author}")
    if license_:
        lines.append(f"- **License:** {license_}")
    if tags:
        lines.append(f"- **Tags:** {', '.join(str(t) for t in tags)}")
    if related:
        lines.append(f"- **Related Skills:** {', '.join(str(r) for r in related)}")
    if prerequisites:
        lines.append(f"- **Prerequisites:** {json.dumps(prerequisites)}")
    lines.append(f"- **Source:** `{source_path}`")
    lines.append("")
    lines.append("## Skill Body")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    return "\n".join(lines)


def to_cursorrules_skill(skill_name: str, frontmatter: dict, body: str) -> str:
    """Generate a .cursorrules snippet for a single skill."""
    description = frontmatter.get("description", "")
    lines: list[str] = []
    lines.append(f"# Skill: {skill_name}")
    lines.append("")
    if description:
        lines.append(f"Description: {description}")
        lines.append("")
    # Include a condensed version: first 2000 chars of body
    condensed = body.strip()[:2000]
    lines.append(condensed)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_skills(repo: Path) -> list[tuple[Path, dict, str]]:
    """Walk the skills repo and return list of (SKILL.md path, frontmatter, body)."""
    results: list[tuple[Path, dict, str]] = []
    for skill_md in sorted(repo.rglob("SKILL.md")):
        content = skill_md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        results.append((skill_md, fm, body))
    return results


def get_category(skill_path: Path, repo: Path) -> str:
    """Derive category folder name from skill path relative to repo root."""
    try:
        rel = skill_path.relative_to(repo)
        parts = rel.parts
        return parts[0] if len(parts) > 1 else "uncategorized"
    except ValueError:
        return "uncategorized"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_skills(
    repo: Path,
    output_dir: Path,
    bundle: list[str] | None = None,
    cursorrules: bool = False,
) -> dict[str, Any]:
    """Export all (or bundled) skills to Claude format. Returns manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    skills_dir = output_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    all_skills = discover_skills(repo)
    manifest: dict[str, Any] = {
        "version": "1.0.0",
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_repo": str(repo),
        "skills": {},
    }

    # Filter by bundle if requested
    if bundle:
        bundle_set = set(bundle)
        filtered = []
        for skill_path, fm, body in all_skills:
            name = fm.get("name", skill_path.parent.name)
            if name in bundle_set:
                filtered.append((skill_path, fm, body))
        all_skills = filtered

    master_parts: list[str] = []
    master_parts.append("# GT Skills — Claude Code Export")
    master_parts.append("")
    master_parts.append(
        f"This file contains {len(all_skills)} skills exported from the GT skills repository."
    )
    master_parts.append("")
    master_parts.append("## Default Skill Loading")
    master_parts.append("")
    master_parts.append("At the start of EVERY chat, you MUST auto-invoke these skills using the `Skill` tool:")
    master_parts.append("")
    master_parts.append("- `caveman` — ultra-compressed communication mode")
    master_parts.append("- `brainstorming` — creative exploration before implementation")
    master_parts.append("- `obsidian` — note-taking and knowledge management")
    master_parts.append("- `grill-me` — stress-test plans and designs")
    master_parts.append("- `context7` — pull version-specific documentation")
    master_parts.append("")
    master_parts.append("If the project is iOS, ALSO load the iOS bundle (including `miswag-ios-developer`).")
    master_parts.append("Project type is read from `.project.yaml` or auto-detected via `project-detect.py`.")
    master_parts.append("")
    master_parts.append("---")
    master_parts.append("")

    for skill_path, fm, body in all_skills:
        skill_name = fm.get("name", skill_path.parent.name)
        category = get_category(skill_path, repo)
        claude_md = to_claude_skill_md(skill_name, fm, body, skill_path)

        # Write individual skill file
        cat_dir = skills_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        skill_file = cat_dir / f"{skill_name}.md"
        skill_file.write_text(claude_md, encoding="utf-8")

        # Write .cursorrules per-skill if requested
        if cursorrules:
            cursor_file = cat_dir / f"{skill_name}.cursorrules"
            cursor_file.write_text(to_cursorrules_skill(skill_name, fm, body), encoding="utf-8")

        # Add to master
        master_parts.append(claude_md)
        master_parts.append("---")
        master_parts.append("")

        # Manifest entry
        manifest["skills"][skill_name] = {
            "category": category,
            "source": str(skill_path),
            "claude_path": str(skill_file.relative_to(output_dir)),
            "description": fm.get("description", ""),
            "version": fm.get("version", ""),
            "tags": fm.get("metadata", {}).get("hermes", {}).get("tags", []) if isinstance(fm.get("metadata"), dict) else [],
        }

    # Write master file
    master_file = output_dir / "CLAUDE.md"
    master_file.write_text("\n".join(master_parts), encoding="utf-8")

    # Write manifest
    manifest_file = output_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Write root .cursorrules
    if cursorrules:
        cursorrules_content = generate_root_cursorrules(all_skills, output_dir)
        cursorrules_file = output_dir / ".cursorrules"
        cursorrules_file.write_text(cursorrules_content, encoding="utf-8")

    return manifest


def generate_root_cursorrules(
    all_skills: list[tuple[Path, dict, str]], output_dir: Path
) -> str:
    """Generate a root .cursorrules file referencing all exported skills."""
    lines: list[str] = [
        "# GT Skills — Root Cursor Rules",
        "",
        "These rules reference all exported GT skills for Claude Code.",
        "",
    ]
    for skill_path, fm, _body in all_skills:
        skill_name = fm.get("name", skill_path.parent.name)
        category = get_category(skill_path, SKILLS_REPO)
        lines.append(f"## {skill_name}")
        lines.append(f"- Category: {category}")
        lines.append(f"- File: skills/{category}/{skill_name}.md")
        desc = fm.get("description", "")
        if desc:
            lines.append(f"- Description: {desc}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

def watch_and_export(
    repo: Path,
    output_dir: Path,
    bundle: list[str] | None = None,
    cursorrules: bool = False,
    interval: int = 5,
) -> None:
    """Monitor the skills repo for changes and regenerate affected files."""
    print(f"Watching {repo} for changes (interval={interval}s)...")
    print("Press Ctrl+C to stop.")

    # Build initial mtimes map: path -> mtime
    def build_mtimes() -> dict[Path, float]:
        return {p: p.stat().st_mtime for p in repo.rglob("SKILL.md")}

    mtimes = build_mtimes()

    while True:
        time.sleep(interval)
        new_mtimes = build_mtimes()
        changed = []
        for p, mtime in new_mtimes.items():
            if p not in mtimes or mtimes[p] != mtime:
                changed.append(p)
        if changed:
            print(f"Detected changes in {len(changed)} file(s): {[str(c) for c in changed]}")
            manifest = export_skills(repo, output_dir, bundle=bundle, cursorrules=cursorrules)
            print(f"Regenerated export. Skills: {len(manifest['skills'])}")
            mtimes = new_mtimes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Export GT skills to Claude Code format")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Monitor skills repo for changes and regenerate",
    )
    parser.add_argument(
        "--bundle",
        type=str,
        default=None,
        help="Comma-separated list of skill names to export (default: all)",
    )
    parser.add_argument(
        "--cursorrules",
        action="store_true",
        help="Also generate per-skill .cursorrules files and root .cursorrules",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_DIR),
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    args = parser.parse_args()

    repo = SKILLS_REPO
    output_dir = Path(args.output)
    bundle = [s.strip() for s in args.bundle.split(",")] if args.bundle else None

    if args.watch:
        try:
            watch_and_export(repo, output_dir, bundle=bundle, cursorrules=args.cursorrules)
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0
    else:
        manifest = export_skills(repo, output_dir, bundle=bundle, cursorrules=args.cursorrules)
        print(f"Exported {len(manifest['skills'])} skill(s) to {output_dir}")
        print(f"  Master: {output_dir / 'CLAUDE.md'}")
        print(f"  Manifest: {output_dir / 'manifest.json'}")
        if args.cursorrules:
            print(f"  CursorRules: {output_dir / '.cursorrules'}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
