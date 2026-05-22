#!/bin/bash
# AI System Sync — Master sync script for GT's AI infrastructure
# Runs on both Mac and PC. Syncs configs, skills, agents, and Obsidian settings.
# Git is the source of truth. Local changes are stashed, pulled, then applied.

set -euo pipefail

REPO_URL="https://github.com/sof9816/ai-system-sync.git"
SYNC_DIR="${HOME}/.ai-system-sync"
LOG_FILE="${SYNC_DIR}/sync.log"
PLATFORM="$(uname -s)"
HOSTNAME="$(hostname -s)"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[SYNC]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERR]${NC} $1" | tee -a "$LOG_FILE"
}

init_repo() {
    if [[ ! -d "$SYNC_DIR/.git" ]]; then
        log "First run — cloning sync repo..."
        rm -rf "$SYNC_DIR"
        git clone "$REPO_URL" "$SYNC_DIR"
    fi
    cd "$SYNC_DIR"
    git config user.email "gt-sync@local"
    git config user.name "GT Sync Bot"
}

sync_to_local() {
    log "Pulling latest from GitHub ($PLATFORM / $HOSTNAME)..."
    cd "$SYNC_DIR"
    git stash push -m "auto-stash-$HOSTNAME-$(date +%s)" || true
    git pull --rebase origin main || git pull origin main || true
    git stash pop || true
}

sync_from_local() {
    log "Pushing local changes to GitHub..."
    cd "$SYNC_DIR"
    git add -A
    if git diff --cached --quiet; then
        log "No local changes to push."
        return 0
    fi
    git commit -m "sync: $HOSTNAME @ $TIMESTAMP" || true
    git push origin main || warn "Push failed — may need manual resolution"
}

copy_configs_to_repo() {
    log "Copying local configs into sync repo..."

    # Hermes
    mkdir -p "$SYNC_DIR/hermes"
    if [[ -f "$HOME/.hermes/config.yaml" ]]; then
        cp "$HOME/.hermes/config.yaml" "$SYNC_DIR/hermes/"
    fi
    if [[ -f "$HOME/.hermes/config.json" ]]; then
        cp "$HOME/.hermes/config.json" "$SYNC_DIR/hermes/"
    fi
    if [[ -d "$HOME/.hermes/scripts" ]]; then
        mkdir -p "$SYNC_DIR/hermes/scripts"
        cp -R "$HOME/.hermes/scripts/"* "$SYNC_DIR/hermes/scripts/" 2>/dev/null || true
    fi

    # pi.dev (skills symlink already handled by skills-repo)
    # Just capture any pi-specific config if it exists
    mkdir -p "$SYNC_DIR/pi"
    if [[ -f "$HOME/.pi/config.json" ]]; then
        cp "$HOME/.pi/config.json" "$SYNC_DIR/pi/"
    fi
    if [[ -f "$HOME/.agents/config.json" ]]; then
        cp "$HOME/.agents/config.json" "$SYNC_DIR/pi/"
    fi

    # GT Dashboard agents
    mkdir -p "$SYNC_DIR/gt-dashboard"
    if [[ -d "$HOME/Public/MyFiles/agent-home/agents" ]]; then
        cp -R "$HOME/Public/MyFiles/agent-home/agents/"* "$SYNC_DIR/gt-dashboard/" 2>/dev/null || true
    fi

    # Obsidian vault configs (not the vault itself — too big, uses iCloud)
    mkdir -p "$SYNC_DIR/obsidian"
    HERMES_VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes/Hermes"
    if [[ -d "$HERMES_VAULT/.obsidian" ]]; then
        mkdir -p "$SYNC_DIR/obsidian/hermes-vault-config"
        cp -R "$HERMES_VAULT/.obsidian/"* "$SYNC_DIR/obsidian/hermes-vault-config/" 2>/dev/null || true
    fi
    GT_VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault"
    if [[ -d "$GT_VAULT/.obsidian" ]]; then
        mkdir -p "$SYNC_DIR/obsidian/gt-vault-config"
        cp -R "$GT_VAULT/.obsidian/"* "$SYNC_DIR/obsidian/gt-vault-config/" 2>/dev/null || true
    fi
}

copy_configs_from_repo() {
    log "Applying synced configs to local system..."

    # Hermes
    if [[ -f "$SYNC_DIR/hermes/config.yaml" ]]; then
        mkdir -p "$HOME/.hermes"
        cp "$SYNC_DIR/hermes/config.yaml" "$HOME/.hermes/config.yaml"
    fi
    if [[ -f "$SYNC_DIR/hermes/config.json" ]]; then
        cp "$SYNC_DIR/hermes/config.json" "$HOME/.hermes/config.json"
    fi
    if [[ -d "$SYNC_DIR/hermes/scripts" ]]; then
        mkdir -p "$HOME/.hermes/scripts"
        cp -R "$SYNC_DIR/hermes/scripts/"* "$HOME/.hermes/scripts/" 2>/dev/null || true
    fi

    # pi.dev
    if [[ -f "$SYNC_DIR/pi/config.json" ]]; then
        mkdir -p "$HOME/.pi"
        cp "$SYNC_DIR/pi/config.json" "$HOME/.pi/config.json" 2>/dev/null || true
    fi
    if [[ -f "$SYNC_DIR/pi/config.json" ]]; then
        mkdir -p "$HOME/.agents"
        cp "$SYNC_DIR/pi/config.json" "$HOME/.agents/config.json" 2>/dev/null || true
    fi

    # GT Dashboard
    if [[ -d "$SYNC_DIR/gt-dashboard" ]]; then
        mkdir -p "$HOME/Public/MyFiles/agent-home/agents"
        cp -R "$SYNC_DIR/gt-dashboard/"* "$HOME/Public/MyFiles/agent-home/agents/" 2>/dev/null || true
    fi

    # Obsidian configs
    HERMES_VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes/Hermes"
    if [[ -d "$SYNC_DIR/obsidian/hermes-vault-config" && -d "$HERMES_VAULT" ]]; then
        cp -R "$SYNC_DIR/obsidian/hermes-vault-config/"* "$HERMES_VAULT/.obsidian/" 2>/dev/null || true
    fi
    GT_VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault"
    if [[ -d "$SYNC_DIR/obsidian/gt-vault-config" && -d "$GT_VAULT" ]]; then
        cp -R "$SYNC_DIR/obsidian/gt-vault-config/"* "$GT_VAULT/.obsidian/" 2>/dev/null || true
    fi
}

main() {
    mkdir -p "$SYNC_DIR"
    touch "$LOG_FILE"
    log "========== AI System Sync Started =========="
    log "Platform: $PLATFORM | Host: $HOSTNAME"

    init_repo
    sync_to_local
    copy_configs_to_repo
    sync_from_local
    copy_configs_from_repo

    log "========== AI System Sync Complete =========="
}

main "$@"
