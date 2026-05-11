#!/usr/bin/env python3
"""☢️ GT ZONE DAILY BRIEFING ☢️

S.T.A.L.K.E.R.-themed daily digest for the Zone.
Fetches RSS feeds across categories, deduplicates via SQLite,
formats as Telegram HTML with thematic flair, outputs to stdout.
Hermes reads stdout and sends to Telegram.

Categories: tech, ai, geopolitics, crypto, ios, engineering, management,
work, health, gym, games, anime, gamedev, movies, stalker_zone,
cpp_assembly, software_craft, indie_games.
"""

import asyncio
import hashlib
import os
import random
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Use the correct Python interpreter
PYTHON = "/opt/homebrew/bin/python3.11"

# Ensure deps are available before importing
try:
    import aiohttp
    import feedparser
except ImportError:
    subprocess.check_call([PYTHON, "-m", "pip", "install", "--quiet", "aiohttp", "feedparser"])
    import importlib
    importlib.invalidate_caches()
    # Add the homebrew site-packages to path if needed
    import site
    site.addsitedir("/opt/homebrew/lib/python3.11/site-packages")
    aiohttp = importlib.import_module("aiohttp")
    feedparser = importlib.import_module("feedparser")
SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = SCRIPT_DIR / "digest.db"
OUTPUT_PATH = SCRIPT_DIR / ".digest_output.html"

# ── Config ─────────────────────────────────────────────────────────
MAX_PER_CAT = int(os.getenv("MAX_PER_CAT", "3"))
MAX_PER_FEED = int(os.getenv("MAX_PER_FEED", "5"))

# ── Zone Flair ─────────────────────────────────────────────────────
ZONE_HEADERS = [
    "☢️ ZONE BRIEFING — {date}",
    "🌫️ THE ZONE WHISPERS — {date}",
    "⚠️ ANOMALY DETECTED — {date}",
    "📡 PDA INCOMING — {date}",
    "🔥 EMISSION SURVIVORS REPORT — {date}",
]

ZONE_FOOTERS = [
    "\n<i>— Stay alert, stalker. The Zone does not forgive.</i>",
    "\n<i>— Watch your back. The Monolith is listening.</i>",
    "\n<i>— Get out of here, stalker... or stay for the artifacts.</i>",
    "\n<i>— Sidorovich has fresh supplies. Check your PDA.</i>",
    "\n<i>— The emission is coming. Find cover.</i>",
]

ZONE_CAT_NAMES = {
    "stalker_zone": "🌫️ THE ZONE",
    "tech": "💻 TECH",
    "ai": "🤖 A.I. & MACHINES",
    "geopolitics": "🌍 THE OUTSIDE WORLD",
    "crypto": "₿ DIGITAL ARTIFACTS",
    "ios": "📱 APPLE DEVICES",
    "engineering": "⚙️ ENGINEERING BUNKER",
    "management": "📊 DUTY HIGH COMMAND",
    "work": "💼 FREELANCE STALKER",
    "health": "❤️ MEDBAY",
    "gym": "🏋️ IRON LUNG",
    "games": "🎮 CONSOLES & PC",
    "anime": "🍥 ANOMALY VISUALS",
    "gamedev": "🕹️ DEV BUNKER",
    "movies": "🎬 CINEMA BUNKER",
    "cpp_assembly": "🔧 LOW-LEVEL FORGE",
    "software_craft": "✨ CODE ARTIFACTS",
    "indie_games": "🎯 INDIE ARTIFACTS",
}

ZONE_EMOJIS = {
    "stalker_zone": "🌫️",
    "tech": "💻",
    "ai": "🤖",
    "geopolitics": "🌍",
    "crypto": "₿",
    "ios": "📱",
    "engineering": "⚙️",
    "management": "📊",
    "work": "💼",
    "health": "❤️",
    "gym": "🏋️",
    "games": "🎮",
    "anime": "🍥",
    "gamedev": "🕹️",
    "movies": "🎬",
    "cpp_assembly": "🔧",
    "software_craft": "✨",
    "indie_games": "🎯",
}

# ── RSS Sources ────────────────────────────────────────────────────
FEEDS = {
    # === THE ZONE ===
    "stalker_zone": [
        "https://www.reddit.com/r/stalker/.rss",
        "https://www.reddit.com/r/stalker_anomaly/.rss",
        "https://www.moddb.com/games/stalker-anomaly/rss",
        "https://www.gsc-game.com/rss/news.xml",
    ],

    # === TECH ===
    "tech": [
        "https://news.ycombinator.com/rss",
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.engadget.com/rss.xml",
        "https://arstechnica.com/feed/",
        "https://feeds.feedburner.com/TechCrunch",
        "https://www.wired.com/feed/rss",
        "https://feeds.arstechnica.com/arstechnica/index",
    ],

    # === A.I. & MACHINES ===
    "ai": [
        "https://arxiv.org/rss/cs.AI",
        "https://blog.google/technology/ai/rss/",
        "https://openai.com/blog/rss.xml",
        "https://www.anthropic.com/rss.xml",
        "https://simonwillison.net/tags/ai/rss/",
        "https://www.oneusefulthing.org/rss",  # Ethan Mollick
        "https://www.lesswrong.com/rss",  # AI alignment / rationality
        "https://importai.substack.com/feed",  # Import AI newsletter
        "https://www.thealgorithmicbridge.com/feed",  # Algorithmic Bridge
        "https://blog.google/technology/ai/rss/",
        "https://www.marktechpost.com/feed/",  # AI model releases
        "https://www.unite.ai/feed/",  # AI tools & models
        "https://venturebeat.com/category/ai/feed/",  # AI industry
    ],

    # === GEOPOLITICS ===
    "geopolitics": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reuters.com/world/rss",
        "https://feeds.a.dj.com/rss/RSSWorldNews.xml",  # WSJ World
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],

    # === CRYPTO ===
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
    ],

    # === iOS / APPLE ===
    "ios": [
        "https://developer.apple.com/news/rss/news.rss",
        "https://www.macrumors.com/rss/macrumors.xml",
        "https://9to5mac.com/feed/",
        "https://daringfireball.net/feeds/main",
        "https://www.swiftbysundell.com/rss",
        "https://swiftweekly.com/rss",
    ],

    # === ENGINEERING BUNKER ===
    "engineering": [
        "https://engineering.linkedin.com/blog.rss",
        "https://slack.engineering/feed/",
        "https://engineering.fb.com/feed/",
        "https://blog.twitter.com/engineering/en_us/blog.rss",
        "https://medium.com/feed/netflix-techblog",
        "https://stripe.com/blog/feed.rss",
        "https://blog.cloudflare.com/rss",
    ],

    # === DUTY HIGH COMMAND ===
    "management": [
        "https://hbr.org/rss/topic/management.rss",
        "https://feeds.feedburner.com/LeadershipFreak",
        "https://www.calnewport.com/blog/feed/",
    ],

    # === FREELANCE STALKER ===
    "work": [
        "https://lifehacker.com/rss",
    ],

    # === MEDBAY ===
    "health": [
        "https://feeds.npr.org/1001/rss.xml",
        "https://www.healthline.com/rss",
    ],

    # === IRON LUNG ===
    "gym": [
        "https://www.bodybuilding.com/rss/articles",
        "https://www.menshealth.com/rss",
    ],

    # === CONSOLES & PC ===
    "games": [
        "https://kotaku.com/rss",
        "https://www.polygon.com/rss/index.xml",
        "https://www.pcgamer.com/rss/",
        "https://store.steampowered.com/feeds/news.xml",
    ],

    # === ANOMALY VISUALS ===
    "anime": [
        "https://www.animenewsnetwork.com/all/rss.xml",
        "https://myanimelist.net/rss/news.xml",
    ],

    # === DEV BUNKER ===
    "gamedev": [
        "https://gamedevelopment.tutsplus.com/articles.rss",
        "https://www.gamasutra.com/rss",
        "https://godotengine.org/rss.xml",
        "https://godotengine.org/article/rss.xml",
    ],

    # === CINEMA BUNKER ===
    "movies": [
        "https://deadline.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://www.imdb.com/news/rss",
        "https://www.rottentomatoes.com/syndication/rss/in_theaters.xml",
        "https://feeds.feedburner.com/ComingSoon",
    ],

    # === LOW-LEVEL FORGE ===
    "cpp_assembly": [
        "https://isocpp.org/blog/rss",
        "https://cppcon.org/feed/",
        "https://herbsutter.com/feed/",
        "https://www.fluentcpp.com/feed/",
        "https://godbolt.org/blog/atom.xml",  # Compiler Explorer
        "https://www.agner.org/optimize/blog/rss.xml",  # Agner Fog
        "https://handmade.network/rss",  # Handmade community (C/asm focus)
        "https://www.phoronix.com/rss.php",  # Linux/hardware low-level
    ],

    # === CODE ARTIFACTS ===
    "software_craft": [
        "https://martinfowler.com/feed.atom",
        "https://blog.cleancoder.com/feed",
        "https://refactoring.guru/rss",
        "https://www.joelonsoftware.com/feed/",
        "https://blog.pragmaticengineer.com/rss/",
        "https://newsletter.pragmaticengineer.com/feed",  # Gergely's newsletter
        "https://addyosmani.com/blog/rss/",
        "https://overreacted.io/rss.xml",  # Dan Abramov
        "https://kentcdodds.com/blog/rss.xml",
        "https://www.swyx.io/rss.xml",  # swyx (learn in public)
    ],

    # === INDIE ARTIFACTS ===
    "indie_games": [
        "https://indiegames.com/feed",
        "https://itch.io/games.rss",
        "https://www.gamedeveloper.com/rss.xml",
        "https://www.reddit.com/r/IndieGaming/.rss",
        "https://tigsource.com/feed/",
    ],
}

# ── DB ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            category TEXT,
            published TEXT,
            fetched_at TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fetched ON articles(fetched_at)")
    conn.commit()
    conn.close()


def article_id(link: str) -> str:
    return hashlib.sha256(link.encode()).hexdigest()[:16]


def is_new(link: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT 1 FROM articles WHERE id=?", (article_id(link),))
    row = cur.fetchone()
    conn.close()
    return row is None


def store_article(title, link, category, published):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO articles VALUES (?,?,?,?,?,?)",
        (article_id(link), title, link, category, published, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def cleanup_old(days=7):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM articles WHERE fetched_at < ?", (cutoff,))
    conn.commit()
    conn.close()


# ── RSS Fetch ──────────────────────────────────────────────────────
async def fetch_feed(session: aiohttp.ClientSession, url: str) -> list[dict]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r:
            text = await r.text()
        parsed = feedparser.parse(text)
        entries = []
        for e in parsed.entries[:MAX_PER_FEED]:
            entries.append(
                {
                    "title": e.get("title", "Untitled"),
                    "link": e.get("link", ""),
                    "published": e.get("published", ""),
                }
            )
        return entries
    except Exception as ex:
        print(f"Feed fail {url}: {ex}", file=sys.stderr)
        return []


# ── Format ─────────────────────────────────────────────────────────
def format_digest(articles: dict[str, list[dict]]) -> list[str]:
    """Return list of message chunks, each under 4096 chars.
    
    Uses PLAIN TEXT with raw URLs — Telegram auto-linkifies them.
    No HTML/Markdown tags since no_agent cron delivers verbatim text.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    header = f"{random.choice(ZONE_HEADERS).format(date=date_str)}\n"
    footer = random.choice(ZONE_FOOTERS)

    chunks = [header]
    for cat, items in articles.items():
        if not items:
            continue
        cat_name = ZONE_CAT_NAMES.get(cat, cat.upper())
        section = f"\n{cat_name}\n"
        for it in items[:MAX_PER_CAT]:
            title = it["title"]
            link = it["link"]
            section += f"• {title}\n  {link}\n"
        if len(chunks[-1]) + len(section) > 3800:
            chunks.append(section)
        else:
            chunks[-1] += section

    # Add footer to last chunk
    if len(chunks[-1]) + len(footer) < 4096:
        chunks[-1] += footer
    else:
        chunks.append(footer)

    return chunks


# ── Main ───────────────────────────────────────────────────────────
async def main():
    init_db()
    cleanup_old()
    articles: dict[str, list[dict]] = {k: [] for k in FEEDS}
    async with aiohttp.ClientSession() as session:
        for cat, urls in FEEDS.items():
            for url in urls:
                entries = await fetch_feed(session, url)
                for e in entries:
                    if e["link"] and is_new(e["link"]):
                        store_article(e["title"], e["link"], cat, e["published"])
                        articles[cat].append(e)
    if not any(articles.values()):
        print("No new articles.", file=sys.stderr)
        return
    chunks = format_digest(articles)
    OUTPUT_PATH.write_text("\n---MSG_SPLIT---\n".join(chunks), encoding="utf-8")
    for chunk in chunks:
        print(chunk)
        print("\n---MSG_SPLIT---\n")


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=90))
