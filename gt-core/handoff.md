# GT Centralized System — Handoff Document
## Created: 2026-05-09 15:45
## For: Fresh Hermes thread

---

## CURRENT STATUS

**System:** GT Core (GT Centralized System)
**Location:** `/Users/gt/Public/MyFiles/agent-home/gt-core/`
**Git Repo:** `github.com/sof9816/ai-skills` (137 skills)

### What's Working
- 137 skills in git repo, synced via symlink to Hermes (`~/.hermes/skills/`) and pi.dev (`~/.agents/skills/`)
- Single source of truth: `gt-core/skills-repo/` — both agents read directly, no copy lag
- Config API at `http://localhost:7373/api/gt/config`
- Project registry API at `http://localhost:7373/api/gt/projects`
- Webhook sync endpoint at `http://localhost:7373/api/webhooks/skills-sync`
- Integration test: 10/10 passed
- Obsidian vault updated with diary, health reports, upgrade suggestions
- Daily digest system active (Hermes cron job)
- Sci-fi Jarvis dashboard built and running
- Context7 skill added to repo
- Superpowers (`using-superpowers`) skill added to repo

### What Needs Work
1. ~~Cron jobs~~ — ✅ Fixed (Hermes cron)
2. ~~Daily digest~~ — ✅ Running
3. ~~Dashboard~~ — ✅ Built
4. ~~pi.dev integration~~ — ✅ Tested
5. ~~Context7 skill~~ — ✅ Added

---

## NEXT TASKS (Priority Order)

### Task 1: Fix Cron Jobs
**Files:**
- `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/setup-cron.py`
- `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/sync-skills.py`
- `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/apply-config.py`
- `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/hermes-diary.py`
- `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/hermes-upgrade.py`

**Issue:** Setup script ran but `crontab -l` shows 0 jobs. Need to debug why.

### Task 2: Daily Digest
**Requirements:**
- Use scrapling for web scraping
- Telegram bot using mtproto proxies from: `https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt`
- Morning digest with AI news, trends, GitHub releases
- Send to Telegram bot

**Files to create:**
- `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/daily-digest.py`

### Task 3: Dashboard Sci-Fi UI
**Requirements:**
- Dark space gradient background
- Cyan neon accents (#00f0ff, #00d4ff)
- Glassmorphism panels
- Scan lines effect
- HUD-style panels
- Real-time status indicators
- Jarvis-inspired aesthetic

**Files:**
- `/Users/gt/Public/MyFiles/agent-home/dashboard/index.html`
- `/Users/gt/Public/MyFiles/agent-home/dashboard/styles.css`
- `/Users/gt/Public/MyFiles/agent-home/dashboard/app.js`

### Task 4: Test pi.dev Integration
**Steps:**
1. Verify pi.dev can see synced skills in `~/.agents/skills/`
2. Test pi.dev executing a task using a skill
3. Verify config propagation to pi.dev

### Task 5: Context7 Skill
**Source:** `https://github.com/upstash/context7`
**URL:** `https://context7.com/`
**Action:** Fetch original skill, add to git repo, sync to all agents

---

## KEY PATHS

| Path | Description |
|------|-------------|
| `/Users/gt/Public/MyFiles/agent-home/` | Working directory |
| `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/` | Git repo (136 skills) |
| `/Users/gt/Public/MyFiles/agent-home/gt-core/scripts/` | All system scripts |
| `/Users/gt/Public/MyFiles/agent-home/gt-core/config/` | Config schema + YAML |
| `/Users/gt/Public/MyFiles/agent-home/dashboard/` | Dashboard files |
| `~/.hermes/skills/` | Hermes skills (synced) |
| `~/.agents/skills/` | pi.dev skills (synced) |
| `/Users/gt/.claude/skills/` | Claude Code skills (7 skills) |
| `/Users/gt/Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault/` | Obsidian vault |

---

## IMPORTANT NOTES

1. **Python version:** Use `/opt/homebrew/bin/python3.11` for venvs (not 3.14)
2. **Kimi API:** Base URL is `https://api.kimi.com/coding` (NO `/v1` suffix)
3. **pi.dev:** Chokes on large prompts — break into tiny chunks
4. **Skills:** Must be created in `gt-core/skills-repo/` and committed, NOT in `~/.hermes/skills/`
5. **Ghostty config:** `~/.config/ghostty/config`

---

## COMMANDS TO RUN IN NEW THREAD

```bash
# Verify current state
cd /Users/gt/Public/MyFiles/agent-home
git -C gt-core/skills-repo log --oneline -5
python3 gt-core/scripts/integration-test.py

# Check cron jobs
crontab -l

# Check skills count
find gt-core/skills-repo -name "SKILL.md" | wc -l
ls ~/.hermes/skills/ | wc -l
ls ~/.agents/skills/ | wc -l
```

---

## USER PREFERENCES

- Short, direct, no-fluff communication
- Proactive feature ideation
- High quality bar (tests, docs, stability)
- Prefers dashboards/GUIs over CLI
- Hybrid workflow: Hermes plans, pi.dev executes
- Max 3 concurrent subagents
- Sci-fi Jarvis aesthetic for dashboard

---

## READY TO CONTINUE

Pick task 1-5 or run all in parallel with subagents.
