#!/usr/bin/env python3
"""Validate a gt-config.yaml against the gt-config-schema.json."""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema is required. Install with: pip install jsonschema")
    sys.exit(1)


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "config" / "schemas" / "gt-config-schema.json"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "gt-config.yaml"


def validate(config_path: Path, schema_path: Path = SCHEMA_PATH) -> int:
    """Validate config file against schema. Returns 0 if valid, 1 otherwise."""
    if not schema_path.exists():
        print(f"Error: Schema not found: {schema_path}")
        return 1
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}")
        return 1

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Error: Failed to parse YAML: {exc}")
            return 1

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(config), key=lambda e: e.path)

    if not errors:
        print(f"OK: {config_path} is valid against {schema_path}")
        return 0

    print(f"FAIL: {config_path} has {len(errors)} validation error(s):")
    for idx, error in enumerate(errors, start=1):
        path = "/".join(str(p) for p in error.path) or "<root>"
        print(f"  {idx}. [{path}] {error.message}")
    return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate GT config YAML against JSON schema.")
    parser.add_argument("config", nargs="?", type=Path, default=DEFAULT_CONFIG_PATH,
                        help="Path to gt-config.yaml (default: %(default)s)")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH,
                        help="Path to JSON schema (default: %(default)s)")
    args = parser.parse_args()

    sys.exit(validate(args.config, args.schema))
