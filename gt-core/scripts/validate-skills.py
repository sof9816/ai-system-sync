#!/usr/bin/env python3
"""
Validate skills in a directory by scanning for SKILL.md files,
extracting YAML frontmatter, and checking required fields and constraints.

Usage:
    python validate-skills.py <skills_dir>
    python validate-skills.py ~/.hermes/skills

Exits with code 1 if any errors, 0 if all valid.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_frontmatter(content: str) -> Tuple[dict, str]:
    """Extract YAML frontmatter from markdown content.
    Returns (frontmatter_dict, error_message).
    """
    if not content.startswith("---"):
        return {}, "Missing YAML frontmatter (must start with ---)"

    # Find the closing ---
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
        # Fallback: simple key:value parser for basic validation
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


def is_broken_quoted_string(value, raw_yaml_text: str) -> bool:
    """Check if a description value looks like a broken quoted string.

    A 'broken quoted string' in YAML frontmatter occurs when a description
    uses double/single quotes but spans multiple lines without proper YAML
    multi-line syntax (folded > or literal |). The YAML parser then silently
    concatenates the lines into one long string with embedded newline chars,
    or fails to parse correctly.

    We flag strings that:
      - contain literal newline characters
      - are NOT from a folded (>) or literal (|) block scalar in the raw text
      - look like they were meant to be multi-line but got mangled
    """
    if not isinstance(value, str):
        return False
    if "\n" not in value:
        return False

    # Check if the raw YAML text uses a block scalar for the description
    # Match 'description:' followed by optional whitespace, then '>' or '|'
    block_scalar_pattern = re.compile(
        r"^description\s*:\s*[>|]", re.MULTILINE
    )
    if block_scalar_pattern.search(raw_yaml_text):
        return False

    return True


def validate_skill(skill_path: Path, seen_names: dict) -> Tuple[bool, str]:
    """Validate a single SKILL.md file.
    Returns (is_valid, error_message).
    """
    rel_path = skill_path.relative_to(Path(skill_path.anchor))

    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Cannot read file: {e}"

    # Extract frontmatter
    frontmatter, error = extract_frontmatter(content)
    if error:
        return False, error

    # Also capture raw YAML text for block-scalar checks
    end_match = re.search(r"\n---\s*(?:\n|$)", content, re.MULTILINE)
    raw_yaml_text = content[3:end_match.start()].strip() if end_match else ""

    # Check required fields
    if "name" not in frontmatter:
        return False, "Missing required field: name"
    if "description" not in frontmatter:
        return False, "Missing required field: description"

    name = frontmatter["name"]
    description = frontmatter["description"]

    # name must be a string
    if not isinstance(name, str):
        return False, f"Field 'name' must be a string, got {type(name).__name__}"

    # description must be a string
    if not isinstance(description, str):
        return False, f"Field 'description' must be a string, got {type(description).__name__}"

    # Check name matches parent directory
    parent_dir = skill_path.parent.name
    if name != parent_dir:
        return False, f"Name mismatch: frontmatter says '{name}', parent directory is '{parent_dir}'"

    # Check for duplicate skill names
    if name in seen_names:
        return False, f"Duplicate skill name '{name}' (also found at {seen_names[name]})"
    seen_names[name] = str(skill_path)

    # Check description for broken quoted strings
    if is_broken_quoted_string(description, raw_yaml_text):
        return False, "Description appears to be a broken quoted string (use folded '>' or literal '|' block for multi-line)"

    return True, ""


def scan_skills(skills_dir: Path) -> List[Path]:
    """Recursively scan for SKILL.md files."""
    skill_files = []
    for root, _dirs, files in os.walk(skills_dir):
        if "SKILL.md" in files:
            skill_files.append(Path(root) / "SKILL.md")
    return skill_files


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <skills_dir>")
        sys.exit(2)

    skills_dir = Path(sys.argv[1]).expanduser().resolve()
    if not skills_dir.exists():
        print(f"Error: Directory not found: {skills_dir}")
        sys.exit(2)
    if not skills_dir.is_dir():
        print(f"Error: Not a directory: {skills_dir}")
        sys.exit(2)

    skill_files = scan_skills(skills_dir)
    if not skill_files:
        print(f"No SKILL.md files found in {skills_dir}")
        sys.exit(0)

    seen_names: dict = {}
    errors = 0

    print(f"Scanning {len(skill_files)} skill(s) in {skills_dir}\n")

    for skill_path in sorted(skill_files):
        rel_path = skill_path.relative_to(skills_dir)
        valid, error = validate_skill(skill_path, seen_names)
        if valid:
            print(f"  ✓ {rel_path}")
        else:
            print(f"  ✗ {rel_path}")
            print(f"    Error: {error}")
            errors += 1

    print()
    if errors:
        print(f"Result: {errors} error(s) found.")
        return 1
    else:
        print("Result: All skills valid.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
