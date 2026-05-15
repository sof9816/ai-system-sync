#!/bin/bash
# sync-to-pc.sh — Push Mac configs to WSL2 PC
# Usage: ./sync-to-pc.sh

set -e

PC_IP="192.168.68.113"
PC_PORT="2222"
PC_USER="gt"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

echo "=== Syncing Mac → PC ==="

# 1. Sync skills repo
echo "[1/6] Syncing skills repo..."
rsync -avz --delete -e "ssh $SSH_OPTS -p $PC_PORT" \
  /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/ \
  $PC_USER@$PC_IP:/home/gt/agent-home/gt-core/skills-repo/

# 2. Sync dashboard backend (excluding venv, node_modules, data)
echo "[2/6] Syncing dashboard backend..."
rsync -avz --delete --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
  -e "ssh $SSH_OPTS -p $PC_PORT" \
  /Users/gt/Public/MyFiles/agent-home/dashboard/backend/ \
  $PC_USER@$PC_IP:/home/gt/agent-home/dashboard/backend/

# 3. Sync dashboard frontend (excluding node_modules)
echo "[3/6] Syncing dashboard frontend..."
rsync -avz --delete --exclude='node_modules' --exclude='dist' \
  -e "ssh $SSH_OPTS -p $PC_PORT" \
  /Users/gt/Public/MyFiles/agent-home/dashboard/frontend/ \
  $PC_USER@$PC_IP:/home/gt/agent-home/dashboard/frontend/

# 4. Sync hermes config
echo "[4/6] Syncing hermes config..."
scp $SSH_OPTS -P $PC_PORT \
  /Users/gt/.hermes/config.yaml \
  /Users/gt/.hermes/.env \
  $PC_USER@$PC_IP:/home/gt/.hermes/

# 5. Sync pi config
echo "[5/6] Syncing pi config..."
scp $SSH_OPTS -P $PC_PORT \
  /Users/gt/.pi/agent/settings.json \
  $PC_USER@$PC_IP:/home/gt/.pi/agent/

# 6. Sync vault
echo "[6/6] Syncing vault..."
rsync -avz --delete -e "ssh $SSH_OPTS -p $PC_PORT" \
  /Users/gt/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/GT\ Vault/ \
  $PC_USER@$PC_IP:/home/gt/hermes-vault/

echo "=== Sync complete ==="
