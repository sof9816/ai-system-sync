Obsidian: Hermes Vault at ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes/Hermes is the AI docs source of truth. GT Vault is general knowledge only.
§
MyFiles directory is /Users/gt/Public/MyFiles (~57 GB). Now organized into 11 numbered category folders (01-Work, 02-Flutter, 03-iOS-Swift, 04-Design, 05-Crypto-Web3, 06-GameDev, 07-Python-Automation, 08-Web-Node, 09-Security-Research, 10-Archives, 99-Misc). Contains sensitive files: tokens.json and Important Stuff/ with passwords/keys in 99-Misc.
§
Ghostty config on macOS is actively used at ~/.config/ghostty/config (not just ~/Library/Application Support/com.mitchellh.ghostty/config). When editing Ghostty settings, patch ~/.config/ghostty/config first.
§
System Python 3 default is Homebrew 3.14.2, which breaks pydantic-core (PyO3 max 3.13). For any Python project using FastAPI/SQLAlchemy/pydantic, must explicitly use `/opt/homebrew/bin/python3.11` when creating venvs. Available: python3.11, python3.13 (both OK), python3.14 (broken for pydantic).
§
pi.dev chokes on large prompts. Use task files <3000 chars. Game dev: check git, grill-me, Obsidian plan, pi.dev agents max 3, check .cursor/rules/. Final Escape Godot at /Users/gt/Public/MyFiles/06-GameDev/final-escape-g. Test screens: debug-only, spawn near ship, auto-collect to test effects. Fullscreen on desktop: move window_set_mode outside is_mobile_device() guard.
§
Windows home PC: 192.168.68.113. WSL2 Ubuntu via port 2222. User gt, pass 1234. Migration package at /Users/gt/Public/MyFiles/agent-home/windows-migration/.
§
GT Core skills repo is single source of truth. Hermes (`~/.hermes/skills/`) and pi.dev (`~/.agents/skills/`) are symlinks to `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/`. `skills.external_dirs` also points to repo. Sync script detects symlinks and skips copy. All skills must be created in repo and committed.
§
Newsletter/PDF pattern: "articles get cut off" = use jsPDF per-article rendering. Each article = own A4 page. Never split across pages. Card chaos fix = add `.article-card` border + padding, increase grid gaps to 1.5-2.5rem, section margin to 3rem.