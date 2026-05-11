#!/usr/bin/env python3
"""
daily-digest.py — Scrape AI/tech news and send Telegram digest.

Sources:
  - Hacker News (top 5 AI-related stories)
  - GitHub Trending (top 3 repos)
  - Reddit: r/LocalLLaMA, r/ClaudeAI (top 2 discussions)

Usage:
  python3 daily-digest.py --dry-run    # Build digest, do not send
  python3 daily-digest.py              # Build digest and send via Telegram

Env / secrets:
  TELEGRAM_BOT_TOKEN   — required to send
  TELEGRAM_CHAT_ID     — required to send
  TELEGRAM_MTProto_PROXY — optional mtproto:// proxy for restricted regions
"""

import argparse
import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime
from urllib.parse import quote, unquote

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_MTProto_PROXY = os.environ.get("TELEGRAM_MTProto_PROXY", "").strip()

# Keywords to filter AI-relevant HN stories
AI_KEYWORDS = [
    "ai", "llm", "gpt", "claude", "openai", "anthropic", "mistral",
    "gemini", "model", "neural", "transformer", "fine-tune", "rlhf",
    "inference", "agent", "autonomous", "rag", "embedding", "vector",
    "machine learning", "deep learning", "stable diffusion", "sora",
    "quantization", "onnx", "mlx", "cuda", "training", "dataset",
    "benchmark", "hallucination", "prompt", "jailbreak", "vulnerability",
    "security", "privacy", "alignment", "agi", "slop",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=_ctx(), timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def is_ai_related(title):
    t = title.lower()
    return any(k in t for k in AI_KEYWORDS)


def clean_title(title):
    # Unescape common HTML entities HN uses
    title = title.replace("&#x27;", "'")
    title = title.replace("&quot;", '"')
    title = title.replace("&amp;", "&")
    title = title.replace("&lt;", "<")
    title = title.replace("&gt;", ">")
    return title.strip()


# ---------------------------------------------------------------------------
# Scrapers
# ---------------------------------------------------------------------------
def scrape_hacker_news(limit=5):
    """Return top AI-related stories from HN front page."""
    html = fetch("https://news.ycombinator.com")
    # titleline pattern
    matches = re.findall(
        r'<span class="titleline">\s*<a href="([^"]+)"[^>]*>([^<]+)</a>',
        html,
    )
    stories = []
    for href, title in matches:
        title = clean_title(title)
        if is_ai_related(title):
            stories.append({"title": title, "url": href, "source": "HN"})
        if len(stories) >= limit:
            break
    # Fallback: if no AI matches, just take top N regardless
    if not stories:
        for href, title in matches[:limit]:
            stories.append({"title": clean_title(title), "url": href, "source": "HN"})
    return stories


def scrape_github_trending(limit=3):
    """Scrape GitHub trending (daily)."""
    url = "https://github.com/trending?since=daily"
    html = fetch(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    repos = []
    # Extract repo paths from hrefs, filter known non-repo paths
    skip_prefixes = (
        "/features", "/pricing", "/login", "/signup", "/explore", "/trending",
        "/collections", "/events", "/sponsors", "/topics", "/about",
        "/security", "/site", "/customer", "/enterprise", "/team",
        "/marketplace", "/mobile", "/pull", "/issues", "/actions",
        "/codespaces", "/copilot", "/settings", "/blog", "/readme",
        "/search", "/stars", "/notifications", "/users", "/orgs",
        "/join", "/new", "/import", "/trending/developers", "/apps",
    )
    matches = re.findall(
        r'href="(/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)"',
        html,
    )
    seen = set()
    for href in matches:
        if href in seen:
            continue
        if any(href.startswith(p) for p in skip_prefixes):
            continue
        if href.endswith(".css") or href.endswith(".js"):
            continue
        seen.add(href)
        # Derive display name from path: owner/repo
        name = href.strip("/").replace("/", " / ")
        repos.append({
            "name": name,
            "url": f"https://github.com{href}",
            "source": "GitHub",
        })
        if len(repos) >= limit:
            break
    return repos


def scrape_reddit(subreddit, limit=2):
    """Scrape Reddit subreddit top posts (JSON endpoint)."""
    url = f"https://www.reddit.com/r/{subreddit}/top/.json?t=day&limit={limit}"
    try:
        data = json.loads(
            fetch(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
            )
        )
    except Exception:
        return []
    posts = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        title = post.get("title", "").strip()
        permalink = post.get("permalink", "")
        url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
        score = post.get("score", 0)
        if title:
            posts.append({
                "title": title,
                "url": url,
                "score": score,
                "subreddit": subreddit,
                "source": "Reddit",
            })
    return posts


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def format_digest(hn_stories, gh_repos, reddit_posts):
    today = datetime.now().strftime("%A, %d %B %Y")
    lines = [
        f"📰 *Daily AI Digest — {today}*",
        "",
        "🤖 *Top AI News (Hacker News)*",
    ]
    for i, s in enumerate(hn_stories, 1):
        lines.append(f"{i}. [{s['title']}]({s['url']})")
    lines.append("")
    lines.append("🔥 *Trending Repos (GitHub)*")
    for i, r in enumerate(gh_repos, 1):
        lines.append(f"{i}. [{r['name']}]({r['url']})")
    lines.append("")
    lines.append("💬 *Reddit Discussions*")
    for i, p in enumerate(reddit_posts, 1):
        score_emoji = "🔺" if p.get("score", 0) > 100 else "⬆️"
        lines.append(f"{i}. [{p['title']}]({p['url']}) {score_emoji} {p.get('score', 0)}")
    lines.append("")
    lines.append("_Digest powered by scrapling + cron_ 🤖")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID", file=sys.stderr)
        return False

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Proxy support (MTProto or HTTP/SOCKS via urllib opener)
    proxy_url = TELEGRAM_MTProto_PROXY
    if proxy_url:
        # urllib supports http/https/socks proxies; mtproto:// is Telegram-specific.
        # If user supplies mtproto:// we warn and skip (needs python-telegram-bot or pproxy).
        if proxy_url.startswith("mtproto://"):
            print(f"[telegram] MTProto proxy configured but urllib cannot handle {proxy_url}", file=sys.stderr)
            print("[telegram] Install python-telegram-bot[passport] or pproxy for MTProto; falling back to direct.", file=sys.stderr)
        else:
            # e.g. http://host:port or socks5://host:port (needs PySocks)
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"https": proxy_url, "http": proxy_url})
            )
            urllib.request.install_opener(opener)

    try:
        with urllib.request.urlopen(req, context=_ctx(), timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                print("[telegram] Message sent successfully.")
                return True
            else:
                print(f"[telegram] API error: {result}", file=sys.stderr)
                return False
    except Exception as exc:
        print(f"[telegram] Request failed: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Daily AI Digest")
    parser.add_argument("--dry-run", action="store_true", help="Build digest but do not send")
    args = parser.parse_args()

    print("[digest] Scraping Hacker News …")
    hn = scrape_hacker_news(limit=5)
    print(f"[digest] HN stories: {len(hn)}")

    print("[digest] Scraping GitHub Trending …")
    gh = scrape_github_trending(limit=3)
    print(f"[digest] GitHub repos: {len(gh)}")

    print("[digest] Scraping Reddit …")
    reddit = []
    for sub in ("LocalLLaMA", "ClaudeAI"):
        posts = scrape_reddit(sub, limit=2)
        reddit.extend(posts)
        print(f"[digest] r/{sub} posts: {len(posts)}")
    # Keep top 2 overall by score
    reddit = sorted(reddit, key=lambda x: x.get("score", 0), reverse=True)[:2]

    digest = format_digest(hn, gh, reddit)

    # Save to log
    log_path = os.path.join(LOG_DIR, f"digest-{datetime.now().strftime('%Y%m%d')}.md")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"[digest] Saved to {log_path}")

    if args.dry_run:
        print("\n--- DRY-RUN DIGEST ---\n")
        print(digest)
        print("\n--- END DIGEST ---")
        print("[digest] Dry-run complete. No message sent.")
        return

    print("[digest] Sending via Telegram …")
    ok = send_telegram(digest)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
