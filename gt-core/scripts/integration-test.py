#!/usr/bin/env python3
"""
GT Centralized System — Integration Test
Tests all components and generates health report.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
SKILLS_REPO = AGENT_HOME / "gt-core/skills-repo"
CONFIG_FILE = AGENT_HOME / "gt-core/config/gt-config.yaml"
DB_PATH = AGENT_HOME / "dashboard/backend/data/app.db"
VAULT_PATH = Path("/Users/gt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes")


def run(cmd, **kwargs):
    """Run shell command, return (ok, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, **kwargs)
        return r.returncode == 0, r.stdout, r.stderr
    except Exception as e:
        return False, "", str(e)


def test_skills():
    """Test 1: Skills repo validation."""
    script = AGENT_HOME / "gt-core/scripts/validate-skills.py"
    if not script.exists():
        return False, "validate-skills.py not found"
    ok, out, err = run(f"cd {SKILLS_REPO} && python3 {script} .")
    if not ok:
        return False, f"Validation failed: {err}"
    if "All skills valid" not in out:
        return False, f"Skills invalid: {out[:200]}"
    # Count skills
    count = out.count("✓")
    return True, f"{count} skills valid"


def test_config():
    """Test 2: Config file exists and API responds."""
    if not CONFIG_FILE.exists():
        return False, "gt-config.yaml not found"
    ok, out, err = run("curl -s http://localhost:7373/api/gt/config")
    if not ok or not out.strip():
        return False, "Config API not responding"
    try:
        data = json.loads(out)
        sections = len(data)
        return True, f"{sections} config sections loaded"
    except json.JSONDecodeError:
        return False, "Config API returned invalid JSON"


def test_projects():
    """Test 3: Project registry API."""
    ok, out, err = run("curl -s http://localhost:7373/api/gt/projects")
    if not ok:
        return False, "Projects API not responding"
    try:
        data = json.loads(out)
        count = len(data)
        return True, f"{count} projects registered"
    except json.JSONDecodeError:
        return False, "Projects API returned invalid JSON"


def test_secrets():
    """Test 4: Secrets API."""
    ok, out, err = run("curl -s http://localhost:7373/api/gt/secrets")
    if not ok:
        return False, "Secrets API not responding"
    try:
        data = json.loads(out)
        count = len(data)
        return True, f"{count} secrets in vault"
    except json.JSONDecodeError:
        return False, "Secrets API returned invalid JSON"


def test_webhook():
    """Test 5: Webhook endpoint responds."""
    ok, out, err = run(
        'curl -s -o /dev/null -w "%{http_code}" '
        '-X POST http://localhost:7373/api/webhooks/skills-sync '
        '-H "Content-Type: application/json" '
        '-d \'{"ref":"refs/heads/main"}\''
    )
    if ok and out.strip() == "200":
        return True, "Webhook responds 200"
    return False, f"Webhook returned {out.strip()}"


def test_diary():
    """Test 6: Today's diary file exists."""
    today = datetime.now().strftime("%Y-%m-%d")
    diary_file = VAULT_PATH / f"hermes/diary/{today}.md"
    if diary_file.exists():
        return True, f"Diary file exists: {diary_file.name}"
    return False, "Today's diary not found"


def test_cron():
    """Test 7: Cron jobs installed."""
    ok, out, err = run("crontab -l | grep 'GT-CORE CRON JOBS'")
    if ok and "GT-CORE CRON JOBS" in out:
        jobs = out.count("python3")
        return True, f"{jobs} cron jobs installed"
    return False, "No GT cron jobs found"


def test_sync():
    """Test 8: Skills synced to hermes."""
    hermes_skills = Path.home() / ".hermes/skills"
    if hermes_skills.exists():
        count = len(list(hermes_skills.rglob("SKILL.md")))
        return True, f"{count} skills synced to ~/.hermes/skills/"
    return False, "Hermes skills dir not found"


def test_claude_export():
    """Test 9: Claude export exists."""
    claude_dir = AGENT_HOME / "gt-core/claude-export"
    if claude_dir.exists():
        files = list(claude_dir.rglob("*.md"))
        return True, f"{len(files)} Claude export files"
    return False, "Claude export dir not found"


def test_provider_switch():
    """Test 10: Provider switch script exists."""
    script = AGENT_HOME / "gt-core/scripts/switch-provider.py"
    if script.exists():
        return True, "switch-provider.py exists"
    return False, "Provider switch script not found"


TESTS = [
    ("Skills Repo", test_skills),
    ("Config System", test_config),
    ("Project Registry", test_projects),
    ("Secrets Vault", test_secrets),
    ("Webhook Sync", test_webhook),
    ("Diary Writer", test_diary),
    ("Cron Jobs", test_cron),
    ("Skills Sync", test_sync),
    ("Claude Export", test_claude_export),
    ("Provider Switch", test_provider_switch),
]


def main():
    fix = "--fix" in sys.argv
    notify = "--notify" in sys.argv

    results = []
    passed = 0
    failed = 0

    print("=" * 60)
    print("GT Centralized System — Integration Test")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    for name, test_fn in TESTS:
        try:
            ok, msg = test_fn()
        except Exception as e:
            ok, msg = False, f"Exception: {e}"
        status = "PASS" if ok else "FAIL"
        results.append({"name": name, "ok": ok, "message": msg})
        if ok:
            passed += 1
            print(f"  ✓ {name:20s} {msg}")
        else:
            failed += 1
            print(f"  ✗ {name:20s} {msg}")

    total = len(TESTS)
    score = int((passed / total) * 100)

    print("=" * 60)
    print(f"Result: {passed}/{total} passed ({score}%)")
    print("=" * 60)

    # JSON output
    report = {
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "failed": failed,
        "total": total,
        "score": score,
        "tests": results,
    }
    print(json.dumps(report, indent=2))

    # Write to Obsidian
    report_dir = VAULT_PATH / "hermes/system/health-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    report_file = report_dir / f"{today}.md"

    md = f"""---
date: {today}
score: {score}%
passed: {passed}
failed: {failed}
---

# GT System Health Report — {today}

## Summary

| Metric | Value |
|--------|-------|
| Score | {score}% |
| Passed | {passed}/{total} |
| Failed | {failed}/{total} |

## Test Results

| Test | Status | Details |
|------|--------|---------|
"""
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        md += f"| {r['name']} | {icon} | {r['message']} |\n"

    md += f"""
## Actions Needed

"""
    failures = [r for r in results if not r["ok"]]
    if failures:
        for r in failures:
            md += f"- [ ] Fix {r['name']}: {r['message']}\n"
    else:
        md += "- All systems operational. No action needed.\n"

    with open(report_file, "w") as f:
        f.write(md)

    print(f"\nReport written to: {report_file}")

    if notify and score < 90:
        print(f"\n⚠️ ALERT: Health score {score}% below 90% threshold!")
        return 1

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
