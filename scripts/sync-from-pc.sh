#!/bin/bash
# sync-from-pc.sh — Pull WSL2 PC configs to Mac
# Usage: ./sync-from-pc.sh

set -e

PC_IP="192.168.68.113"
PC_PORT="2222"
PC_USER="gt"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

echo "=== Syncing PC → Mac ==="

# 1. Sync skills repo
echo "[1/5] Syncing skills repo..."
rsync -avz --delete -e "ssh $SSH_OPTS -p $PC_PORT" \
  $PC_USER@$PC_IP:/home/gt/agent-home/gt-core/skills-repo/ \
  /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/

# 2. Sync dashboard backend
echo "[2/5] Syncing dashboard backend..."
rsync -avz --delete --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
  -e "ssh $SSH_OPTS -p $PC_PORT" \
  $PC_USER@$PC_IP:/home/gt/agent-home/dashboard/backend/ \
  /Users/gt/Public/MyFiles/agent-home/dashboard/backend/

# 3. Sync dashboard frontend
echo "[3/5] Syncing dashboard frontend..."
rsync -avz --delete --exclude='node_modules' --exclude='dist' \
  -e "ssh $SSH_OPTS -p $PC_PORT" \
  $PC_USER@$PC_IP:/home/gt/agent-home/dashboard/frontend/ \
  /Users/gt/Public/MyFiles/agent-home/dashboard/frontend/

# 4. Sync vault
echo "[4/5] Syncing vault..."
rsync -avz --delete -e "ssh $SSH_OPTS -p $PC_PORT" \
  $PC_USER@$PC_IP:/home/gt/hermes-vault/ \
  /Users/gt/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/GT\ Vault/

# 5. Sync pi prompts/extensions (optional)
echo "[5/5] Syncing pi prompts..."
rsync -avz --delete -e "ssh $SSH_OPTS -p $PC_PORT" \
  $PC_USER@$PC_IP:/home/gt/.pi/agent/prompts/ \
  /Users/gt/.pi/agent/prompts/

echo "=== Sync complete ==="
