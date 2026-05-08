#!/usr/bin/env python3
"""
Migrate existing skills into gt-core/skills-repo/.

Source 1: agent-home/skills/*.md — flat .md files
Source 2: ~/.hermes/hermes-agent/skills/**/SKILL.md — categorized with YAML frontmatter

Creates categorized directory structure and copies each skill with proper structure.
"""

import os
import re
import shutil
from pathlib import Path

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
SKILLS_REPO = AGENT_HOME / "gt-core" / "skills-repo"
SOURCE1 = AGENT_HOME / "skills"
SOURCE2 = Path.home() / ".hermes" / "hermes-agent" / "skills"

# Category mapping for flat .md files from agent-home/skills/
CATEGORY_MAP = {
    # iOS Development
    "ios-developer": "ios-development",
    "miswag-ios-developer": "ios-development",
    "swiftui-pro": "ios-development",
    "swiftui-expert-skill": "ios-development",
    "swiftdata-pro": "ios-development",
    "swiftdata-expert-skill": "ios-development",
    "swift-testing-pro": "ios-development",
    "swift-testing-expert": "ios-development",
    "swift-concurrency": "ios-development",
    "swift-concurrency-pro": "ios-development",
    "core-data-expert": "ios-development",
    "hig-foundations": "ios-development",
    "hig-patterns": "ios-development",
    "app-store-optimization": "ios-development",
    "mobile-security-coder": "ios-development",
    "xcode-project-analyzer": "ios-development",
    "xcode-compilation-analyzer": "ios-development",
    "xcode-build-orchestrator": "ios-development",
    "xcode-build-fixer": "ios-development",
    "xcode-build-benchmark": "ios-development",
    "spm-build-analysis": "ios-development",
    "release-whats-changed": "ios-development",
    # Software Development
    "testing-patterns": "software-development",
    "error-handling-patterns": "software-development",
    "clean-code": "software-development",
    "code-reviewer": "software-development",
    "claude-code-guide": "software-development",
    "concise-planning": "software-development",
    "writing-plans": "software-development",
    "grill-me": "software-development",
    # Architecture
    "architecture": "architecture",
    "architecture-patterns": "architecture",
    # Superpowers
    "deep-research": "superpowers",
    "context-manager": "superpowers",
    "memory-systems": "superpowers",
}

def extract_frontmatter(content: str) -> tuple:
    """Extract YAML frontmatter and body from markdown."""
    if not content.startswith("---"):
        return None, content
    end_match = re.search(r"\n---\s*(?:\n|$)", content, re.MULTILINE)
    if not end_match:
        return None, content
    yaml_text = content[3:end_match.start()].strip()
    body = content[end_match.end():].lstrip()
    return yaml_text, body

def parse_yaml_value(yaml_text: str, key: str) -> str:
    """Simple key:value parser for YAML frontmatter."""
    for line in yaml_text.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""

def fix_frontmatter(yaml_text: str, skill_name: str) -> str:
    """Fix broken frontmatter: ensure name matches directory, quote descriptions with colons."""
    lines = yaml_text.splitlines()
    new_lines = []
    in_desc = False
    desc_block_type = None  # '>' or '|' or None
    for i, line in enumerate(lines):
        if line.startswith("name:"):
            new_lines.append(f"name: {skill_name}")
            continue
        if line.startswith("description:"):
            in_desc = True
            val = line.split(":", 1)[1].strip()
            if val.startswith('"') or val.startswith("'"):
                # Broken quoted string — convert to folded block
                quote_char = val[0]
                val = val[1:]
                if val.endswith(quote_char) and len(val) > 1:
                    val = val[:-1]
                    new_lines.append(f"description: \"{val}\"")
                    in_desc = False
                else:
                    new_lines.append("description: >")
                    if val:
                        new_lines.append(f"  {val}")
                    desc_block_type = ">"
            elif val.startswith(">") or val.startswith("|"):
                new_lines.append(line)
                desc_block_type = val[0]
            else:
                # If description contains a colon and isn't quoted, quote it
                if ":" in val and not (val.startswith('"') or val.startswith("'")):
                    new_lines.append(f'description: "{val}"')
                    in_desc = False
                else:
                    new_lines.append(line)
                    in_desc = False
            continue
        if in_desc and desc_block_type:
            if line.strip() == "" or line.startswith(" ") or line.startswith("\t"):
                new_lines.append(line)
                continue
            else:
                in_desc = False
                desc_block_type = None
                new_lines.append(line)
                continue
        if in_desc and not desc_block_type:
            if line.startswith(" ") or line.startswith("\t"):
                new_lines.insert(len(new_lines) - 1, "description: >")
                desc_block_type = ">"
                prev = new_lines.pop()
                prev_val = prev.split(":", 1)[1].strip()
                if prev_val.startswith('"') or prev_val.startswith("'"):
                    prev_val = prev_val[1:]
                new_lines.append(f"  {prev_val}")
                new_lines.append(f"  {line.strip()}")
            else:
                in_desc = False
                new_lines.append(line)
            continue
        new_lines.append(line)
    return "\n".join(new_lines)

def migrate_source1():
    """Migrate flat .md files from agent-home/skills/."""
    migrated = []
    for md_file in sorted(SOURCE1.glob("*.md")):
        skill_name = md_file.stem
        category = CATEGORY_MAP.get(skill_name, "misc")
        dest_dir = SKILLS_REPO / category / skill_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "SKILL.md"

        content = md_file.read_text(encoding="utf-8")
        yaml_text, body = extract_frontmatter(content)

        if yaml_text is None:
            # No frontmatter — create one
            # Derive a simple description from the first heading or first paragraph
            first_heading_match = re.search(r"^#+\s+(.+)$", body, re.MULTILINE)
            first_para_match = re.search(r"\n\n([^#\n].+?)(?:\n\n|\n#)", body, re.DOTALL)
            if first_heading_match:
                desc = first_heading_match.group(1).strip()
            elif first_para_match:
                desc = first_para_match.group(1).strip().replace("\n", " ")
            else:
                desc = f"Skill: {skill_name}"
            # Truncate description if too long
            if len(desc) > 200:
                desc = desc[:197] + "..."
            new_content = f"---\nname: {skill_name}\ndescription: {desc}\n---\n\n{body}"
        else:
            yaml_text = fix_frontmatter(yaml_text, skill_name)
            new_content = f"---\n{yaml_text}\n---\n\n{body}"

        dest_file.write_text(new_content, encoding="utf-8")
        migrated.append((skill_name, category, str(dest_file)))
    return migrated

def migrate_source2():
    """Migrate categorized skills from ~/.hermes/hermes-agent/skills/."""
    migrated = []
    for skill_md in sorted(SOURCE2.rglob("SKILL.md")):
        # Skip if inside references/templates/scripts (those are subdirs of a skill)
        rel_parts = skill_md.relative_to(SOURCE2).parts
        if len(rel_parts) < 2:
            continue
        category = rel_parts[0]
        skill_name = rel_parts[1]
        dest_dir = SKILLS_REPO / category / skill_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "SKILL.md"

        content = skill_md.read_text(encoding="utf-8")
        yaml_text, body = extract_frontmatter(content)

        if yaml_text is None:
            # Shouldn't happen for hermes skills, but handle gracefully
            new_content = content
        else:
            yaml_text = fix_frontmatter(yaml_text, skill_name)
            new_content = f"---\n{yaml_text}\n---\n\n{body}"

        dest_file.write_text(new_content, encoding="utf-8")
        migrated.append((skill_name, category, str(dest_file)))

        # Copy references/, templates/, scripts/ subdirs if they exist
        skill_src_dir = skill_md.parent
        for subdir_name in ("references", "templates", "scripts"):
            subdir_src = skill_src_dir / subdir_name
            if subdir_src.exists() and subdir_src.is_dir():
                subdir_dst = dest_dir / subdir_name
                if subdir_dst.exists():
                    shutil.rmtree(subdir_dst)
                shutil.copytree(subdir_src, subdir_dst)
    return migrated

def main():
    # Ensure skills-repo exists
    SKILLS_REPO.mkdir(parents=True, exist_ok=True)

    # Clear existing skills (but preserve .git, README.md, .gitignore)
    for item in SKILLS_REPO.iterdir():
        if item.name in (".git", ".gitignore", "README.md"):
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    migrated1 = migrate_source1()
    migrated2 = migrate_source2()

    print(f"Migrated {len(migrated1)} flat skills from agent-home/skills/")
    print(f"Migrated {len(migrated2)} categorized skills from ~/.hermes/hermes-agent/skills/")
    print(f"Total: {len(migrated1) + len(migrated2)} skills")

    # Print summary by category
    from collections import Counter
    cats = Counter([c for _, c, _ in migrated1 + migrated2])
    print("\nBy category:")
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()
