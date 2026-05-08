#!/usr/bin/env python3
"""
Bundle skills into a single YAML file.

Usage:
    python bundle-skills.py <bundle_name> <skill_path> [<skill_path> ...]
    python bundle-skills.py ios-dev-bundle ios-development/swiftui-expert ios-development/uikit-expert

Reads each skill's SKILL.md from gt-core/skills-repo/ and outputs a single
YAML bundle file to gt-core/bundles/{name}.yaml.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_frontmatter(content: str) -> Tuple[dict, str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}, "Missing YAML frontmatter"
    end_match = re.search(r"\n---\s*(?:\n|$)", content, re.MULTILINE)
    if not end_match:
        return {}, "Missing closing --- for YAML frontmatter"
    yaml_text = content[3:end_match.start()].strip()
    if not yaml_text:
        return {}, "Empty YAML frontmatter"
    try:
        import yaml
        data = yaml.safe_load(yaml_text)
        if data is None:
            return {}, "Empty YAML frontmatter"
        if not isinstance(data, dict):
            return {}, f"YAML frontmatter must be a mapping, got {type(data).__name__}"
        return data, ""
    except ImportError:
        data = {}
        for line in yaml_text.splitlines():
            if ":" in line and not line.startswith("#"):
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                data[key] = val
        return data, ""
    except Exception as e:
        return {}, f"Invalid YAML syntax: {e}"


def _write_yaml(obj, f, indent=0):
    """Pure Python YAML writer fallback."""
    prefix = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and ("\n" in v or len(v) > 80):
                f.write(f"{prefix}{k}: |\n")
                for line in v.splitlines():
                    f.write(f"{prefix}  {line}\n")
            elif isinstance(v, (dict, list)):
                f.write(f"{prefix}{k}:\n")
                _write_yaml(v, f, indent + 1)
            else:
                f.write(f"{prefix}{k}: {v}\n")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                f.write(f"{prefix}-\n")
                _write_yaml(item, f, indent + 1)
            else:
                f.write(f"{prefix}- {item}\n")
    else:
        f.write(f"{prefix}{obj}\n")


def read_skill_content(skill_path: Path) -> str:
    """Read full SKILL.md content, return as string."""
    try:
        return skill_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {skill_path}: {e}", file=sys.stderr)
        sys.exit(1)


def bundle_skills(bundle_name: str, skill_paths: List[str], repo_dir: Path) -> dict:
    """Build bundle dict from list of skill paths."""
    skills = []
    for skill_path_str in skill_paths:
        skill_path = repo_dir / skill_path_str / "SKILL.md"
        if not skill_path.exists():
            print(f"Error: Skill not found: {skill_path}", file=sys.stderr)
            sys.exit(1)

        content = read_skill_content(skill_path)
        frontmatter, error = extract_frontmatter(content)
        if error:
            print(f"Error: Invalid frontmatter in {skill_path}: {error}", file=sys.stderr)
            sys.exit(1)

        name = frontmatter.get("name", skill_path.parent.name)
        skills.append({
            "name": name,
            "content": content,
        })

    return {
        "bundle": {
            "name": bundle_name,
            "version": "1.0.0",
            "skills": skills,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle skills into a YAML file.")
    parser.add_argument("bundle_name", help="Name of the bundle (used for output filename)")
    parser.add_argument("skill_paths", nargs="+", help="Relative paths to skills inside skills-repo (e.g., category/skill-name)")
    parser.add_argument("--repo", default="gt-core/skills-repo", help="Path to skills repository (default: gt-core/skills-repo)")
    parser.add_argument("--outdir", default="gt-core/bundles", help="Output directory for bundle YAML (default: gt-core/bundles)")
    parser.add_argument("--version", default="1.0.0", help="Bundle version (default: 1.0.0)")
    args = parser.parse_args()

    repo_dir = Path(args.repo).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()

    if not repo_dir.exists():
        print(f"Error: Skills repo not found: {repo_dir}", file=sys.stderr)
        sys.exit(1)

    outdir.mkdir(parents=True, exist_ok=True)

    bundle = bundle_skills(args.bundle_name, args.skill_paths, repo_dir)
    bundle["bundle"]["version"] = args.version

    try:
        import yaml
        has_yaml = True
    except ImportError:
        has_yaml = False

    output_path = outdir / f"{args.bundle_name}.yaml"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            if has_yaml:
                yaml.dump(bundle, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            else:
                _write_yaml(bundle, f)
        print(f"Bundle written to: {output_path}")
        return 0
    except Exception as e:
        print(f"Error writing bundle: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
