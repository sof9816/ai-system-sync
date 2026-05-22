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
MAX_PER_CAT = int(os.getenv("MAX_PER_CAT", "6"))
MAX_PER_FEED = int(os.getenv("MAX_PER_FEED", "5"))
FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "10"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "30"))

# ── Zone Flair ─────────────────────────────────────────────────────
ZONE_HEADERS = [
    "☢️ ZONE BRIEFING — {date}",
    "🌫️ THE ZONE WHISPERS — {date}",
    "⚠️ ANOMALY DETECTED — {date}",
    "📡 PDA INCOMING — {date}",
    "🔥 EMISSION SURVIVORS REPORT — {date}",
]

ZONE_FOOTERS = [
    "\n— Stay alert, stalker. The Zone does not forgive.",
    "\n— Watch your back. The Monolith is listening.",
    "\n— Get out of here, stalker... or stay for the artifacts.",
    "\n— Sidorovich has fresh supplies. Check your PDA.",
    "\n— The emission is coming. Find cover.",
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
        "https://www.reddit.com/r/stalker/comments/.rss",
        "https://www.reddit.com/r/stalkermodding/.rss",
        "https://www.reddit.com/r/stalker_anomaly/comments/.rss",
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
        "https://lobste.rs/rss",
        "https://www.theregister.com/headlines.atom",
        "https://slashdot.org/slashdot.rss",
        "https://hackaday.com/feed/",
        "https://www.bleepingcomputer.com/feed/",
        "https://www.androidpolice.com/feed/",
        "https://9to5google.com/feed/",
        "https://www.xda-developers.com/feed/",
        "https://www.reddit.com/r/technology/.rss",
        "https://www.reddit.com/r/gadgets/.rss",
        "https://www.producthunt.com/feed",
        "https://www.cnet.com/rss/news/",
        "https://gizmodo.com/rss",
        "https://www.tomshardware.com/rss.xml",
    ],

    # === A.I. & MACHINES ===
    "ai": [
        "https://arxiv.org/rss/cs.AI",
        "https://blog.google/technology/ai/rss/",
        "https://openai.com/blog/rss.xml",
        "https://www.anthropic.com/rss.xml",
        "https://simonwillison.net/tags/ai/rss/",
        "https://www.oneusefulthing.org/rss",
        "https://www.lesswrong.com/rss",
        "https://importai.substack.com/feed",
        "https://www.thealgorithmicbridge.com/feed",
        "https://www.marktechpost.com/feed/",
        "https://www.unite.ai/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://blog.research.google/feeds/posts/default",
        "https://ai.googleblog.com/feeds/posts/default",
        "https://huggingface.co/blog/feed.xml",
        "https://www.reddit.com/r/LocalLLaMA/.rss",
        "https://www.reddit.com/r/artificial/.rss",
        "https://www.reddit.com/r/MachineLearning/.rss",
        "https://www.reddit.com/r/singularity/.rss",
        "https://www.pymnts.com/artificial-intelligence-2/feed/",
        "https://www.euronews.com/tag/artificial-intelligence/rss",
        "https://www.ai-journal.com/rss",
        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
        "https://www.cnet.com/tech/computing/rss/",
        "https://www.reuters.com/technology/artificial-intelligence/rss",
    ],

    # === GEOPOLITICS ===
    "geopolitics": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reuters.com/world/rss",
        "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.npr.org/1001/rss.xml",
        "https://www.politico.com/rss/politics08.xml",
        "https://www.foreignaffairs.com/rss.xml",
        "https://www.reddit.com/r/worldnews/.rss",
        "https://www.reddit.com/r/geopolitics/.rss",
        "https://www.reddit.com/r/internationalpolitics/.rss",
        "https://feeds.washingtonpost.com/rss/world",
        "https://feeds.nytimes.com/nyt/rss/World",
        "https://www.economist.com/international/rss.xml",
    ],

    # === CRYPTO ===
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://thedefiant.io/feed",
        "https://blockworks.co/feed",
        "https://www.theblock.co/rss.xml",
        "https://www.reddit.com/r/CryptoCurrency/.rss",
        "https://www.reddit.com/r/Bitcoin/.rss",
        "https://www.reddit.com/r/ethereum/.rss",
        "https://www.reddit.com/r/defi/.rss",
        "https://bitcoinmagazine.com/feed",
        "https://feeds.feedburner.com/nftnews",
    ],

    # === iOS / APPLE ===
    "ios": [
        "https://developer.apple.com/news/rss/news.rss",
        "https://www.macrumors.com/rss/macrumors.xml",
        "https://9to5mac.com/feed/",
        "https://daringfireball.net/feeds/main",
        "https://www.swiftbysundell.com/rss",
        "https://swiftweekly.com/rss",
        "https://www.raywenderlich.com/feed",
        "https://nshipster.com/feed.xml",
        "https://iosdevweekly.com/issues/feed",
        "https://www.reddit.com/r/apple/.rss",
        "https://www.reddit.com/r/ios/.rss",
        "https://www.reddit.com/r/jailbreak/.rss",
        "https://appleinsider.com/rss/news/",
        "https://www.cultofmac.com/feed/",
        "https://appleworld.today/feed/",
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
        "https://github.blog/feed/",
        "https://blog.uber.com/engineering/rss",
        "https://dropbox.tech/feed",
        "https://www.reddit.com/r/programming/.rss",
        "https://www.reddit.com/r/softwareengineering/.rss",
        "https://www.reddit.com/r/devops/.rss",
        "https://www.reddit.com/r/sysadmin/.rss",
        "https://aws.amazon.com/blogs/aws/feed/",
        "https://kubernetes.io/feed.xml",
    ],

    # === DUTY HIGH COMMAND ===
    "management": [
        "https://hbr.org/rss/topic/management.rss",
        "https://feeds.feedburner.com/LeadershipFreak",
        "https://www.calnewport.com/blog/feed/",
        "https://seths.blog/feed/",
        "https://fs.blog/feed/",
        "https://www.reddit.com/r/leadership/.rss",
        "https://www.reddit.com/r/management/.rss",
        "https://www.reddit.com/r/productivity/.rss",
        "https://feeds.feedburner.com/timferriss",
    ],

    # === FREELANCE STALKER ===
    "work": [
        "https://lifehacker.com/rss",
        "https://www.entrepreneur.com/latest.rss",
        "https://feeds.feedburner.com/37signals/beMH",
        "https://www.reddit.com/r/freelance/.rss",
        "https://www.reddit.com/r/startups/.rss",
        "https://www.reddit.com/r/smallbusiness/.rss",
        "https://www.reddit.com/r/antiwork/.rss",
        "https://www.reddit.com/r/overemployed/.rss",
        "https://www.reddit.com/r/digitalnomad/.rss",
    ],

    # === MEDBAY ===
    "health": [
        "https://feeds.npr.org/1001/rss.xml",
        "https://www.healthline.com/rss",
        "https://www.medicalnewstoday.com/newsfeeds/rss/medical_headlines.xml",
        "https://www.reddit.com/r/health/.rss",
        "https://www.reddit.com/r/medicine/.rss",
        "https://www.reddit.com/r/science/.rss",
        "https://www.statnews.com/feed/",
        "https://www.nature.com/subjects/medicine-and-healthcare.rss",
    ],

    # === IRON LUNG ===
    "gym": [
        "https://www.bodybuilding.com/rss/articles",
        "https://www.menshealth.com/rss",
        "https://www.nerdfitness.com/blog/feed/",
        "https://www.reddit.com/r/Fitness/.rss",
        "https://www.reddit.com/r/bodybuilding/.rss",
        "https://www.reddit.com/r/weightroom/.rss",
        "https://www.reddit.com/r/running/.rss",
        "https://www.reddit.com/r/crossfit/.rss",
        "https://www.reddit.com/r/hyrox/.rss",
        "https://www.strongerbyscience.com/feed/",
    ],

    # === CONSOLES & PC ===
    "games": [
        "https://kotaku.com/rss",
        "https://www.polygon.com/rss/index.xml",
        "https://www.pcgamer.com/rss/",
        "https://store.steampowered.com/feeds/news.xml",
        "https://www.ign.com/rss/articles/feed",
        "https://www.gamespot.com/feeds/news/",
        "https://www.reddit.com/r/gaming/.rss",
        "https://www.reddit.com/r/pcgaming/.rss",
        "https://www.reddit.com/r/Steam/.rss",
        "https://www.reddit.com/r/PS5/.rss",
        "https://www.reddit.com/r/XboxSeriesX/.rss",
        "https://www.reddit.com/r/NintendoSwitch/.rss",
        "https://www.eurogamer.net/?format=rss",
        "https://www.rockpapershotgun.com/feed",
        "https://www.gamesindustry.biz/rss",
    ],

    # === ANOMALY VISUALS ===
    "anime": [
        "https://www.animenewsnetwork.com/all/rss.xml",
        "https://myanimelist.net/rss/news.xml",
        "https://crunchyroll.com/news/rss",
        "https://www.reddit.com/r/anime/.rss",
        "https://www.reddit.com/r/manga/.rss",
        "https://www.reddit.com/r/OnePiece/.rss",
        "https://www.reddit.com/r/Naruto/.rss",
        "https://www.reddit.com/r/attackontitan/.rss",
        "https://www.funimation.com/blog/feed/",
    ],

    # === DEV BUNKER ===
    "gamedev": [
        "https://gamedevelopment.tutsplus.com/articles.rss",
        "https://www.gamasutra.com/rss",
        "https://godotengine.org/rss.xml",
        "https://godotengine.org/article/rss.xml",
        "https://www.gamedeveloper.com/rss.xml",
        "https://www.unrealengine.com/en-US/blog/rss",
        "https://www.reddit.com/r/gamedev/.rss",
        "https://www.reddit.com/r/Unity3D/.rss",
        "https://www.reddit.com/r/unrealengine/.rss",
        "https://www.reddit.com/r/godot/.rss",
        "https://www.reddit.com/r/IndieDev/.rss",
        "https://www.reddit.com/r/gameassets/.rss",
        "https://www.reddit.com/r/voxelgamedev/.rss",
    ],

    # === CINEMA BUNKER ===
    "movies": [
        "https://deadline.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://www.imdb.com/news/rss",
        "https://www.rottentomatoes.com/syndication/rss/in_theaters.xml",
        "https://feeds.feedburner.com/ComingSoon",
        "https://variety.com/feed/",
        "https://www.reddit.com/r/movies/.rss",
        "https://www.reddit.com/r/marvelstudios/.rss",
        "https://www.reddit.com/r/StarWars/.rss",
        "https://www.reddit.com/r/DC_Cinematic/.rss",
        "https://www.reddit.com/r/horror/.rss",
        "https://www.reddit.com/r/boxoffice/.rss",
        "https://screenrant.com/feed/",
        "https://collider.com/feed/",
    ],

    # === LOW-LEVEL FORGE ===
    "cpp_assembly": [
        "https://isocpp.org/blog/rss",
        "https://cppcon.org/feed/",
        "https://herbsutter.com/feed/",
        "https://www.fluentcpp.com/feed/",
        "https://godbolt.org/blog/atom.xml",
        "https://www.agner.org/optimize/blog/rss.xml",
        "https://handmade.network/rss",
        "https://www.phoronix.com/rss.php",
        "https://lwn.net/headlines/newrss",
        "https://www.reddit.com/r/cpp/.rss",
        "https://www.reddit.com/r/rust/.rss",
        "https://www.reddit.com/r/ProgrammingLanguages/.rss",
        "https://www.reddit.com/r/ReverseEngineering/.rss",
        "https://www.reddit.com/r/asm/.rss",
        "https://www.reddit.com/r/osdev/.rss",
        "https://www.reddit.com/r/Compilers/.rss",
    ],

    # === CODE ARTIFACTS ===
    "software_craft": [
        "https://martinfowler.com/feed.atom",
        "https://blog.cleancoder.com/feed",
        "https://refactoring.guru/rss",
        "https://www.joelonsoftware.com/feed/",
        "https://blog.pragmaticengineer.com/rss/",
        "https://newsletter.pragmaticengineer.com/feed",
        "https://addyosmani.com/blog/rss/",
        "https://overreacted.io/rss.xml",
        "https://kentcdodds.com/blog/rss.xml",
        "https://www.swyx.io/rss.xml",
        "https://blog.codinghorror.com/rss/",
        "https://feeds.feedburner.com/ScottHanselman",
        "https://www.reddit.com/r/coding/.rss",
        "https://www.reddit.com/r/learnprogramming/.rss",
        "https://www.reddit.com/r/webdev/.rss",
        "https://www.reddit.com/r/reactjs/.rss",
        "https://www.reddit.com/r/javascript/.rss",
        "https://www.reddit.com/r/Python/.rss",
        "https://www.reddit.com/r/golang/.rss",
        "https://www.reddit.com/r/typescript/.rss",
        "https://www.reddit.com/r/ExperiencedDevs/.rss",
        "https://www.reddit.com/r/cscareerquestions/.rss",
    ],

    # === INDIE ARTIFACTS ===
    "indie_games": [
        "https://indiegames.com/feed",
        "https://itch.io/games.rss",
        "https://www.gamedeveloper.com/rss.xml",
        "https://www.reddit.com/r/IndieGaming/.rss",
        "https://tigsource.com/feed/",
        "https://www.indiegamereviewer.com/feed/",
        "https://www.reddit.com/r/roguelikes/.rss",
        "https://www.reddit.com/r/survivalgaming/.rss",
        "https://www.reddit.com/r/BaseBuildingGames/.rss",
        "https://www.reddit.com/r/turnbased/.rss",
        "https://www.reddit.com/r/Metroidvania/.rss",
        "https://www.reddit.com/r/pcgaming/.rss",
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
async def fetch_feed(session: aiohttp.ClientSession, url: str) -> tuple[str, str, list[dict]]:
    """Fetch a single feed. Returns (category, url, entries)."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT)) as r:
            text = await r.text()
        parsed = feedparser.parse(text)
        entries = []
        for e in parsed.entries[:MAX_PER_FEED]:
            desc = ""
            for field in ("summary", "description", "content", "subtitle"):
                val = e.get(field)
                if val:
                    if isinstance(val, list) and val:
                        val = val[0].get("value", "")
                    desc = str(val)[:400]
                    break
            import re, html
            desc = re.sub(r"<[^>]+>", "", desc).strip()
            desc = html.unescape(desc)
            desc = " ".join(desc.split())
            if desc.lower() in {"comments", "", "read more", "continue reading", "as", "f", "submitted by"}:
                desc = ""
            if len(desc) < 5:
                desc = ""
            entries.append(
                {
                    "title": e.get("title", "Untitled"),
                    "link": e.get("link", ""),
                    "published": e.get("published", ""),
                    "description": desc,
                }
            )
        return ("", url, entries)
    except Exception as ex:
        print(f"Feed fail {url}: {ex}", file=sys.stderr)
        return ("", url, [])


# ── Format ─────────────────────────────────────────────────────────
def format_digest(articles: dict[str, list[dict]]) -> list[str]:
    """Return list of message chunks, each under 4096 chars.
    
    Uses PLAIN TEXT with raw URLs — Telegram auto-linkifies them.
    No HTML/Markdown tags since no_agent cron delivers verbatim text.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    header = f"{random.choice(ZONE_HEADERS).format(date=date_str)}\n"
    footer = random.choice(ZONE_FOOTERS)

    # Categories that get TL;DR descriptions
    HOT_CATS = {"ai", "tech", "ios", "crypto", "gamedev", "software_craft"}

    chunks = [header]
    for cat, items in articles.items():
        if not items:
            continue
        cat_name = ZONE_CAT_NAMES.get(cat, cat.upper())
        section = f"\n{cat_name}\n"
        for it in items[:MAX_PER_CAT]:
            title = it["title"]
            link = it["link"]
            desc = it.get("description", "")
            # Mark hot categories
            marker = "🔥 " if cat in HOT_CATS else ""
            section += f"• {marker}{title}\n  {link}\n"
            if desc:
                # Truncate description to ~120 chars, clean
                short = desc[:120].rsplit(" ", 1)[0] if len(desc) > 120 else desc
                if short and short != desc:
                    short += "…"
                section += f"  └ {short}\n"
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
        # Build task list: (category, url, coro)
        all_tasks = []
        for cat, urls in FEEDS.items():
            for url in urls:
                all_tasks.append((cat, url))
        
        # Process in batches of MAX_CONCURRENT for true parallelism
        for i in range(0, len(all_tasks), MAX_CONCURRENT):
            batch = all_tasks[i:i + MAX_CONCURRENT]
            coros = [fetch_feed(session, url) for _, url in batch]
            results = await asyncio.gather(*coros, return_exceptions=True)
            
            for (cat, url), result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Feed error {url}: {result}", file=sys.stderr)
                    continue
                _, _, entries = result
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
    asyncio.run(asyncio.wait_for(main(), timeout=300))
