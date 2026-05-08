#!/usr/bin/env python3
"""
setup-cron.py — Manage GT system cron jobs.

Usage:
  python3 setup-cron.py --install    Add GT cron jobs
  python3 setup-cron.py --uninstall  Remove GT cron jobs
  python3 setup-cron.py --list       Show current GT cron jobs
"""

import argparse
import os
import re
import subprocess
import sys

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Marker used to identify GT cron jobs block
CRON_MARKER_START = "# === GT-CORE CRON JOBS START ==="
CRON_MARKER_END = "# === GT-CORE CRON JOBS END ==="

# Job definitions: (cron_schedule, job_name, script_cmd)
JOBS = [
    ("0 * * * *", "skills-sync", f"cd {BASE_DIR} && python3 {SCRIPTS_DIR}/sync-skills.py"),
    ("0 */6 * * *", "config-validate", f"cd {BASE_DIR} && python3 {SCRIPTS_DIR}/validate-config.py"),
    ("0 2 * * *", "hermes-upgrade", f"cd {BASE_DIR} && python3 {SCRIPTS_DIR}/hermes-upgrade.py --dry-run"),
    ("0 3 * * *", "diary-writer", f"cd {BASE_DIR} && python3 {SCRIPTS_DIR}/hermes-diary.py --today"),
    ("0 4 * * 0", "project-detect", f"cd {BASE_DIR} && python3 {SCRIPTS_DIR}/project-detect.py --register"),
]


def build_cron_block():
    lines = [CRON_MARKER_START]
    for schedule, name, cmd in JOBS:
        log_file = os.path.join(LOG_DIR, f"cron-{name}.log")
        # Redirect stdout and stderr to log file
        lines.append(f"{schedule} {cmd} >> {log_file} 2>&1")
    lines.append(CRON_MARKER_END)
    return "\n".join(lines) + "\n"


def get_current_crontab():
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    # No crontab for user yet
    if "no crontab" in result.stderr.lower():
        return ""
    print(f"Error reading crontab: {result.stderr.strip()}", file=sys.stderr)
    sys.exit(1)


def set_crontab(content):
    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
    proc.communicate(input=content)
    if proc.returncode != 0:
        print("Error updating crontab.", file=sys.stderr)
        sys.exit(1)


def remove_gt_block(crontab):
    pattern = re.compile(
        re.escape(CRON_MARKER_START) + r".*?" + re.escape(CRON_MARKER_END) + r"\n?",
        re.DOTALL,
    )
    return pattern.sub("", crontab)


def install():
    current = get_current_crontab()
    current = remove_gt_block(current)
    new_crontab = current.rstrip("\n") + "\n\n" + build_cron_block()
    set_crontab(new_crontab)
    print("GT cron jobs installed successfully.")


def uninstall():
    current = get_current_crontab()
    if CRON_MARKER_START not in current:
        print("No GT cron jobs found to uninstall.")
        return
    new_crontab = remove_gt_block(current).strip("\n")
    set_crontab(new_crontab + "\n")
    print("GT cron jobs uninstalled successfully.")


def list_jobs():
    current = get_current_crontab()
    if CRON_MARKER_START not in current:
        print("No GT cron jobs found.")
        return
    match = re.search(
        re.escape(CRON_MARKER_START) + r"(.*?)" + re.escape(CRON_MARKER_END),
        current,
        re.DOTALL,
    )
    if match:
        block = match.group(1).strip()
        print("Current GT cron jobs:")
        for line in block.splitlines():
            line = line.strip()
            if line:
                print("  " + line)
    else:
        print("GT marker found but could not parse jobs.")


def main():
    parser = argparse.ArgumentParser(description="Manage GT system cron jobs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true", help="Add GT cron jobs")
    group.add_argument("--uninstall", action="store_true", help="Remove GT cron jobs")
    group.add_argument("--list", action="store_true", help="Show current GT cron jobs")
    args = parser.parse_args()

    if args.install:
        install()
    elif args.uninstall:
        uninstall()
    elif args.list:
        list_jobs()


if __name__ == "__main__":
    main()
