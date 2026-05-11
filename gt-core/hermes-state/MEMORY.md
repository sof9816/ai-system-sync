Obsidian vault path: /Users/gt/Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault. Uses PARA-like folders (00-04) + hermes/ for AI-related notes. Hermes writes to hermes/ unless asked otherwise.
§
MyFiles directory is /Users/gt/Public/MyFiles (~57 GB). Now organized into 11 numbered category folders (01-Work, 02-Flutter, 03-iOS-Swift, 04-Design, 05-Crypto-Web3, 06-GameDev, 07-Python-Automation, 08-Web-Node, 09-Security-Research, 10-Archives, 99-Misc). Contains sensitive files: tokens.json and Important Stuff/ with passwords/keys in 99-Misc.
§
Ghostty config on macOS is actively used at ~/.config/ghostty/config (not just ~/Library/Application Support/com.mitchellh.ghostty/config). When editing Ghostty settings, patch ~/.config/ghostty/config first.
§
System Python 3 default is Homebrew 3.14.2, which breaks pydantic-core (PyO3 max 3.13). For any Python project using FastAPI/SQLAlchemy/pydantic, must explicitly use `/opt/homebrew/bin/python3.11` when creating venvs. Available: python3.11, python3.13 (both OK), python3.14 (broken for pydantic).
§
pi.dev CLI chokes on large prompts. Use task files (one file, <3000 chars). Game dev workflow: check git, grill-me before planning, document in Obsidian, spawn pi.dev for code, swarm max 3, check .cursor/rules/. Final Escape Godot: /Users/gt/Public/MyFiles/06-GameDev/final-escape-g. Vector-neon=default SVG skin (flat). Original PNG=profile-only. Cosmic/Cyberpunk=paid. New power-ups need vector-neon integration. a0=old/unused. Test screens: debug-only, simple, power-ups spawn lower half away from asteroid path.
§
Zone Daily Briefing: Hermes cron at 10 AM, 18 categories, 70+ feeds, Stalker theme. Script at gt-core/scripts/daily-digest.py, copied to ~/.hermes/scripts/. GT prefers clean one-line links: `• [Title](link)`, no summary fragments.
§
GT Core skills repo is single source of truth. Hermes (`~/.hermes/skills/`) and pi.dev (`~/.agents/skills/`) are symlinks to `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/`. `skills.external_dirs` also points to repo. Sync script detects symlinks and skips copy. All skills must be created in repo and committed.
§
Nate Herk Framework (Hermes best practices):
→ GitHub backup cron: nightly push of skills + memory to private repo. Non-negotiable.
→ Agent-per-role: split when agent needs own creds, memory, or ongoing separate role. Main personal first, then spin off.
→ Security: named API keys per agent, least privilege, firewall, nightly security audit skill.
→ Wrong twice on same thing → correct on spot + update skill/memory.
→ Same instruction twice → write a skill.
→ Verbose/off-tone → edit soul.
→ New scheduled task → build skill first, then cron it.
→ Something breaks → check memory.md first (stale memory = #1 cause of weird behavior).
→ Dashboard opening: save as skill for 3-command future access.
→ Never paste API keys in chat. Use `hermes config set KEY value`.
→ Telegram = remote control (quick tasks, voice, crons). CLI = cockpit (deep work, coding). Don't vibe-code from Telegram — context rot invisible there.
→ Auto-compaction threshold ~136K tokens. When it fires, Hermes inserts fallback marker. Ask "explain this" if unclear.
→ Soul.md shapes personality per agent. This agent = terse/direct/no-fluff.
→ Skills need sharp YAML front matter. If agent doesn't invoke skill when expected, tell it: "Update YAML front matter so this triggers when I say X."