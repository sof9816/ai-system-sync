#!/usr/bin/env python3
"""Validate a GT project manifest YAML file against the project manifest schema."""

import json
import sys
import os

import yaml
from jsonschema import validate, ValidationError, RefResolver


SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "schemas",
    "project-manifest-schema.json",
)


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest_path: str) -> int:
    schema = load_schema()
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {manifest_path}")
        return 1
    except yaml.YAMLError as exc:
        print(f"ERROR: Invalid YAML syntax: {exc}")
        return 1

    try:
        validate(instance=manifest, schema=schema)
    except ValidationError as exc:
        print(f"ERROR: Manifest validation failed: {exc.message}")
        print(f"  Path: {list(exc.path)}")
        print(f"  Schema path: {list(exc.schema_path)}")
        return 1

    print("OK: Manifest is valid.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-project.yaml>")
        sys.exit(1)

    sys.exit(validate_manifest(sys.argv[1]))
