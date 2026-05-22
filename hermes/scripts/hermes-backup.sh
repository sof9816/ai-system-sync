#!/bin/bash
set -e
REPO="/Users/gt/Public/MyFiles/agent-home/gt-core"
SKILLS="$REPO/skills-repo"
STATE="$REPO/hermes-state"

# Backup skills
cd "$SKILLS"
git add -A
git diff --cached --quiet || git commit -m "auto: skills $(date +%Y-%m-%d-%H:%M)"
git push origin main || true

# Backup state
mkdir -p "$STATE"
cp ~/.hermes/memories/*.md "$STATE/"
cp ~/.hermes/SOUL.md "$STATE/"
grep -v -E '(api_key|token|secret|password|credential)' ~/.hermes/config.yaml > "$STATE/config.yaml"

cd "$REPO"
git add -A
git diff --cached --quiet || git commit -m "auto: hermes state $(date +%Y-%m-%d-%H:%M)"
git push origin main || true

echo "Backup complete at $(date)"
