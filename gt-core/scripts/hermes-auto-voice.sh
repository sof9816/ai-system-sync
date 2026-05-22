#!/usr/bin/env bash
# GT Hermes Auto-Voice Launcher
# Automatically enables voice mode and fixes Gatekeeper-blocked portaudio
set -euo pipefail

# Fix 1: Redirect sounddevice to Homebrew's signed libportaudio
# (Gatekeeper blocks the bundled dylib with com.apple.provenance)
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_LIBRARY_PATH:-}"

# Fix 2: Launch Hermes via venv Python
exec /Users/gt/.hermes/hermes-agent/venv/bin/python3 -m hermes_cli.main "$@"
