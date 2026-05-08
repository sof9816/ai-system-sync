#!/usr/bin/env python3
"""Switch AI provider with rollback support."""
import sqlite3, json, os, sys, shutil, datetime, urllib.request
from pathlib import Path

CONFIG_PATH = Path("/Users/gt/Public/MyFiles/agent-home/gt-core/config/gt-config.yaml")
DB_PATH = Path.home() / "Public/MyFiles/agent-home/dashboard/backend/data/app.db"
HERMES_CFG = Path.home() / ".hermes/config.yaml"
PI_CFG = Path.home() / ".pi/agent/settings.json"
VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault/hermes/system/provider-switches.md"

log = lambda **kw: print(json.dumps({"ts": datetime.datetime.now().isoformat(), **kw}))

def parse_yaml(path):
    cfg, section = {}, None
    for line in open(path):
        s = line.lstrip()
        if s.startswith("#") or not s.strip(): continue
        indent = len(line) - len(s)
        if indent == 0 and s.rstrip().endswith(":"):
            section = s.rstrip()[:-1]
            cfg[section] = {}
        elif section and ":" in s:
            k, v = s.split(":", 1)
            cfg[section][k.strip()] = v.strip()
    return cfg

def backup(p):
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    bak = Path(str(p) + f".bak.{ts}")
    shutil.copy2(p, bak)
    log(event="backup", file=str(p), backup=str(bak))
    return bak

def read_secrets(provider):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT * FROM gt_secrets WHERE provider = ?", (provider,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

def set_status(provider, status):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("UPDATE gt_secrets SET status = ? WHERE provider = ?", (status, provider))
    conn.commit(); conn.close()
    log(event="status_change", provider=provider, status=status)

def test_key(base_url, key):
    req = urllib.request.Request(f"{base_url}/v1/models", headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        log(event="test_fail", error=str(e))
        return False

def replace_line(path, prefix, new_line, dry_run=False):
    lines = open(path).readlines()
    out = []
    for line in lines:
        if line.lstrip().startswith(prefix):
            out.append(new_line + "\n")
        else:
            out.append(line)
    if not dry_run:
        with open(path, "w") as f:
            f.writelines(out)
    log(event="edit", file=str(path), line=new_line.strip(), dry_run=dry_run)

def append_vault(summary):
    VAULT.parent.mkdir(parents=True, exist_ok=True)
    with open(VAULT, "a") as f:
        f.write(f"\n- {datetime.datetime.now().isoformat()}: {summary}\n")
    log(event="vault_append", file=str(VAULT))

def switch_provider(new_provider, dry_run=False):
    log(event="start", provider=new_provider, dry_run=dry_run)
    cfg = parse_yaml(CONFIG_PATH)
    providers = cfg.get("providers", {})
    if new_provider not in providers:
        log(event="error", msg="unknown provider"); return False
    base_url = providers[new_provider].get("base_url", "")
    env_key = providers[new_provider].get("api_key_env", "")
    api_key = os.environ.get(env_key, "")
    secrets = read_secrets(new_provider)
    active = [s for s in secrets if s.get("status") == "active"]
    if active:
        api_key = active[0].get("api_key", api_key)
    if not api_key:
        log(event="error", msg="no api key"); return False
    current = cfg.get("ai", {}).get("primary_provider", "")
    if not dry_run:
        backup(HERMES_CFG); backup(PI_CFG)
        if current: set_status(current, "standby")
        set_status(new_provider, "active")
    replace_line(HERMES_CFG, "provider:", f"  provider: {new_provider}", dry_run)
    replace_line(HERMES_CFG, "default:", f"  default: {cfg.get('ai',{}).get('model','')}", dry_run)
    replace_line(PI_CFG, "defaultProvider", f'  "defaultProvider": "{new_provider}"', dry_run)
    replace_line(PI_CFG, "defaultModel", f'  "defaultModel": "{cfg.get("ai",{}).get("model","")}"', dry_run)
    if test_key(base_url, api_key):
        log(event="test_pass")
        append_vault(f"Switched to {new_provider} (dry_run={dry_run})")
        return True
    log(event="test_fail", msg="rolling back")
    if not dry_run:
        set_status(new_provider, "standby")
        if current: set_status(current, "active")
        # restore backups
        for bak in sorted(Path.home().glob(".hermes/config.yaml.bak.*"), reverse=True)[:1]:
            shutil.copy2(bak, HERMES_CFG)
        for bak in sorted(Path.home().glob(".pi/agent/settings.json.bak.*"), reverse=True)[:1]:
            shutil.copy2(bak, PI_CFG)
        log(event="rollback")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: switch-provider.py <provider> [--dry-run]"); sys.exit(1)
    provider = sys.argv[1]
    dry = "--dry-run" in sys.argv
    ok = switch_provider(provider, dry)
    sys.exit(0 if ok else 1)
