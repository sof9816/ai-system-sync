#!/bin/bash
# Zone Dispatch — Daily Build & Deploy (ultra-fast)
# Uses pre-built dist/ + only updates data

set -e

PROJECT_DIR="/Users/gt/Public/MyFiles/08-Web-Node/newsletter-mvp"
LOG_FILE="/Users/gt/.hermes/cron/output/zone-dispatch-deploy.log"
PUBLIC_URL="https://newsletter-mvp-rho.vercel.app"
FULL_URL="https://newsletter-mvp-rho.vercel.app/full"

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

# Step 4: Deploy (npx --no-install skips registry checks that can hang)
echo "[$(date)] Deploying..." >> "$LOG_FILE"

# macOS has no 'timeout' — use perl alarm. Vercel deploy can take 2-3 min.
perl -e 'alarm shift; exec @ARGV' 180 npx --no-install vercel deploy --prod --yes --cwd "$PROJECT_DIR" >> "$LOG_FILE" 2>&1 || {
    echo "[$(date)] Deploy failed or timed out" >> "$LOG_FILE"
    exit 1
}

echo "[$(date)] Done" >> "$LOG_FILE"

# Step 5: Collect build artifacts with links
BUILD_OUTPUT=$(cat <<EOF
Zone Dispatch deployed!

Public (free): $PUBLIC_URL
Full (paid): $FULL_URL

Build artifacts:
EOF
)

# Add links to each dist file
for file in "$PROJECT_DIR"/dist/assets/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        size=$(du -h "$file" | cut -f1)
        BUILD_OUTPUT="$BUILD_OUTPUT
- [$filename]($PUBLIC_URL/assets/$filename) — $size"
    fi
done

# Add index.html
BUILD_OUTPUT="$BUILD_OUTPUT
- [index.html]($PUBLIC_URL/index.html) — $(du -h "$PROJECT_DIR/dist/index.html" | cut -f1)"

echo "$BUILD_OUTPUT" > /tmp/zone-dispatch-links.txt

# Output to stdout for cron delivery
echo "$BUILD_OUTPUT"

# Try to send via Telegram bot if configured
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "parse_mode=Markdown" \
        -d "text=Zone Dispatch deployed!%0A%0A🌐 Public (free): $PUBLIC_URL%0A🔒 Full (paid): $FULL_URL%0A%0A✅ Build: SUCCESS%0A📦 Deploy: SUCCESS" \
        > /dev/null 2>&1 || true
fi

echo "[$(date)] Links sent" >> "$LOG_FILE"