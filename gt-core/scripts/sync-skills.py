#!/usr/bin/env python3
"""
sync-skills.py

Triggered by a Git webhook push event to gt-core/skills-repo/.

Steps:
1. Parse optional webhook payload (JSON stdin) for ref/branch info.
2. Pull latest changes in gt-core/skills-repo/.
3. Run validate-skills.py (expected at gt-core/scripts/validate-skills.py).
4. Sync valid skills to ~/.hermes/skills/ and ~/.agents/skills/.
5. Log to stdout and emit a JSON status blob.

Usage:
    # With webhook payload on stdin
    cat webhook.json | python3 gt-core/scripts/sync-skills.py

    # Without payload (assumes main branch)
    python3 gt-core/scripts/sync-skills.py

Exit codes:
    0 — success (or nothing to do)
    1 — validation or sync failure
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
SKILLS_REPO = AGENT_HOME / "gt-core/skills-repo"
VALIDATE_SCRIPT = AGENT_HOME / "gt-core/scripts/validate-skills.py"
HERMES_SKILLS = Path.home() / ".hermes/skills"
AGENTS_SKILLS = Path.home() / ".agents/skills"


def log(msg: str):
    print(f"[sync-skills] {msg}", flush=True)


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    """Run a shell command and return (ok, output_or_error)."""
    try:
        env = os.environ.copy()
        env["PATH"] = env.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin"
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=60,
        )
        ok = result.returncode == 0
        out = result.stdout.strip() if ok else (result.stderr.strip() or result.stdout.strip())
        return ok, out
    except Exception as e:
        return False, str(e)


def parse_webhook_payload() -> dict:
    """Read JSON webhook payload from stdin if available."""
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read().strip()
            if raw:
                return json.loads(raw)
        except json.JSONDecodeError as e:
            log(f"WARN: invalid JSON on stdin: {e}")
    return {}


def pull_latest(repo: Path) -> tuple[bool, str]:
    if not (repo / ".git").exists():
        return False, f"Not a git repository: {repo}"
    log(f"Pulling latest in {repo} ...")
    ok, out = run_cmd(["git", "pull", "--ff-only"], cwd=repo)
    if ok:
        log("Git pull succeeded.")
    else:
        log(f"Git pull failed: {out}")
    return ok, out


def validate_skills(repo: Path, validate_script: Path) -> tuple[bool, str]:
    if validate_script.exists():
        log(f"Running validator: {validate_script} ...")
        ok, out = run_cmd([sys.executable, str(validate_script), str(repo)])
        log(out)
        return ok, out

    log("WARN: validate-skills.py not found; skipping validation.")
    return True, "validation skipped (script missing)"


def sync_skills(src: Path, dst: Path) -> tuple[bool, str]:
    """Sync skill files from src to dst using rsync if available, else shutil.copytree."""
    if not src.exists():
        return True, f"source does not exist: {src}"

    dst.mkdir(parents=True, exist_ok=True)

    # Prefer rsync for atomicity and speed
    rsync_ok, _ = run_cmd(["which", "rsync"])
    if rsync_ok:
        log(f"Rsyncing {src}/ -> {dst}/")
        ok, out = run_cmd(
            [
                "rsync",
                "-a",
                "--delete",
                "--exclude=.git",
                "--exclude=__pycache__",
                "--exclude=*.pyc",
                str(src) + "/",
                str(dst) + "/",
            ]
        )
        return ok, out

    # Fallback: copytree with overwrite
    log(f"rsync unavailable; using shutil.copytree fallback {src} -> {dst}")
    try:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return True, "copytree succeeded"
    except Exception as e:
        return False, str(e)


def main() -> int:
    payload = parse_webhook_payload()
    ref = payload.get("ref", "refs/heads/main")
    branch = ref.split("/")[-1] if ref else "main"
    log(f"Webhook ref={ref} (branch={branch})")

    status = {
        "ref": ref,
        "branch": branch,
        "repo": str(SKILLS_REPO),
        "steps": {},
        "overall": "pending",
    }

    # 1. Pull latest
    pull_ok, pull_msg = pull_latest(SKILLS_REPO)
    status["steps"]["pull"] = {"ok": pull_ok, "message": pull_msg}

    # 2. Validate
    val_ok, val_msg = validate_skills(SKILLS_REPO, VALIDATE_SCRIPT)
    status["steps"]["validate"] = {"ok": val_ok, "message": val_msg}

    # 3. Sync to targets
    sync_hermes_ok, sync_hermes_msg = sync_skills(SKILLS_REPO, HERMES_SKILLS)
    sync_agents_ok, sync_agents_msg = sync_skills(SKILLS_REPO, AGENTS_SKILLS)
    status["steps"]["sync_hermes"] = {"ok": sync_hermes_ok, "message": sync_hermes_msg}
    status["steps"]["sync_agents"] = {"ok": sync_agents_ok, "message": sync_agents_msg}

    # 4. Overall status
    overall_ok = val_ok and sync_hermes_ok and sync_agents_ok
    status["overall"] = "success" if overall_ok else "failure"

    # Always emit JSON status last line
    print(json.dumps(status, indent=2))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
