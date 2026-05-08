# Dashboard Overhaul Plan — 2025-05-06

## Scope

### In
- Fix config files for pi, hermes, dashboard with correct API keys
- Kimi Code: `sk-kimi-c73dtqTeMaJPt1fDUpwXNzeyRW6DhnwWgpGemyCaExfHDywwfZC8hd21ISf7c54h`
- Moonshot (legacy): `sk-QETaTm4aabse0Xp0BLdXFzDixP7gLq5SZcCRPsDsATSyTvbk`
- Combine Overview + Health tabs
- Combine Files + AI Config pages with file editing
- Add AI validator middleware for config updates
- Remove all backup configs
- Fix Ghostty terminal button to open new window
- Unify UI/UX across Hermes, Pi, Ghostty control pages
- Update Obsidian vault with system memory
- Clean agent-home structure

### Out
- Rewriting the entire backend from scratch
- Changing the database schema
- Adding new auth systems

---

## Action Items

### Phase 1: Config & Keys (Foundation)
- [x] Fix `dashboard/backend/.env` — correct KIMI_API_KEY to moonshot key
- [x] Fix `~/.hermes/.env` — add both keys
- [x] Verify `pi.json`, `hermes/config.json`, `~/.hermes/config.yaml`, `~/.pi/agent/auth.json` have correct keys
- [x] Remove `dashboard/data/config_backups/` entirely

### Phase 2: Backend Fixes
- [x] Fix Ghostty `open-ghostty` endpoint to spawn truly new windows
- [x] Add AI config validator in `config_manager.py` before apply
- [x] Update `billing.py` to read keys from correct env files
- [x] Ensure all backend routers read from unified config sources

### Phase 3: Frontend Restructure
- [x] Combine Overview + Health into single `Overview.tsx`
- [x] Remove Health route from Sidebar and App.tsx
- [x] Merge Files functionality into AI Config page
- [x] Add "Config Files" sub-tab in AI Config
- [x] Remove standalone Files route
- [x] Unify Hermes/Pi/Ghostty page layouts (same header pattern, colors, tab style)

### Phase 4: UI/UX Unification
- [x] Standardize control page headers (icon + title + subtitle + refresh/save buttons)
- [x] Standardize section tab bars (same active/hover styles)
- [x] Standardize color accents per page but same structure
- [x] Fix Sidebar to reflect new combined tabs

### Phase 5: Obsidian & Memory
- [x] Create/update system memory note in Obsidian
- [x] Document current config state
- [x] Ensure hermes memory references obsidian vault

### Phase 6: Cleanup
- [x] Verify agent-home directory structure is clean
- [x] Remove any dead files
- [x] Test dashboard builds and runs
