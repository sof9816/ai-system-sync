#!/usr/bin/env python3
"""Hermes Self-Upgrade Script: scans task history, detects patterns, checks deps, suggests upgrades."""
import argparse, json, os, re, sqlite3, sys, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta

DB = os.path.expanduser("/Users/gt/Public/MyFiles/agent-home/dashboard/data/dashboard.db")
OBSIDIAN = os.path.expanduser("/Users/gt/Public/MyFiles/agent-home/Hermes Vault/Hermes/system/upgrade-suggestions.md")

def fetch(query, params=()):
    if not os.path.exists(DB):
        return []
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def skill_from_command(cmd_json):
    try:
        cmd = json.loads(cmd_json) if isinstance(cmd_json, str) else cmd_json
        if isinstance(cmd, list):
            for i, a in enumerate(cmd):
                if a == "--append-system-prompt" and i + 1 < len(cmd):
                    p = cmd[i + 1]
                    if "prompts/" in p:
                        return os.path.basename(p).replace(".md", "")
        return None
    except Exception:
        return None

def error_pattern(text):
    patterns = [
        (r"PermissionDeniedError", "PermissionDeniedError"),
        (r"openai\.PermissionDeniedError", "OpenAI PermissionDenied"),
        (r"Error code:\s*403", "403 Forbidden"),
        (r"access_terminated_error", "Access Terminated"),
        (r"No such file or directory", "Missing File"),
        (r"Playback failed", "Playback Failed"),
        (r"Sandbox restriction", "Sandbox Restriction"),
        (r"Failed to stat path", "Stat Path Failure"),
        (r"CoreData:\s*error", "CoreData Error"),
        (r"Signing for .* requires a development team", "Xcode Signing"),
        (r"'main' attribute can only apply to one type", "Swift Main Attribute"),
    ]
    found = []
    for pat, name in patterns:
        if re.search(pat, text or "", re.IGNORECASE):
            found.append(name)
    return found

def analyze_patterns(days=30):
    since = (datetime.now() - timedelta(days=days)).isoformat()
    sessions = fetch("SELECT * FROM running_sessions WHERE created_at > ? ORDER BY created_at DESC", (since,))
    skills = Counter()
    errors = Counter()
    week_skills = defaultdict(Counter)
    for s in sessions:
        sk = skill_from_command(s.get("command", "[]"))
        if sk:
            skills[sk] += 1
            wk = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00") if "Z" in s["created_at"] else s["created_at"]).isocalendar().week
            week_skills[wk][sk] += 1
        for e in error_pattern(s.get("command", "") + " " + (s.get("output_log", "") or "")):
            errors[e] += 1
    suggestions = []
    for wk, cnt in week_skills.items():
        for sk, c in cnt.items():
            if c > 5:
                suggestions.append({"type": "new_skill", "skill": sk, "week": wk, "count": c, "reason": f"{sk} used {c} times in week {wk}"})
    for err, c in errors.items():
        if c > 3:
            suggestions.append({"type": "config_fix", "pattern": err, "count": c, "reason": f"{err} seen {c} times"})
    return suggestions, skills, errors, len(sessions)

def analyze_performance(days=30):
    since = (datetime.now() - timedelta(days=days)).isoformat()
    usage = fetch("SELECT * FROM api_usage_records WHERE created_at > ?", (since,))
    if not usage:
        return []
    total = len(usage)
    success = sum(1 for u in usage if u.get("request_status") == "success")
    rate = (success / total * 100) if total else 100
    avg_tokens = sum(u.get("tokens_total", 0) or 0 for u in usage) / total if total else 0
    avg_time = sum(u.get("response_ms", 0) or 0 for u in usage) / total if total else 0
    suggestions = []
    if rate < 80:
        suggestions.append({"type": "model_change", "reason": f"Success rate {rate:.1f}% < 80%", "current_rate": rate})
    spike_threshold = avg_tokens * 2.5
    spikes = [u for u in usage if (u.get("tokens_total") or 0) > spike_threshold]
    if len(spikes) > 2:
        suggestions.append({"type": "thinking_adjust", "reason": f"{len(spikes)} token spikes > {spike_threshold:.0f}", "spikes": len(spikes)})
    if avg_time > 8000:
        suggestions.append({"type": "provider_change", "reason": f"Avg response {avg_time:.0f}ms > 8000ms", "avg_ms": avg_time})
    return suggestions

def check_latest(pkg, pypi=True):
    try:
        if pypi:
            url = f"https://pypi.org/pypi/{pkg}/json"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())
                return data["info"]["version"]
        else:
            url = f"https://registry.npmjs.org/{pkg}/latest"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())
                return data.get("version", "unknown")
    except Exception as e:
        return f"error: {e}"

def check_dependencies():
    suggestions = []
    pkgs = [("hermes-agent", True), ("pi", True), ("dashboard", False)]
    for pkg, pypi in pkgs:
        latest = check_latest(pkg, pypi)
        suggestions.append({"type": "dependency", "package": pkg, "latest": latest, "action": f"Check if {pkg} needs upgrade to {latest}"})
    return suggestions

def write_obsidian(data):
    os.makedirs(os.path.dirname(OBSIDIAN), exist_ok=True)
    lines = ["# Hermes Upgrade Suggestions", f"Generated: {datetime.now().isoformat()}", ""]
    for s in data["suggestions"]:
        lines.append(f"- **{s['type']}**: {s.get('reason', s.get('action', ''))}")
    lines.append("")
    lines.append("## Stats")
    lines.append(f"- Sessions (30d): {data['stats']['sessions']}")
    lines.append(f"- Skills used: {dict(data['stats']['skills'])}")
    lines.append(f"- Error patterns: {dict(data['stats']['errors'])}")
    with open(OBSIDIAN, "w") as f:
        f.write("\n".join(lines))

CACHE_DIR = os.path.expanduser("/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/.cache")
CACHE_FILE = os.path.join(CACHE_DIR, "research_cache.json")
CACHE_TTL_HOURS = 6

def _cache_path():
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_FILE

def _load_cache():
    try:
        with open(_cache_path(), "r") as f:
            return json.load(f)
    except Exception:
        return None

def _save_cache(data):
    with open(_cache_path(), "w") as f:
        json.dump(data, f)

def _is_cache_fresh(cached):
    if not cached or "cached_at" not in cached:
        return False
    try:
        cached_time = datetime.fromisoformat(cached["cached_at"])
        return datetime.now() - cached_time < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:
        return False

def _fetch_reddit_json(subreddit, limit=25):
    """Try to fetch Reddit JSON feed. Returns None if blocked/unavailable."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "HermesUpgradeBot/0.1 (stdlib only)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception:
        return None

def _mock_research_data():
    """Fallback mock data when Reddit APIs are unavailable."""
    return [
        {
            "source": "r/LocalLLaMA (mock)",
            "title": "New budget inference provider drops GPT-4-class pricing to $0.30/M tokens",
            "category": "cost_effective_api",
            "priority": "high",
            "action": "Evaluate new provider for GT system integration"
        },
        {
            "source": "r/ClaudeAI (mock)",
            "title": "Claude 4 Sonnet released with 200k context and tool use improvements",
            "category": "model_release",
            "priority": "high",
            "action": "Update model aliases and test compatibility"
        },
        {
            "source": "r/LocalLLaMA (mock)",
            "title": "MCP (Model Context Protocol) skills trending — 40% more repos this month",
            "category": "new_skill_category",
            "priority": "medium",
            "action": "Consider adding MCP skill support to GT"
        },
        {
            "source": "r/ClaudeAI (mock)",
            "title": "OpenAI deprecates GPT-3.5-turbo-0613 in 60 days",
            "category": "model_deprecation",
            "priority": "high",
            "action": "Audit and migrate any GPT-3.5-turbo-0613 references"
        },
        {
            "source": "r/LocalLLaMA (mock)",
            "title": "Kimi k2.6 tops coding benchmarks — 15% better than Claude 3.7 Sonnet",
            "category": "performance_benchmark",
            "priority": "medium",
            "action": "Benchmark Kimi k2.6 against current GT default model"
        }
    ]

def _score_finding(title, category):
    """Score a finding by relevance to GT system."""
    title_lower = (title or "").lower()
    if category in ("cost_effective_api", "model_deprecation"):
        return "high"
    if category in ("new_skill_category", "performance_benchmark"):
        return "medium"
    if any(w in title_lower for w in ["price", "cost", "cheap", "free", "deprecat"]):
        return "high"
    if any(w in title_lower for w in ["new model", "release", "benchmark", "skill", "tool"]):
        return "medium"
    return "low"

def _parse_reddit_posts(data, subreddit):
    """Extract relevant posts from Reddit JSON."""
    findings = []
    try:
        posts = data.get("data", {}).get("children", [])
    except Exception:
        return findings
    keywords = [
        "api", "cost", "price", "cheap", "release", "new model", "claude", "gpt", "kimi",
        "skill", "tool", "mcp", "benchmark", "deprecat", "terminate", "sunset"
    ]
    for child in posts:
        post = child.get("data", {})
        title = post.get("title", "")
        title_lower = title.lower()
        if not any(k in title_lower for k in keywords):
            continue
        # Categorize
        if any(w in title_lower for w in ["price", "cost", "cheap", "free", "api pricing"]):
            category = "cost_effective_api"
        elif any(w in title_lower for w in ["deprecat", "sunset", "terminate", "end of life"]):
            category = "model_deprecation"
        elif any(w in title_lower for w in ["release", "new model", "claude", "gpt", "kimi"]):
            category = "model_release"
        elif any(w in title_lower for w in ["skill", "tool", "mcp", "framework"]):
            category = "new_skill_category"
        elif any(w in title_lower for w in ["benchmark", "performance", "speed", "latency"]):
            category = "performance_benchmark"
        else:
            category = "general"
        priority = _score_finding(title, category)
        if priority == "low":
            continue
        findings.append({
            "source": f"r/{subreddit}",
            "title": title,
            "category": category,
            "priority": priority,
            "action": _suggest_action(category, title)
        })
    return findings

def _suggest_action(category, title):
    actions = {
        "cost_effective_api": "Evaluate provider for GT integration",
        "model_release": "Update model aliases and test compatibility",
        "new_skill_category": "Consider adding support to GT",
        "performance_benchmark": "Benchmark against current GT default model",
        "model_deprecation": "Audit and migrate references",
        "general": "Monitor for GT relevance"
    }
    return actions.get(category, "Review for GT impact")

def research_ai_trends(force=False):
    """
    Simulate last30days-skill research:
    - Scans Reddit r/LocalLLaMA, r/ClaudeAI for trending posts.
    - Uses urllib to fetch JSON if available, else cached/mock data.
    - Scores findings by relevance to GT system.
    - Caches results for 6 hours.
    """
    if not force:
        cached = _load_cache()
        if _is_cache_fresh(cached):
            return cached.get("findings", [])

    all_findings = []
    for sub in ["LocalLLaMA", "ClaudeAI"]:
        data = _fetch_reddit_json(sub)
        if data:
            all_findings.extend(_parse_reddit_posts(data, sub))

    if not all_findings:
        all_findings = _mock_research_data()

    # Deduplicate by title
    seen = set()
    deduped = []
    for f in all_findings:
        if f["title"] not in seen:
            seen.add(f["title"])
            deduped.append(f)

    _save_cache({"cached_at": datetime.now().isoformat(), "findings": deduped})
    return deduped

def write_obsidian(data):
    os.makedirs(os.path.dirname(OBSIDIAN), exist_ok=True)
    lines = ["# Hermes Upgrade Suggestions", f"Generated: {datetime.now().isoformat()}", ""]
    for s in data["suggestions"]:
        lines.append(f"- **{s['type']}**: {s.get('reason', s.get('action', ''))}")
    lines.append("")
    lines.append("## Stats")
    lines.append(f"- Sessions (30d): {data['stats']['sessions']}")
    lines.append(f"- Skills used: {dict(data['stats']['skills'])}")
    lines.append(f"- Error patterns: {dict(data['stats']['errors'])}")
    if data.get("research"):
        lines.append("")
        lines.append("## External Trends")
        for r in data["research"]:
            lines.append(f"- **[{r['priority'].upper()}]** {r['title']} (via {r['source']})")
            lines.append(f"  - Action: {r['action']}")
    with open(OBSIDIAN, "w") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Hermes self-upgrade analyzer")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve trusted suggestions")
    parser.add_argument("--dry-run", action="store_true", help="Show suggestions without acting")
    parser.add_argument("--research", action="store_true", help="Force fresh AI trends research")
    args = parser.parse_args()

    pattern_sugs, skills, errors, sess_count = analyze_patterns()
    perf_sugs = analyze_performance()
    dep_sugs = check_dependencies()
    research = research_ai_trends(force=args.research)

    all_sugs = pattern_sugs + perf_sugs + dep_sugs
    result = {
        "generated_at": datetime.now().isoformat(),
        "suggestions": all_sugs,
        "stats": {"sessions": sess_count, "skills": dict(skills), "errors": dict(errors)},
        "research": research
    }

    print(json.dumps(result, indent=2))

    if not args.dry_run:
        write_obsidian(result)
        print(f"\nObsidian note written to: {OBSIDIAN}")

    if args.auto_approve:
        trusted = [s for s in all_sugs if s["type"] in ("config_fix", "dependency")]
        if trusted:
            print(f"\nAuto-approved {len(trusted)} trusted suggestion(s):")
            for t in trusted:
                print(f"  - {t['type']}: {t.get('reason', t.get('action', ''))}")

if __name__ == "__main__":
    main()
