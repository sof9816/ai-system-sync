#!/bin/bash
# Zone Dispatch — Daily Build & Deploy (ultra-fast)
# Uses pre-built dist/ + only updates data

set -e

PROJECT_DIR="/Users/gt/Public/MyFiles/08-Web-Node/newsletter-mvp"
LOG_FILE="/Users/gt/.hermes/cron/output/zone-dispatch-deploy.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting..." > "$LOG_FILE"

cd "$PROJECT_DIR"

# Step 1: Regenerate digest.json
LATEST_DIGEST=$(ls -t ~/.hermes/cron/output/9a2440921b32/*.md 2>/dev/null | head -1)
if [ -n "$LATEST_DIGEST" ]; then
    /opt/homebrew/bin/python3.11 scripts/generate-digest.py < "$LATEST_DIGEST" > src/data/digest.json 2>> "$LOG_FILE"
    echo "[$(date)] digest.json done" >> "$LOG_FILE"
else
    echo "[$(date)] No digest found" >> "$LOG_FILE"
    exit 1
fi

# Step 2: Copy digest.json to public/ for runtime fetch
cp src/data/digest.json public/digest.json

# Step 3: Quick build (Vite only, skip tsc type check)
echo "[$(date)] Building..." >> "$LOG_FILE"
npx vite build --emptyOutDir 2>> "$LOG_FILE"
echo "[$(date)] Build done" >> "$LOG_FILE"

# Step 4: Deploy
echo "[$(date)] Deploying..." >> "$LOG_FILE"
npx vercel@latest deploy --prod --yes --cwd "$PROJECT_DIR" 2>> "$LOG_FILE" || true

echo "[$(date)] Done" >> "$LOG_FILE"
