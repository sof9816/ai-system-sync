# GT AI System — Status Report

> Last updated: 2026-05-04 by pi.dev

## Dashboard URLs

| URL | What |
|-----|------|
| http://localhost:3000/3001 | Vite dev server (hot reload, proxies `/api` → 7373) |
| http://localhost:7373 | Backend serving built frontend + API |

## Verified Working

```bash
GET /api/health          → overall: ok, kimi_api_key: ok (51 chars)
GET /api/billing/balance → status: ok, balance: $12.45, currency: USD
GET /api/ios/projects    → projects: [CarPlaySounds]
POST /api/files/open     → opens Finder on macOS ✅
GET /api/agents          → 8 agents online
```

## Latest Changes (2026-05-04)

### Unified Prompt-Only Project Creation
**Before:** Two separate creation flows — General (name+description form) and iOS (prompt textarea)
**After:** Single prompt textarea for ALL projects. Type your idea, system auto-detects if it's iOS.

**Detection:** If prompt contains `ios`, `iphone`, `ipad`, `swiftui`, `swift`, `carplay`, `widgetkit`, `app store`, `xcode`, `uikit`, or `catalyst` → scaffolds as iOS project. Otherwise → general project.

### Fixed Issues
1. **Overview "New iOS App" button** — Was linking to deleted `/ios` route. Now links to `/projects`
2. **pi.dev error banner** — Now more prominent (darker red bg) with explicit dismiss button. Persists until user clears it.
3. **Unified project creation** — Single "New Project" button, single prompt textarea

### Obsidian Notes Updated
- `Hermes Vault/Hermes/agents/pi/memory.md` — Added CarPlaySounds project entry
- `Hermes Vault/Hermes/agents/pi/projects.md` — Full work log of dashboard overhaul

### Architecture Docs
- `dashboard/docs/ARCHITECTURE.md` — Complete system architecture, API routes, data models, design decisions

## CarPlaySounds App

```
projects/ios/CarPlaySounds/
├── Sources/
│   ├── Models/ (LocationTrigger, SoundProfile, WidgetConfig)
│   ├── Views/ (ContentView, SoundPickerView, WidgetGalleryView, CarPlayScene)
│   ├── ViewModels/ (LocationManager, SoundEngine, WidgetManager)
│   ├── Services/ (GeofenceService, AudioService)
│   └── Widgets/ (CarPlayWidget)
├── Resources/ (sound files + Assets.xcassets)
├── PROJECT.md
└── README.md
```

## How to Use

**Refresh your browser:**
```bash
open http://localhost:3000   # or 3001 if Vite picked it
```

Then **Cmd+Shift+R** (hard refresh).

### Projects Tab
- **Filter pills:** All | iOS | General
- **New Project** button → prompt textarea appears
- Type any idea (iOS app, web app, script, anything)
- Badge shows if it will scaffold as iOS or general
- **Create & Code** → pi.dev scaffolds + starts coding

### pi.dev Workshop
- Type a prompt (e.g. "Add dark mode toggle")
- Click **Run pi** on any project card
- Output appears below. Errors show in red banner.

### Project Card Actions
- **Run pi** — runs workshop prompt on this project
- **Open in Finder** — opens project folder in macOS Finder
- **View Spec** — scrollable modal with PROJECT.md (iOS only)
- **Delete** — removes project

---

**pi.dev is your lead developer and CTO.** 🚀
