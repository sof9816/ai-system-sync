# daily-digest-builder

> Build automated daily digest systems with scraping, Telegram bots, and cron jobs. Use this skill when creating news aggregators, monitoring dashboards, scheduled report bots, or any recurring content-delivery pipeline.

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/daily-digest-builder/SKILL.md`

## Skill Body

# Daily Digest Builder Skill

This skill provides patterns and recipes for building automated daily digest systems—scraping sources, formatting content, and delivering it via Telegram bots on a cron schedule.

## When to Use
Use this skill when:
- **Building a news or data aggregator**: Combine multiple sources into a single daily briefing.
- **Creating monitoring dashboards**: Daily summaries of metrics, alerts, or system health.
- **Setting up scheduled report bots**: Deliver formatted digests to Telegram channels or groups.
- **Automating recurring content delivery**: Any pipeline that runs on a schedule and pushes output to users.

## 1. Scraping Setup
- **Respect robots.txt**: Check a site's `robots.txt` before scraping. Be a good citizen.
- **Use proper headers**: Set a descriptive `User-Agent` with contact info. Some sites block default agents.
- **Rate limiting**: Add delays between requests. Exponential backoff on 429 responses.
- **Cache responses**: Store raw HTML to avoid re-fetching during development.
- **Parse defensively**: Sites change. Use CSS selectors with fallback logic. Validate expected fields exist.
- **Headless when needed**: Use Playwright or Selenium for JavaScript-heavy sites, but prefer static fetching when possible.
- **Example pattern**:
  ```python
  import requests
  from bs4 import BeautifulSoup
  import time

  def fetch_source(url):
      headers = {"User-Agent": "DailyDigestBot/1.0 (+https://example.com/bot)"}
      resp = requests.get(url, headers=headers, timeout=30)
      resp.raise_for_status()
      time.sleep(1)  # rate limit
      return BeautifulSoup(resp.text, "html.parser")
  ```

## 2. Telegram MTProto Proxy Config
- **Why MTProto**: In regions with Telegram blocks, MTProto proxies allow bot traffic to flow.
- **Proxy format**: `mtproto://<secret>@<host>:<port>` or use the `proxy_url` parameter in libraries.
- **python-telegram-bot example**:
  ```python
  from telegram import Bot
  from telegram.request import HTTPXRequest

  request = HTTPXRequest(proxy_url="http://proxy.example.com:8080")
  bot = Bot(token="YOUR_BOT_TOKEN", request=request)
  ```
- **aiogram example**:
  ```python
  from aiogram import Bot
  bot = Bot(token="YOUR_BOT_TOKEN", proxy="http://proxy.example.com:8080")
  ```
- **Self-hosted proxy**: Run `mtproto-proxy` via Docker for full control. See https://github.com/TelegramMessenger/MTProxy.
- **Rotation**: Maintain a small pool of proxies and rotate on connection failure.

## 3. Cron Patterns
- **Standard cron**: `0 9 * * *` — every day at 9:00 AM.
- **System cron**: Edit with `crontab -e`. Use full paths and log output.
  ```
  0 9 * * * /usr/bin/python3 /home/user/digest/run.py >> /home/user/digest/cron.log 2>&1
  ```
- **Hermes cron** (preferred when Hermes has messaging tools): Use `hermes cron create` so the agent owns delivery. Script outputs HTML; Hermes reads stdout/file and sends via `send_message`. See **Hermes-Mediated Delivery** below.
- **GitHub Actions scheduled workflows**: Good for hosted execution without a server.
  ```yaml
  on:
    schedule:
      - cron: "0 9 * * *"
  ```
- **Systemd timers**: More robust than cron. Supports dependencies, logging, and failure handling.
- **Timezones**: Always specify the timezone explicitly. UTC is safest; local time is friendlier.
- **Idempotency**: Design the job so running it twice is safe. Use deduplication keys or check before send.

### Hermes-Mediated Delivery
When Hermes has access to Telegram/email via its `messaging` toolset, do NOT embed send logic in the digest script. Instead:
1. Script fetches + formats digest, writes to a known file (e.g., `.digest_output.html`)
2. Script prints digest to stdout
3. Hermes cron job runs the script, captures output
4. Hermes uses `send_message` to deliver to Telegram/email
5. Hermes can also filter, summarize, or log Hermes-relevant items to Obsidian

Benefits: no API keys in scripts, no MTProto proxy complexity, delivery failures handled by Hermes retry logic, digest can be enriched before sending.

Pitfall: Embedding `python-telegram-bot` or SMTP directly in the script duplicates what Hermes already does, creates credential management problems, and breaks when Telegram is network-blocked (Hermes gateway may have alternate delivery paths).

## 4. Message Formatting
- **Keep it scannable**: Use bold headers, bullet points, and emojis sparingly for visual anchors.
- **Telegram HTML mode**: Use `<b>`, `<i>`, `<a href="...">`, `<code>`. Escape `<`, `>`, `&` in user content.
- **Length limits**: Telegram messages have a 4096 character limit. Split into multiple messages if needed.
- **Preview cards**: Include a thumbnail and link for each item if the digest is link-heavy.
- **Example template**:
  ```html
  <b>📅 Daily Digest — 2024-01-15</b>

  <b>🔥 Top Stories</b>
  • <a href="https://example.com/1">Story One</a> — Brief summary here.
  • <a href="https://example.com/2">Story Two</a> — Another summary.

  <b>📊 Metrics</b>
  • Users: <code>1,234</code> (+5%)
  • Errors: <code>12</code> (-3)
  ```
- **Error handling in formatting**: If a source fails, note it inline rather than silently omitting.
  ```
  ⚠️ Source "TechNews" failed to respond. Retrying next cycle.
  ```

## 5. Pipeline Architecture
- **Fetch → Parse → Filter → Format → Deliver**: Each stage is independent and testable.
- **Store raw data**: Save fetched content before parsing. Enables replay and debugging.
- **Deduplication**: Track sent items by URL or hash. Do not spam users with repeats.
- **Failure isolation**: One broken source should not kill the entire digest. Wrap each source in try/catch.
- **Retries with backoff**: Retry transient failures 3 times with exponential backoff.
- **Dead letter queue**: Log permanently failed items for manual inspection.

## 6. Configuration & Secrets
- **Environment variables**: `BOT_TOKEN`, `CHAT_ID`, `PROXY_URL`, `SOURCE_LIST`.
- **Config file**: JSON or YAML for source definitions, templates, and schedules.
- **Secret management**: Use a secrets manager (1Password, Doppler, AWS Secrets Manager) or encrypted env files. Never commit tokens.
- **Chat ID discovery**: Message `@userinfobot` or use `bot.get_updates()` to find your chat ID.

## 7. Monitoring & Alerting
- **Heartbeat**: Send a "digest builder alive" message to an admin channel once per day.
- **Log everything**: Structured JSON logs with timestamps, source names, and error details.
- **Alert on failure**: If the digest fails to build or deliver, notify via a separate channel or email.
- **Metrics**: Track sources scraped, items delivered, failures per source, delivery latency.

## 🛠️ Daily Digest Builder Checklist
- [ ] Are all sources fetched with proper rate limiting and headers?
- [ ] Is the Telegram token stored securely and not in the repo?
- [ ] Is the cron schedule explicit about timezone?
- [ ] Does the pipeline handle one source failing without crashing?
- [ ] Are messages split if they exceed 4096 characters?
- [ ] Is there deduplication to prevent repeated content?
- [ ] Are failures logged and alerted?
