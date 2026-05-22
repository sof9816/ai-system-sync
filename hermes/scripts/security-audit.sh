#!/bin/bash
REPORT="☠️ HERMES SECURITY AUDIT — $(date)\n"
CRIT=0
WARN=0
OK=0

# 1. Secret exposure in non-.env files (skip binaries, git, tests, sessions)
LEAKS=$(find ~/.hermes/ -type f \
  ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/state-snapshots/*" ! -path "*/skills.backup/*" \
  ! -name "*.db" ! -name "*.db-wal" ! -name "*.db-shm" ! -name "*.pack" ! -name "*.jsonl" \
  ! -name "*.json" ! -name ".hermes_history" ! -name "*.lock" \
  ! -name "*test*.py" ! -name "*test*.ts" ! -name "*test*.js" ! -name "tirith" \
  -exec grep -H -E '(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z_-]{35})' {} + 2>/dev/null | \
  grep -v '.env' | grep -v 'auth.json' | grep -v 'models_dev_cache' | \
  grep -v 'sk-xxx' | grep -v 'sk-test' | grep -v 'sk-abc' | grep -v 'ghp_xx' | head -10)
if [ -n "$LEAKS" ]; then
  REPORT+="\n[CRITICAL] Secrets found outside .env/auth.json:\n$LEAKS\n"
  ((CRIT++))
else
  REPORT+="\n[OK] No secrets leaked in plain files\n"
  ((OK++))
fi

# 2. .env permissions
ENV_PERMS=$(stat -f "%Lp" ~/.hermes/.env 2>/dev/null)
if [ "$ENV_PERMS" != "600" ]; then
  REPORT+="\n[WARN] ~/.hermes/.env permissions are $ENV_PERMS (should be 600)\n"
  ((WARN++))
else
  REPORT+="\n[OK] ~/.hermes/.env permissions are 600\n"
  ((OK++))
fi

# 3. Sensitive files in Public (GT-specific)
if [ -f ~/Public/MyFiles/99-Misc/tokens.json ]; then
  REPORT+="\n[CRITICAL] tokens.json exists in Public folder. Migrate to Keychain.\n"
  ((CRIT++))
else
  REPORT+="\n[OK] tokens.json not in Public\n"
  ((OK++))
fi

# 4. Cron audit
if [ -f ~/.hermes/cron/jobs.json ]; then
  CRON_COUNT=$(jq '.jobs | length' ~/.hermes/cron/jobs.json 2>/dev/null)
  REPORT+="\n[OK] $CRON_COUNT cron job(s) configured\n"
  ((OK++))
else
  REPORT+="\n[WARN] No cron jobs file found\n"
  ((WARN++))
fi

# 5. Gateway exposure
GATEWAY_HOST=$(grep -A2 'gateway:' ~/.hermes/config.yaml 2>/dev/null | grep 'host:' | awk '{print $2}')
if [ "$GATEWAY_HOST" = "0.0.0.0" ]; then
  REPORT+="\n[WARN] Gateway bound to 0.0.0.0 — verify intentional\n"
  ((WARN++))
else
  REPORT+="\n[OK] Gateway not openly exposed\n"
  ((OK++))
fi

REPORT+="\nSummary: $CRIT critical, $WARN warnings, $OK passed\n"
echo -e "$REPORT"
