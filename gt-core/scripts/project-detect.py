#!/usr/bin/env python3
"""
project-detect.py — Auto-detect project type and metadata.

Usage:
    python project-detect.py <directory> [--register]

1. Scans a directory for `.project.yaml`.
2. If found: reads, validates, prints info, returns JSON.
3. If not found: guesses project type from directory contents and suggests `.project.yaml`.
4. With --register: POSTs project details to dashboard API.
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Optional jsonschema validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Optional requests for --register
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

PROJECT_YAML_NAME = ".project.yaml"
DASHBOARD_API_URL = "http://localhost:7373/api/gt/projects"

PROJECT_SCHEMA = {
    "type": "object",
    "required": ["name", "type"],
    "properties": {
        "name": {"type": "string"},
        "type": {"type": "string"},
        "description": {"type": "string"},
        "skills": {
            "type": "array",
            "items": {"type": "string"},
        },
        "agents": {
            "type": "array",
            "items": {"type": "string"},
        },
        "version": {"type": "string"},
        "author": {"type": "string"},
    },
}

# File → project type mapping
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


def find_project_yaml(directory: Path) -> Optional[Path]:
    """Look for .project.yaml in the given directory."""
    candidate = directory / PROJECT_YAML_NAME
    if candidate.is_file():
        return candidate
    return None


def validate_yaml(data: dict) -> List[str]:
    """Validate project data; return list of error messages."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["Top-level YAML is not a mapping."]

    if HAS_JSONSCHEMA:
        try:
            jsonschema.validate(instance=data, schema=PROJECT_SCHEMA)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
    else:
        # Basic manual checks
        if "name" not in data:
            errors.append("Missing required field: 'name'")
        if "type" not in data:
            errors.append("Missing required field: 'type'")

    return errors


def detect_project_type(directory: Path) -> Optional[Dict[str, Any]]:
    """Guess project type by scanning directory contents."""
    detected: Dict[str, Any] = {}
    found_files: List[str] = []

    for root, dirs, files in os.walk(directory):
        # Skip common non-project directories
        dirs[:] = [d for d in dirs if d not in {"node_modules", "venv", ".git", "__pycache__", ".pytest_cache", "dist", "build", ".next"}]
        for filename, meta in FILE_TYPE_MAP.items():
            if filename in files:
                found_files.append(filename)
                # Merge metadata (first match wins for simple fields)
                if "type" not in detected:
                    detected["type"] = meta["type"]
                # Union skills and agents across all matches
                detected.setdefault("skills", set()).update(meta.get("skills", []))
                detected.setdefault("agents", set()).update(meta.get("agents", []))

    if not found_files:
        return None

    detected["skills"] = sorted(detected["skills"])
    detected["agents"] = sorted(detected["agents"])
    detected["detected_files"] = found_files
    return detected


def build_suggested_project_yaml(directory: Path) -> str:
    """Generate a suggested .project.yaml based on directory scan."""
    detection = detect_project_type(directory)
    if detection is None:
        return "# No recognizable project files found.\n# Please create a .project.yaml manually.\n"

    suggestion = {
        "name": directory.name or "unknown",
        "type": detection.get("type", "unknown"),
        "description": "Auto-detected project",
        "skills": detection.get("skills", []),
        "agents": detection.get("agents", []),
        "version": "0.1.0",
        "author": "",
    }
    return yaml.dump(suggestion, sort_keys=False, default_flow_style=False)


def read_project_yaml(path: Path) -> Dict[str, Any]:
    """Read and parse .project.yaml."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        data = {}
    return data


def print_project_info(data: dict, source: str) -> None:
    """Pretty-print project info."""
    print(f"Project source: {source}")
    print(f"  Name:        {data.get('name', 'N/A')}")
    print(f"  Type:        {data.get('type', 'N/A')}")
    print(f"  Description: {data.get('description', 'N/A')}")
    print(f"  Skills:      {', '.join(data.get('skills', [])) or 'N/A'}")
    print(f"  Agents:      {', '.join(data.get('agents', [])) or 'N/A'}")
    print(f"  Version:     {data.get('version', 'N/A')}")
    print(f"  Author:      {data.get('author', 'N/A')}")


def register_project(data: dict) -> bool:
    """POST project data to dashboard API."""
    if not HAS_REQUESTS:
        print("Error: 'requests' library is required for --register. Install it with: pip install requests")
        return False

    payload = {
        "path": str(Path(data.get("directory", ".")).resolve()),
        "name": data.get("name"),
        "type": data.get("type"),
        "description": data.get("description", ""),
        "skills": data.get("skills", []),
        "agents": data.get("agents", []),
        "version": data.get("version", ""),
        "author": data.get("author", ""),
    }

    try:
        resp = requests.post(DASHBOARD_API_URL, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            print(f"Successfully registered project at {DASHBOARD_API_URL}")
            return True
        else:
            print(f"Registration failed: HTTP {resp.status_code} — {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"Registration failed: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-detect project type and metadata.")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--register", action="store_true", help=f"POST project to {DASHBOARD_API_URL}")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}")
        return 1

    project_yaml = find_project_yaml(directory)

    if project_yaml:
        data = read_project_yaml(project_yaml)
        errors = validate_yaml(data)
        if errors:
            print("Validation errors:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print_project_info(data, str(project_yaml))
        result = dict(data)
    else:
        print(f"No {PROJECT_YAML_NAME} found in {directory}")
        detection = detect_project_type(directory)
        if detection:
            print("Guessed project type from directory contents:")
            print(f"  Detected files: {', '.join(detection['detected_files'])}")
            print(f"  Type:           {detection['type']}")
            print(f"  Skills:         {', '.join(detection['skills'])}")
            print(f"  Agents:         {', '.join(detection['agents'])}")
            suggestion = build_suggested_project_yaml(directory)
            print("\nSuggested .project.yaml content:")
            print("---")
            print(suggestion)
            result = {
                "directory": str(directory),
                "name": directory.name,
                "type": detection["type"],
                "description": "Auto-detected project",
                "skills": detection["skills"],
                "agents": detection["agents"],
                "version": "0.1.0",
                "author": "",
                "suggested_yaml": suggestion,
            }
        else:
            print("Could not guess project type. No recognizable files found.")
            result = {
                "directory": str(directory),
                "name": directory.name,
                "type": "unknown",
                "description": "",
                "skills": [],
                "agents": [],
                "version": "",
                "author": "",
            }

    # JSON output
    print("\n--- JSON output ---")
    print(json.dumps(result, indent=2))

    if args.register:
        print("\n--- Registering project ---")
        register_project(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
