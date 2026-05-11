#!/usr/bin/env python3
"""
pi-start.py — Smart pi.dev launcher with auto-detected skills.

Usage:
    pi-start [extra_args...]

1. Detects project type from cwd or .project.yaml
2. Reads gt-config.yaml for default skills + project bundles
3. Launches pi with --skill flags automatically
"""

import json
import os
import subprocess
import sys
from pathlib import Path

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
CONFIG_PATH = AGENT_HOME / "gt-core/config/gt-config.yaml"
PI_BIN = Path("/opt/homebrew/bin/pi")

# File → project type mapping
FILE_TYPE_MAP = {
    "Package.swift": "ios",
    "pubspec.yaml": "flutter",
    "package.json": "node",
    "requirements.txt": "python",
    "setup.py": "python",
    "pyproject.toml": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "pom.xml": "java",
    "build.gradle": "java",
    "CMakeLists.txt": "cpp",
    "Makefile": "c",
    "Gemfile": "ruby",
    "composer.json": "php",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
}


def load_yaml_fallback(path: Path) -> dict:
    """Load YAML, falling back to venv python if pyyaml missing."""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        venv_python = AGENT_HOME / "dashboard/backend/venv/bin/python3"
        if venv_python.exists():
            result = subprocess.run(
                [str(venv_python), "-c",
                 f"import yaml, json; print(json.dumps(yaml.safe_load(open('{path}')) or {{}}))"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        return {}


def detect_project_type(directory: Path) -> str:
    """Guess project type from directory contents."""
    # Check .project.yaml first
    project_yaml = directory / ".project.yaml"
    if project_yaml.exists():
        try:
            data = load_yaml_fallback(project_yaml)
            if data.get("type"):
                return data["type"]
        except Exception:
            pass

    # Scan files
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", "venv", ".git", "__pycache__",
            ".pytest_cache", "dist", "build", ".next",
            "DerivedData", ".build", "Pods", ".swiftpm"
        }]
        for filename, ptype in FILE_TYPE_MAP.items():
            if filename in files:
                return ptype
    return "unknown"


def build_skill_args(gt: dict, project_type: str) -> list[str]:
    """Build --skill flags from config."""
    skills_config = gt.get("skills", {})
    default_skills = skills_config.get("default", [])
    project_bundles = skills_config.get("project_bundles", {})
    bundle = project_bundles.get(project_type, [])

    # Combine defaults + bundle, deduplicate, preserve order
    all_skills = list(dict.fromkeys(default_skills + bundle))

    args = []
    for skill in all_skills:
        args.extend(["--skill", skill])
    return args


def main() -> int:
    # Manual arg parsing so --flags go to pi, not us
    no_auto_skills = "--no-auto-skills" in sys.argv
    extra_args = [a for a in sys.argv[1:] if a != "--no-auto-skills"]

    cwd = Path.cwd()
    gt = load_yaml_fallback(CONFIG_PATH)

    if not no_auto_skills:
        project_type = detect_project_type(cwd)
        skill_args = build_skill_args(gt, project_type)
        if skill_args:
            print(f"[pi-start] Detected project type: {project_type}")
            print(f"[pi-start] Auto-loading skills: {', '.join(skill_args[i+1] for i in range(0, len(skill_args), 2))}")
    else:
        skill_args = []

    # Build pi command
    pi_cmd = [str(PI_BIN)]
    pi_cmd.extend(skill_args)
    pi_cmd.extend(extra_args)

    # Exec pi (replaces this process)
    os.execv(str(PI_BIN), pi_cmd)
    return 0  # unreachable


if __name__ == "__main__":
    sys.exit(main())
