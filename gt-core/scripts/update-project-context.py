#!/usr/bin/env python3
"""
update-project-context.py — Update project-specific agent context.

Usage:
    python update-project-context.py [directory] [--apply] [--obsidian]

1. Detects project type from .project.yaml or directory contents.
2. Generates/updates local AGENTS.md with project-specific skills.
3. Updates Obsidian with project context notes.
4. Optionally updates skills from the skills-repo if they are stale.
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    # Fallback: use venv python if yaml not available
    VENV_PYTHON = Path("/Users/gt/Public/MyFiles/agent-home/dashboard/backend/venv/bin/python3")
    if VENV_PYTHON.exists():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), __file__] + sys.argv[1:])
    else:
        print("Error: pyyaml is required. Install with: pip install pyyaml")
        sys.exit(1)

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
CONFIG_PATH = AGENT_HOME / "gt-core/config/gt-config.yaml"
SKILLS_REPO = AGENT_HOME / "gt-core/skills-repo"
OBSIDIAN_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes"

# Reuse project-detect logic
FILE_TYPE_MAP = {
    "Package.swift": {"type": "ios", "skills": ["swift", "xcode"], "agents": ["ios-dev"]},
    "pubspec.yaml": {"type": "flutter", "skills": ["dart", "flutter"], "agents": ["flutter-dev"]},
    "package.json": {"type": "node", "skills": ["javascript", "typescript", "node"], "agents": ["frontend-dev", "node-dev"]},
    "requirements.txt": {"type": "python", "skills": ["python"], "agents": ["python-dev"]},
    "setup.py": {"type": "python", "skills": ["python"], "agents": ["python-dev"]},
    "pyproject.toml": {"type": "python", "skills": ["python"], "agents": ["python-dev"]},
    "Cargo.toml": {"type": "rust", "skills": ["rust"], "agents": ["rust-dev"]},
    "go.mod": {"type": "go", "skills": ["go"], "agents": ["go-dev"]},
    "pom.xml": {"type": "java", "skills": ["java", "maven"], "agents": ["java-dev"]},
    "build.gradle": {"type": "java", "skills": ["java", "gradle"], "agents": ["java-dev"]},
    "CMakeLists.txt": {"type": "cpp", "skills": ["cpp", "cmake"], "agents": ["cpp-dev"]},
    "Makefile": {"type": "c", "skills": ["c", "make"], "agents": ["c-dev"]},
    "Gemfile": {"type": "ruby", "skills": ["ruby"], "agents": ["ruby-dev"]},
    "composer.json": {"type": "php", "skills": ["php"], "agents": ["php-dev"]},
    "Dockerfile": {"type": "docker", "skills": ["docker"], "agents": ["devops"]},
    "docker-compose.yml": {"type": "docker", "skills": ["docker", "compose"], "agents": ["devops"]},
    "vite.config.ts": {"type": "node", "skills": ["typescript", "vite"], "agents": ["frontend-dev"]},
    "vite.config.js": {"type": "node", "skills": ["javascript", "vite"], "agents": ["frontend-dev"]},
    "tailwind.config.js": {"type": "node", "skills": ["tailwind", "css"], "agents": ["frontend-dev"]},
    "tsconfig.json": {"type": "node", "skills": ["typescript"], "agents": ["frontend-dev"]},
}


def log(msg: str, level: str = "INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        log(f"Failed to load YAML {path}: {e}", "ERROR")
        return {}


def detect_project_type(directory: Path) -> Optional[Dict[str, Any]]:
    """Guess project type by scanning directory contents."""
    detected: Dict[str, Any] = {}
    found_files: List[str] = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in {"node_modules", "venv", ".git", "__pycache__", ".pytest_cache", "dist", "build", ".next", "DerivedData", ".build"}]
        for filename, meta in FILE_TYPE_MAP.items():
            if filename in files:
                found_files.append(filename)
                if "type" not in detected:
                    detected["type"] = meta["type"]
                detected.setdefault("skills", set()).update(meta.get("skills", []))
                detected.setdefault("agents", set()).update(meta.get("agents", []))

    if not found_files:
        return None

    detected["skills"] = sorted(detected["skills"])
    detected["agents"] = sorted(detected["agents"])
    detected["detected_files"] = found_files
    return detected


def read_project_yaml(directory: Path) -> Optional[Dict[str, Any]]:
    candidate = directory / ".project.yaml"
    if not candidate.is_file():
        return None
    with open(candidate, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["directory"] = str(directory)
    return data


def build_local_agents_md(
    project_data: dict,
    gt_skills: dict,
    project_type: str,
) -> str:
    """Build a project-local AGENTS.md that merges defaults + project bundle."""
    default_skills = gt_skills.get("default", [])
    project_bundles = gt_skills.get("project_bundles", {})
    bundle = project_bundles.get(project_type, [])

    lines = [
        f"# AGENTS.md — {project_data.get('name', 'Unknown Project')}",
        "",
        f"**Type:** `{project_type}`  ",
        f"**Path:** `{project_data.get('directory', '.')}`  ",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}Z",
        "",
        "## Default Skills (Auto-Load)",
        "",
        "These skills MUST be invoked at the start of every chat in this project:",
        "",
    ]
    for skill in default_skills:
        lines.append(f"- `{skill}`")
    lines.append("")

    if bundle:
        lines.extend([
            f"## {project_type.upper()} Project Bundle (Auto-Load)",
            "",
            f"Because this is a `{project_type}` project, also load:",
            "",
        ])
        for skill in bundle:
            lines.append(f"- `{skill}`")
        lines.append("")

    lines.extend([
        "## Instructions",
        "",
        "1. At the start of EVERY chat, invoke the `Skill` tool for each skill listed above.",
        "2. If a skill is missing from the environment, run the sync script:",
        "   `python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/sync-skills.py`",
        "3. Update this file by running:",
        "   `python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/update-project-context.py --apply`",
        "",
    ])

    return "\n".join(lines) + "\n"


def write_obsidian_project_note(project_data: dict, project_type: str, bundle: List[str]):
    """Write/update an Obsidian note for this project's context."""
    name = project_data.get("name", "unknown")
    safe_name = name.replace(" ", "-").replace("/", "-")
    note_path = OBSIDIAN_VAULT / f"projects/{safe_name}-context.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# Project Context: {name}",
        "",
        f"- **Type:** `{project_type}`",
        f"- **Path:** `{project_data.get('directory', 'N/A')}`",
        f"- **Last Updated:** {ts}",
        "",
        "## Active Skills",
        "",
    ]
    for skill in bundle:
        lines.append(f"- [[{skill}]]")
    lines.extend([
        "",
        "## Notes",
        "",
        "_Add session notes here._",
        "",
    ])

    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Updated Obsidian note: {note_path}")


def update_skills_if_needed(auto_update_skills: List[str], dry_run: bool):
    """Run sync-skills.py if any auto-update skill has changed."""
    sync_script = AGENT_HOME / "gt-core/scripts/sync-skills.py"
    if not sync_script.exists():
        log("sync-skills.py not found, skipping skill update", "WARN")
        return

    if dry_run:
        log("[DRY-RUN] Would run sync-skills.py for auto-update skills")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(sync_script)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            log("Skills synced successfully")
        else:
            log(f"Skill sync failed: {result.stderr}", "ERROR")
    except Exception as e:
        log(f"Skill sync error: {e}", "ERROR")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update project-specific agent context")
    parser.add_argument("directory", nargs="?", default=".", help="Project directory")
    parser.add_argument("--apply", action="store_true", help="Write AGENTS.md and update Obsidian")
    parser.add_argument("--obsidian", action="store_true", help="Update Obsidian notes")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        log(f"Not a directory: {directory}", "ERROR")
        return 1

    dry_run = not args.apply

    # Load GT config
    gt = load_yaml(CONFIG_PATH)
    gt_skills = gt.get("skills", {})

    # Try .project.yaml first
    project_data = read_project_yaml(directory)
    if project_data:
        log(f"Found .project.yaml: {project_data.get('name')}")
        project_type = project_data.get("type", "unknown")
    else:
        log("No .project.yaml found; auto-detecting...")
        detection = detect_project_type(directory)
        if detection:
            project_type = detection["type"]
            project_data = {
                "name": directory.name,
                "type": project_type,
                "directory": str(directory),
                "skills": detection.get("skills", []),
                "agents": detection.get("agents", []),
            }
            log(f"Detected project type: {project_type}")
        else:
            log("Could not detect project type.")
            project_type = "unknown"
            project_data = {"name": directory.name, "type": "unknown", "directory": str(directory)}

    # Determine effective bundle
    project_bundles = gt_skills.get("project_bundles", {})
    bundle = project_bundles.get(project_type, [])

    # Build local AGENTS.md
    agents_md_content = build_local_agents_md(project_data, gt_skills, project_type)
    agents_md_path = directory / "AGENTS.md"

    if dry_run:
        log(f"[DRY-RUN] Would write {agents_md_path}")
        print("\n--- Proposed AGENTS.md ---")
        print(agents_md_content)
    else:
        agents_md_path.write_text(agents_md_content, encoding="utf-8")
        log(f"Wrote {agents_md_path}")

    # Update Obsidian
    if args.obsidian or args.apply:
        write_obsidian_project_note(project_data, project_type, bundle)

    # Auto-update skills
    auto_update = gt_skills.get("auto_update", [])
    if auto_update and args.apply:
        log(f"Auto-updating skills: {auto_update}")
        update_skills_if_needed(auto_update, dry_run)

    # Summary
    summary = {
        "directory": str(directory),
        "project_type": project_type,
        "default_skills": gt_skills.get("default", []),
        "project_bundle": bundle,
        "agents_md": str(agents_md_path),
        "mode": "dry-run" if dry_run else "applied",
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
