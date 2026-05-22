#!/usr/bin/env python3
"""
GT Auto-Sync Agent
Runs periodically to:
1. Update System Overview in Obsidian
2. Sync skills repo to GitHub
3. Check PC connectivity and sync if online
4. Scan for new projects and update index
"""
import subprocess, json, sys
from pathlib import Path
from datetime import datetime

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
LOG_FILE = AGENT_HOME / "logs/auto-sync.log"

def log(msg):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    print(msg)

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout, r.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    log("=== Auto-Sync Agent Starting ===")
    
    # 1. Update System Overview
    ok, out, err = run("python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/system-overview-generator.py")
    log(f"System Overview: {'OK' if ok else 'FAILED'} {err[:100] if err else ''}")
    
    # 2. Sync skills repo to GitHub
    skills_repo = AGENT_HOME / "gt-core/skills-repo"
    if skills_repo.exists():
        ok, out, err = run(f"cd {skills_repo} && git add -A && git diff --cached --quiet || git commit -m 'auto-sync: {datetime.now().isoformat()}' && git push origin main", timeout=60)
        log(f"Skills sync: {'OK' if ok else 'FAILED'} {err[:100] if err else ''}")
    
    # 3. Check PC and sync if online
    ok, out, err = run("ssh -o ConnectTimeout=5 -p 2222 gt@192.168.68.113 'echo PC_ONLINE' 2>/dev/null")
    if ok and "PC_ONLINE" in out:
        log("PC is ONLINE — syncing...")
        # Sync skills to PC
        ok, out, err = run("rsync -avz --delete /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/ gt@192.168.68.113:~/skills-repo/ 2>/dev/null", timeout=120)
        log(f"PC sync: {'OK' if ok else 'FAILED'}")
    else:
        log("PC is OFFLINE — skipping sync")
    
    log("=== Auto-Sync Complete ===")

if __name__ == "__main__":
    main()
