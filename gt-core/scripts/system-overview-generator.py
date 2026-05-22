#!/usr/bin/env python3
"""
GT System Overview Generator
Scans all components and generates a comprehensive system health report.
Updates Obsidian vault with current status.
"""
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

HERMES_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes/Hermes"
AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
DASHBOARD_DB = AGENT_HOME / "dashboard/backend/data/app.db"

def run_cmd(cmd, timeout=10):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        return type('obj', (object,), {'stdout': '', 'stderr': str(e), 'returncode': -1})()

def check_hermes():
    r = run_cmd("hermes --version 2>/dev/null")
    version = r.stdout.strip() if r.returncode == 0 else "NOT RUNNING"
    
    # Check voice config
    config_path = Path.home() / ".hermes/config.yaml"
    voice_enabled = False
    if config_path.exists():
        text = config_path.read_text()
        voice_enabled = "stt:" in text and "enabled: true" in text
    
    return {
        "status": "healthy" if r.returncode == 0 else "down",
        "version": version,
        "voice_configured": voice_enabled,
        "voice_auto_enabled": True,  # We patched cli.py
        "config_path": str(config_path),
    }

def check_pi():
    r = run_cmd("pi --version 2>/dev/null")
    version = r.stdout.strip() if r.returncode == 0 else "NOT RUNNING"
    
    # Check pi settings
    settings_path = Path.home() / ".pi/agent/settings.json"
    provider = "unknown"
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text())
            provider = data.get("provider", "unknown")
        except:
            pass
    
    return {
        "status": "healthy" if r.returncode == 0 else "down",
        "version": version,
        "provider": provider,
        "settings_path": str(settings_path),
    }

def check_dashboard():
    r = run_cmd("curl -s http://localhost:7373/api/health 2>/dev/null | head -1")
    healthy = r.returncode == 0 and ("ok" in r.stdout.lower() or "{" in r.stdout)
    
    db_size = 0
    if DASHBOARD_DB.exists():
        db_size = DASHBOARD_DB.stat().st_size
    
    return {
        "status": "healthy" if healthy else "down",
        "health_response": r.stdout.strip(),
        "db_size_mb": round(db_size / 1024 / 1024, 2),
        "db_path": str(DASHBOARD_DB),
    }

def check_obsidian():
    vault = HERMES_VAULT
    note_count = 0
    if vault.exists():
        note_count = len(list(vault.rglob("*.md")))
    
    return {
        "status": "healthy" if vault.exists() else "missing",
        "vault_path": str(vault),
        "note_count": note_count,
    }

def check_pc():
    r = run_cmd("ssh -o ConnectTimeout=3 -p 2222 gt@192.168.68.113 'echo PC_OK' 2>/dev/null")
    reachable = "PC_OK" in r.stdout
    
    return {
        "status": "connected" if reachable else "offline",
        "ip": "192.168.68.113",
        "ssh_port": 2222,
        "last_check": datetime.now().isoformat(),
    }

def check_github():
    r = run_cmd("gh auth status 2>/dev/null")
    authed = r.returncode == 0
    
    # Check repos
    repos = ["ai-skills"]
    repo_status = {}
    for repo in repos:
        r2 = run_cmd(f"gh repo view sof9816/{repo} --json name 2>/dev/null")
        repo_status[repo] = "exists" if r2.returncode == 0 else "missing"
    
    return {
        "status": "authenticated" if authed else "not_authed",
        "repos": repo_status,
    }

def get_projects():
    projects = []
    
    # From dashboard DB
    if DASHBOARD_DB.exists():
        try:
            conn = sqlite3.connect(str(DASHBOARD_DB))
            cursor = conn.cursor()
            cursor.execute("SELECT name, type, status, last_activity FROM projects")
            for row in cursor.fetchall():
                projects.append({
                    "name": row[0], "type": row[1], "status": row[2],
                    "source": "dashboard_db", "last_activity": row[3]
                })
            conn.close()
        except:
            pass
    
    # From .project.yaml files
    for yaml_file in AGENT_HOME.rglob(".project.yaml"):
        try:
            content = yaml_file.read_text()
            name = "unknown"
            for line in content.split("\n"):
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                    break
            projects.append({
                "name": name, "type": "unknown", "status": "active",
                "source": str(yaml_file.parent), "last_activity": "unknown"
            })
        except:
            pass
    
    # From Obsidian project folders
    projects_dir = HERMES_VAULT / "03 Projects"
    if projects_dir.exists():
        for folder in projects_dir.iterdir():
            if folder.is_dir():
                projects.append({
                    "name": folder.name, "type": "obsidian", "status": "active",
                    "source": str(folder), "last_activity": "unknown"
                })
    
    return projects

def generate_overview():
    overview = {
        "generated_at": datetime.now().isoformat(),
        "hermes": check_hermes(),
        "pi_dev": check_pi(),
        "dashboard": check_dashboard(),
        "obsidian": check_obsidian(),
        "pc": check_pc(),
        "github": check_github(),
        "projects": get_projects(),
    }
    return overview

def save_to_obsidian(overview):
    output_path = HERMES_VAULT / "00 Inbox/System Overview.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    md = f"""# GT System Overview

> Generated: {overview['generated_at']}
> Auto-refresh: Run `python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/system-overview-generator.py`

---

## System Health Dashboard

| Component | Status | Details |
|-----------|--------|---------|
| Hermes | {overview['hermes']['status']} | Version: {overview['hermes']['version']} |
| pi.dev | {overview['pi_dev']['status']} | Provider: {overview['pi_dev']['provider']} |
| Dashboard | {overview['dashboard']['status']} | DB: {overview['dashboard']['db_size_mb']} MB |
| Obsidian | {overview['obsidian']['status']} | Notes: {overview['obsidian']['note_count']} |
| PC (WSL2) | {overview['pc']['status']} | IP: {overview['pc']['ip']} |
| GitHub | {overview['github']['status']} | Repos: {', '.join(overview['github']['repos'].keys())} |

---

## Projects

| Project | Type | Status | Source |
|---------|------|--------|--------|
"""
    for p in overview['projects']:
        md += f"| {p['name']} | {p['type']} | {p['status']} | {p['source']} |\n"
    
    md += """
---

## Current Blockers

"""
    blockers = []
    if overview['hermes']['status'] != 'healthy':
        blockers.append("- Hermes is not running")
    if overview['dashboard']['status'] != 'healthy':
        blockers.append("- Dashboard backend is down")
    if overview['pc']['status'] != 'connected':
        blockers.append("- PC (WSL2) is offline — sync may be stale")
    
    if blockers:
        md += "\n".join(blockers) + "\n"
    else:
        md += "No critical blockers detected.\n"
    
    md += """
---

## Recommended Next Actions

1. [ ] Run dashboard health check
2. [ ] Sync skills repo to PC if online
3. [ ] Review pending projects in Obsidian
4. [ ] Check Telegram bot for new messages

---

*This file is auto-generated. Do not edit manually — it will be overwritten.*
"""
    
    output_path.write_text(md)
    print(f"Saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    overview = generate_overview()
    path = save_to_obsidian(overview)
    print(json.dumps(overview, indent=2, default=str))
