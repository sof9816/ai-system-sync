#!/usr/bin/env python3
"""
hermes-diary.py — Hermes Diary Writer
Reads today's session data from the dashboard DB (or stdin) and writes
a structured diary entry to the Obsidian Hermes Vault.

Usage:
    python hermes-diary.py --today
    python hermes-diary.py --today --project "MyProject"
    python hermes-diary.py --date 2026-05-07
    cat session.json | python hermes-diary.py --stdin
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sqlite3
import sys
import subprocess
import yaml
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ── Configuration ───────────────────────────────────────────────────────────

DASHBOARD_DB = os.environ.get(
    "DASHBOARD_DB",
    "/Users/gt/Public/MyFiles/agent-home/dashboard/data/dashboard.db",
)

VAULT_ROOT = os.environ.get(
    "GT_VAULT_ROOT",
    "/Users/gt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes",
)

DIARY_DIR = Path(VAULT_ROOT) / "hermes" / "diary"

# ── DB helpers ────────────────────────────────────────────────────────────────


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DASHBOARD_DB)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_sessions(day: date, project: str | None = None) -> list[dict[str, Any]]:
    """Pull running_sessions for a given calendar day."""
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    sql = """
        SELECT id, name, agent_type, project_id, project_name, status,
               cwd, command, created_at, updated_at, completed_at, exit_code,
               session_dir
        FROM running_sessions
        WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) < datetime(?)
    """
    params: list[Any] = [start.isoformat(), end.isoformat()]
    if project:
        sql += " AND (project_name = ? OR name LIKE ?)"
        params += [project, f"% on {project}%"]
    sql += " ORDER BY created_at ASC"
    with _db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def fetch_api_usage(day: date) -> list[dict[str, Any]]:
    """Pull api_usage_records for the day."""
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    sql = """
        SELECT provider, model, tokens_input, tokens_output, tokens_total,
               cost_usd, request_status, response_ms, source_system, created_at
        FROM api_usage_records
        WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) < datetime(?)
        ORDER BY created_at ASC
    """
    with _db() as conn:
        rows = conn.execute(sql, [start.isoformat(), end.isoformat()]).fetchall()
    return [dict(r) for r in rows]


def fetch_agent_sessions(day: date) -> list[dict[str, Any]]:
    """Pull agent chat messages for the day."""
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    sql = """
        SELECT agent_name, role, message, timestamp
        FROM agent_sessions
        WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) < datetime(?)
        ORDER BY timestamp ASC
    """
    with _db() as conn:
        rows = conn.execute(sql, [start.isoformat(), end.isoformat()]).fetchall()
    return [dict(r) for r in rows]


def fetch_projects() -> list[dict[str, Any]]:
    sql = "SELECT id, name, path, type, status FROM gt_projects"
    with _db() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# ── Analysis helpers ────────────────────────────────────────────────────────


def _extract_skills_from_sessions(sessions: list[dict]) -> Counter:
    skills = Counter()
    # Heuristic: look for skill names in session names / commands / cwd
    skill_patterns = {
        "ios": r"iOS|Swift|Xcode|CarPlay",
        "python": r"python|\.py$|backend",
        "web": r"react|vue|angular|html|css|js$|ts$",
        "infra": r"docker|k8s|terraform|ansible|deploy",
        "data": r"sql|db|sqlite|postgres|mongo",
        "ai": r"llm|gpt|openai|kimi|claude|model",
        "swarm": r"swarm|agent|multi-agent",
        "design": r"ui|ux|figma|design",
    }
    for s in sessions:
        text = f"{s.get('name','')} {s.get('cwd','')} {str(s.get('command',''))}"
        for skill, pat in skill_patterns.items():
            if re.search(pat, text, re.I):
                skills[skill] += 1
    return skills


def _extract_decisions(agent_sessions: list[dict]) -> list[str]:
    decisions = []
    for row in agent_sessions:
        msg = row.get("message", "")
        # naive heuristic: sentences that look like decisions
        for sentence in re.split(r"[.!?]\s+", msg):
            low = sentence.lower()
            if any(k in low for k in ("decided", "choose", "opted", "will use", "going with", "settled on", "agreed to")):
                decisions.append(sentence.strip())
    # dedupe while preserving order
    seen = set()
    uniq = []
    for d in decisions:
        if d not in seen and len(d) > 15:
            seen.add(d)
            uniq.append(d)
    return uniq[:8]  # cap


def _extract_errors(sessions: list[dict]) -> list[dict]:
    errors = []
    for s in sessions:
        if s.get("exit_code") not in (0, None):
            errors.append({
                "session": s.get("name"),
                "error": f"Exit code {s.get('exit_code')}",
                "resolution": "Review logs in session_dir",
            })
        if s.get("status") == "killed":
            errors.append({
                "session": s.get("name"),
                "error": "Session was killed",
                "resolution": "Check resource limits or manual interruption",
            })
    return errors


def _build_performance(api_usage: list[dict]) -> dict[str, Any]:
    total_tokens = sum(r.get("tokens_total") or 0 for r in api_usage)
    total_time_ms = sum(r.get("response_ms") or 0 for r in api_usage)
    total_cost = sum(r.get("cost_usd") or 0 for r in api_usage)
    statuses = Counter(r.get("request_status") for r in api_usage)
    total = len(api_usage) or 1
    success_rate = round((statuses.get("success", 0) / total) * 100, 1)
    models_used = Counter(r.get("model") for r in api_usage if r.get("model"))
    providers_used = Counter(r.get("provider") for r in api_usage if r.get("provider"))
    return {
        "total_tokens": total_tokens,
        "total_time_ms": total_time_ms,
        "total_cost_usd": round(total_cost, 4),
        "success_rate": success_rate,
        "models_used": dict(models_used),
        "providers_used": dict(providers_used),
        "request_count": len(api_usage),
    }


def _suggestions(sessions: list[dict], api_perf: dict, errors: list) -> list[str]:
    suggs = []
    if api_perf["success_rate"] < 80:
        suggs.append("API success rate is low — review provider keys and rate limits.")
    if api_perf["total_cost_usd"] > 5.0:
        suggs.append("Daily API spend exceeded $5 — consider caching or model downgrade.")
    if len(errors) > 3:
        suggs.append("High error count today — add retry logic and better error handling.")
    if not suggs:
        suggs.append("No major issues detected — maintain current workflow.")
    return suggs


# ── Markdown builders ───────────────────────────────────────────────────────


def _fm_line(key: str, value: Any) -> str:
    if isinstance(value, (list, dict)):
        return f'{key}: {json.dumps(value)}'
    return f"{key}: {value}"


def build_diary_entry(
    day: date,
    sessions: list[dict],
    api_usage: list[dict],
    agent_sessions: list[dict],
    project_filter: str | None = None,
) -> str:
    skills = _extract_skills_from_sessions(sessions)
    decisions = _extract_decisions(agent_sessions)
    errors = _extract_errors(sessions)
    perf = _build_performance(api_usage)
    suggestions = _suggestions(sessions, perf, errors)

    session_ids = [s["id"] for s in sessions]
    models_used = list(perf["models_used"].keys()) if perf["models_used"] else ["unknown"]

    lines: list[str] = []
    lines.append("---")
    lines.append(_fm_line("date", day.isoformat()))
    lines.append(_fm_line("session_id", session_ids))
    lines.append(_fm_line("tasks_count", len(sessions)))
    lines.append(_fm_line("skills_used", list(skills.keys())))
    lines.append(_fm_line("models_used", models_used))
    if project_filter:
        lines.append(_fm_line("project", project_filter))
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append(f"- **Sessions**: {len(sessions)}")
    lines.append(f"- **API calls**: {perf['request_count']}")
    lines.append(f"- **Tokens**: {perf['total_tokens']:,}")
    lines.append(f"- **Success rate**: {perf['success_rate']}%")
    if project_filter:
        lines.append(f"- **Filtered by project**: {project_filter}")
    lines.append("")

    # Decisions
    lines.append("## Decisions Made")
    if decisions:
        for d in decisions:
            lines.append(f"- {d}")
    else:
        lines.append("- No explicit decisions captured today.")
    lines.append("")

    # Skills
    lines.append("## Skills Used")
    lines.append("| Skill | Count |")
    lines.append("|-------|-------|")
    for skill, cnt in skills.most_common():
        lines.append(f"| {skill} | {cnt} |")
    if not skills:
        lines.append("| — | — |")
    lines.append("")

    # Performance
    lines.append("## Performance")
    lines.append(f"- **Total tokens**: {perf['total_tokens']:,}")
    lines.append(f"- **Total time (ms)**: {perf['total_time_ms']:,}")
    lines.append(f"- **Total cost (USD)**: ${perf['total_cost_usd']}")
    lines.append(f"- **Success rate**: {perf['success_rate']}%")
    lines.append("")

    # Errors
    lines.append("## Errors Encountered")
    if errors:
        for e in errors:
            lines.append(f"- **{e['session']}**: {e['error']}")
            lines.append(f"  - *Resolution*: {e['resolution']}")
    else:
        lines.append("- None")
    lines.append("")

    # Suggestions
    lines.append("## Suggestions for Future")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")

    # Related project notes
    lines.append("## Related Project Notes")
    projects = fetch_projects()
    linked = []
    for s in sessions:
        pname = s.get("project_name")
        if pname:
            for p in projects:
                if p.get("name") == pname:
                    linked.append((pname, p.get("path", "")))
                    break
    if linked:
        seen = set()
        for pname, ppath in linked:
            if pname in seen:
                continue
            seen.add(pname)
            # Obsidian link style
            safe = pname.replace(" ", "%20")
            lines.append(f"- [[{pname}]] — `{ppath}`")
    else:
        lines.append("- No project context available.")
    lines.append("")

    return "\n".join(lines)


def build_append_section(
    day: date,
    sessions: list[dict],
    api_usage: list[dict],
    agent_sessions: list[dict],
) -> str:
    """Build a new section to append when the file already exists."""
    skills = _extract_skills_from_sessions(sessions)
    decisions = _extract_decisions(agent_sessions)
    errors = _extract_errors(sessions)
    perf = _build_performance(api_usage)
    suggestions = _suggestions(sessions, perf, errors)

    ts = datetime.now().strftime("%H:%M:%S")
    lines: list[str] = []
    lines.append(f"## Update {ts}")
    lines.append("")
    lines.append("### Decisions Made")
    if decisions:
        for d in decisions:
            lines.append(f"- {d}")
    else:
        lines.append("- No new decisions.")
    lines.append("")
    lines.append("### Skills Used")
    for skill, cnt in skills.most_common():
        lines.append(f"- {skill} ({cnt})")
    lines.append("")
    lines.append("### Performance")
    lines.append(f"- Tokens: {perf['total_tokens']:,} | Time: {perf['total_time_ms']:,}ms | Success: {perf['success_rate']}%")
    lines.append("")
    lines.append("### Errors")
    if errors:
        for e in errors:
            lines.append(f"- {e['session']}: {e['error']}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("### Suggestions")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")
    return "\n".join(lines)


# ── File I/O ────────────────────────────────────────────────────────────────


def diary_path(day: date) -> Path:
    DIARY_DIR.mkdir(parents=True, exist_ok=True)
    return DIARY_DIR / f"{day.isoformat()}.md"


def write_or_append(day: date, content: str, append_mode: bool = False) -> Path:
    path = diary_path(day)
    if path.exists() and append_mode:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n")
            f.write(content)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return path


# ── Stdin JSON mode ───────────────────────────────────────────────────────────


def read_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON on stdin: {exc}", file=sys.stderr)
        sys.exit(1)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes Diary Writer")
    parser.add_argument("--today", action="store_true", help="Process today's sessions")
    parser.add_argument("--date", type=str, help="Process a specific date (YYYY-MM-DD)")
    parser.add_argument("--project", type=str, help="Filter by project name")
    parser.add_argument("--stdin", action="store_true", help="Read session JSON from stdin")
    parser.add_argument("--vault", type=str, default=VAULT_ROOT, help="Obsidian vault root path")
    parser.add_argument("--db", type=str, default=DASHBOARD_DB, help="Dashboard SQLite DB path")
    args = parser.parse_args()

    if args.vault:
        vault_root = args.vault
        DIARY_DIR = Path(vault_root) / "hermes" / "diary"
    if args.db:
        db_path = args.db

    # Determine target day
    if args.stdin:
        payload = read_stdin()
        day = date.fromisoformat(payload.get("date", date.today().isoformat()))
        sessions = payload.get("sessions", [])
        api_usage = payload.get("api_usage", [])
        agent_sessions = payload.get("agent_sessions", [])
        content = build_diary_entry(day, sessions, api_usage, agent_sessions, args.project)
        path = write_or_append(day, content, append_mode=False)
        print(path)
        return

    if args.date:
        day = date.fromisoformat(args.date)
    elif args.today:
        day = date.today()
    else:
        parser.print_help()
        sys.exit(1)

    sessions = fetch_sessions(day, project=args.project)
    api_usage = fetch_api_usage(day)
    agent_sessions = fetch_agent_sessions(day)

    path = diary_path(day)
    if path.exists():
        section = build_append_section(day, sessions, api_usage, agent_sessions)
        write_or_append(day, section, append_mode=True)
    else:
        content = build_diary_entry(day, sessions, api_usage, agent_sessions, args.project)
        write_or_append(day, content, append_mode=False)

    print(path)


if __name__ == "__main__":
    main()
