#!/usr/bin/env bash
# GT Hermes Launcher — auto-fixes voice mode and auto-enables it on startup
# Path: /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/hermes-launcher.sh

set -euo pipefail

# ── 1. Fix sounddevice / Gatekeeper issue ────────────────────────────────
# macOS Gatekeeper blocks the bundled libportaudio.dylib with com.apple.provenance.
# SIP prevents removing that xattr, so we redirect sounddevice to Homebrew's
# signed library via DYLD_LIBRARY_PATH.
HOMEBREW_PORTAUDIO="/opt/homebrew/lib/libportaudio.dylib"
if [[ -f "$HOMEBREW_PORTAUDIO" ]]; then
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_LIBRARY_PATH:-}"
fi

# ── 2. Launch Hermes via the official entry point ────────────────────────
# We invoke the venv Python directly so the env var is inherited.
exec /Users/gt/.hermes/hermes-agent/venv/bin/python3 -m hermes_cli.main "$@"
