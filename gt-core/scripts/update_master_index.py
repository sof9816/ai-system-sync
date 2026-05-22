#!/usr/bin/env python3
"""
Master System Index Auto-Updater
================================
Scans the entire GT AI ecosystem and updates the Master System Index in Obsidian.

Sources scanned:
- Hermes Vault (all .md files)
- GT Vault (all .md files)
- Dashboard SQLite DB (projects, sessions, configs)
- Skills repo (SKILL.md files)
- Hermes config (~/.hermes/config.yaml)
- pi.dev config (~/.pi/agent/settings.json)
- Cron jobs (hermes cron list)
- Session logs (dashboard/data/sessions/)

Usage:
    python3 update_master_index.py              # Run once
    python3 update_master_index.py --daemon     # Run every 6 hours
    python3 update_master_index.py --watch      # Watch for file changes

Cron setup:
    0 */6 * * * /opt/homebrew/bin/python3.11 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/update_master_index.py
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ── Configuration ───────────────────────────────────────────────────────────

HERMES_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes/Hermes"
GT_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault"
SKILLS_REPO = Path.home() / "Public/MyFiles/agent-home/gt-core/skills-repo"
DASHBOARD_DB = Path.home() / "Public/MyFiles/agent-home/dashboard/data/dashboard.db"
SCRIPT_DIR = Path(__file__).parent.resolve()
INDEX_PATH = HERMES_VAULT / "00 Inbox/Master System Index.md"

HERMES_CONFIG = Path.home() / ".hermes/config.yaml"
PI_CONFIG = Path.home() / ".pi/agent/settings.json"
PI_AUTH = Path.home() / ".pi/agent/auth.json"
HERMES_ENV = Path.home() / ".hermes/.env"

# ── Helpers ─────────────────────────────────────────────────────────────────


def run_cmd(cmd: list[str], timeout: int = 30) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def file_mtime(path: Path) -> str:
    if path.exists():
        return datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    return "N/A"


def count_skills() -> tuple[int, list[tuple[str, str]]]:
    skills: list[tuple[str, str]] = []
    if not SKILLS_REPO.exists():
        return 0, skills
    for skill_file in SKILLS_REPO.rglob("SKILL.md"):
        rel = skill_file.relative_to(SKILL_DIR := SKILLS_REPO)
        category = rel.parts[0] if len(rel.parts) > 1 else "root"
        skills.append((category, str(rel)))
    return len(skills), skills


def scan_vault_md_files(vault: Path) -> list[Path]:
    if not vault.exists():
        return []
    return list(vault.rglob("*.md"))


def read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
        import yaml

        return yaml.safe_load(text[3:end]) or {}
    except Exception:
        return {}


def query_dashboard_db() -> dict[str, Any]:
    data: dict[str, Any] = {"projects": [], "sessions": [], "configs": [], "ai_configs": []}
    if not DASHBOARD_DB.exists():
        return data
    try:
        conn = sqlite3.connect(str(DASHBOARD_DB))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Projects
        try:
            cur.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            data["projects"] = [dict(row) for row in cur.fetchall()]
        except Exception:
            pass

        # Running sessions
        try:
            cur.execute("SELECT * FROM running_sessions ORDER BY updated_at DESC LIMIT 30")
            data["sessions"] = [dict(row) for row in cur.fetchall()]
        except Exception:
            pass

        # Configs
        try:
            cur.execute("SELECT * FROM gt_configs")
            data["configs"] = [dict(row) for row in cur.fetchall()]
        except Exception:
            pass

        # AI configs
        try:
            cur.execute("SELECT * FROM system_ai_configs")
            data["ai_configs"] = [dict(row) for row in cur.fetchall()]
        except Exception:
            pass

        conn.close()
    except Exception as e:
        data["error"] = str(e)
    return data


def get_cron_jobs() -> list[dict[str, str]]:
    output = run_cmd(["hermes", "cron", "list"], timeout=15)
    jobs: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("─") or line.startswith("┌") or line.startswith("┘") or line.startswith("│") or line.startswith("Scheduled") or line.startswith("\n"):
            continue
        if re.match(r"^[0-9a-f]{12}", line):
            if current:
                jobs.append(current)
            parts = line.split(None, 1)
            current = {"id": parts[0], "name": parts[1] if len(parts) > 1 else ""}
        elif ":" in line and current is not None:
            key, val = line.split(":", 1)
            current[key.strip().lower().replace(" ", "_")] = val.strip()
    if current:
        jobs.append(current)
    return jobs


def get_hermes_version() -> str:
    out = run_cmd(["hermes", "--version"], timeout=10)
    m = re.search(r"(\d+\.\d+\.\d+)", out)
    return m.group(1) if m else "unknown"


def get_disk_usage() -> str:
    out = run_cmd(["df", "-h", "/"], timeout=5)
    lines = out.strip().splitlines()
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 5:
            return f"{parts[4]} used ({parts[3]} free)"
    return "unknown"


def scan_project_status(vault: Path) -> list[dict[str, str]]:
    """Scan 03 Projects/ for status markers."""
    projects_dir = vault / "03 Projects"
    results: list[dict[str, str]] = []
    if not projects_dir.exists():
        return results
    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir():
            continue
        name = proj_dir.name
        status = "unknown"
        last_activity = "N/A"
        blockers = ""
        next_action = ""
        for md_file in proj_dir.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8", errors="ignore")
            if "Status:" in text or "status" in text.lower():
                for line in text.splitlines()[:30]:
                    if line.lower().startswith("status"):
                        status = line.split(":", 1)[-1].strip().lower()
            if "blocker" in text.lower() or "bug" in text.lower():
                blockers = "See project docs"
            mtime = datetime.datetime.fromtimestamp(md_file.stat().st_mtime)
            if last_activity == "N/A" or mtime > datetime.datetime.strptime(last_activity, "%Y-%m-%d"):
                last_activity = mtime.strftime("%Y-%m-%d")
        results.append(
            {
                "name": name,
                "status": status,
                "last_activity": last_activity,
                "blockers": blockers,
                "next_action": next_action,
            }
        )
    return results


# ── Index Generator ─────────────────────────────────────────────────────────


def generate_index() -> str:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    skill_count, skills = count_skills()
    db_data = query_dashboard_db()
    cron_jobs = get_cron_jobs()
    hermes_version = get_hermes_version()
    disk = get_disk_usage()
    vault_files = scan_vault_md_files(HERMES_VAULT)
    gt_vault_files = scan_vault_md_files(GT_VAULT)
    project_status = scan_project_status(HERMES_VAULT)

    # Build projects table from DB + vault scan
    db_projects = db_data.get("projects", [])
    project_lines = []
    for p in db_projects:
        name = p.get("name", "Unknown")
        status = p.get("status", "unknown")
        desc = p.get("description", "")
        updated = p.get("updated_at", "N/A")
        project_lines.append(f"| {name} | {status} | {updated} | {desc} |")

    # Build sessions table
    sessions = db_data.get("sessions", [])
    session_lines = []
    for s in sessions[:20]:
        name = s.get("name", "Unknown")
        agent = s.get("agent_type", "?")
        proj = s.get("project_name", "?")
        status = s.get("status", "?")
        ts = s.get("updated_at", "?")
        session_lines.append(f"| {name} | {agent} | {proj} | {status} | {ts} |")

    # Build cron table
    cron_lines = []
    for job in cron_jobs:
        cron_lines.append(
            f"| `{job.get('id', '?')}` | {job.get('name', '?')} | {job.get('schedule', '?')} | {job.get('next_run', '?')} | {job.get('last_run', '?')} | {job.get('status', '?')} |"
        )

    # Build skills table (top categories)
    from collections import Counter

    cat_counts = Counter([s[0] for s in skills])
    skill_lines = []
    for cat, cnt in cat_counts.most_common(20):
        skill_lines.append(f"| {cat} | {cnt} |")

    index = f"""# Master System Index

> **The single source of truth for GT's entire AI ecosystem.**
> **Auto-generated:** {now}
> **Next auto-update:** Every 6 hours via cron, or manual trigger
> **Bot:** @skorpion_claw_bot
> **Stack:** Hermes (orchestrator) + pi.dev (coder) + Kimi K2.6 + Dashboard + Obsidian

---

## System Snapshot

| Metric | Value |
|--------|-------|
| Hermes Version | {hermes_version} |
| Disk Usage | {disk} |
| Vault Files (Hermes) | {len(vault_files)} |
| Vault Files (GT) | {len(gt_vault_files)} |
| Skills | {skill_count} |
| Dashboard Projects | {len(db_projects)} |
| Recent Sessions | {len(sessions)} |
| Cron Jobs | {len(cron_jobs)} |

---

## Projects

| Name | Status | Last Update | Description |
|------|--------|-------------|-------------|
{chr(10).join(project_lines) if project_lines else "| — | — | — | — |"}

### Vault-Scanned Projects

| Name | Status | Last Activity | Blockers |
|------|--------|---------------|----------|
{chr(10).join(f"| {p['name']} | {p['status']} | {p['last_activity']} | {p['blockers']} |" for p in project_status) if project_status else "| — | — | — | — |"}

---

## Agents

| Agent | Role | Status |
|-------|------|--------|
| Hermes | Orchestrator, planner, monitor | Active |
| pi.dev | Coder, implementer, builder | Active |
| Kimi K2.6 | Primary LLM (262K context) | Active |
| Architect | System design, ADRs | Standby |
| CTO | Tech stack review, security | Standby |
| CFO | Budget, investment | Standby |
| CMO | GTM, ASO, content | Standby |
| COO | Operations, pipeline | Standby |
| Researcher | Research, trend watch | Standby |
| Reviewer | Code review, security audits | Standby |

---

## Recent Sessions (Last 20)

| Session | Agent | Project | Status | Updated |
|---------|-------|---------|--------|---------|
{chr(10).join(session_lines) if session_lines else "| — | — | — | — | — |"}

---

## Cron Jobs

| ID | Name | Schedule | Next Run | Last Run | Status |
|----|------|----------|----------|----------|--------|
{chr(10).join(cron_lines) if cron_lines else "| — | — | — | — | — | — |"}

---

## Skills (Top Categories)

| Category | Count |
|----------|-------|
{chr(10).join(skill_lines) if skill_lines else "| — | — |"}

---

## Quick Reference

| What | Path |
|------|------|
| This index | `{INDEX_PATH}` |
| Hermes config | `~/.hermes/config.yaml` |
| pi.dev config | `~/.pi/agent/settings.json` |
| Dashboard DB | `{DASHBOARD_DB}` |
| Skills repo | `{SKILLS_REPO}` |
| Daily digest | `gt-core/scripts/daily-digest.py` |
| Auto-updater | `gt-core/scripts/update_master_index.py` |

### How to Update

```bash
# Manual
python3 {SCRIPT_DIR}/update_master_index.py

# Cron (every 6 hours)
0 */6 * * * /opt/homebrew/bin/python3.11 {SCRIPT_DIR}/update_master_index.py
```

---

*This index is auto-generated. Do not edit manually — your changes will be overwritten.*
*Generator: `{SCRIPT_DIR}/update_master_index.py`*
"""
    return index


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Master System Index Auto-Updater")
    parser.add_argument("--daemon", action="store_true", help="Run every 6 hours")
    parser.add_argument("--watch", action="store_true", help="Watch for file changes")
    parser.add_argument("--output", type=Path, default=INDEX_PATH, help="Output path")
    args = parser.parse_args()

    if args.watch:
        print("[Watcher] Monitoring vault for changes... (Ctrl+C to stop)")
        last_hash = ""
        while True:
            index = generate_index()
            h = hashlib.sha256(index.encode()).hexdigest()
            if h != last_hash:
                args.output.write_text(index, encoding="utf-8")
                print(f"[Watcher] Updated {args.output} at {datetime.datetime.utcnow().isoformat()}")
                last_hash = h
            time.sleep(60)
    elif args.daemon:
        print("[Daemon] Starting 6-hour loop... (Ctrl+C to stop)")
        while True:
            index = generate_index()
            args.output.write_text(index, encoding="utf-8")
            print(f"[Daemon] Updated {args.output} at {datetime.datetime.utcnow().isoformat()}")
            time.sleep(6 * 3600)
    else:
        index = generate_index()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(index, encoding="utf-8")
        print(f"[OK] Master System Index updated: {args.output}")


if __name__ == "__main__":
    main()
