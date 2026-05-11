# gt-centralized-system

> >

## Metadata

- **Version:** 1.0.0
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/gt-centralized-system/SKILL.md`

## Skill Body

# GT Centralized System

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GT DASHBOARD (UI)                         │
│         Control panel. One-click switches. Alerts.          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     HERMES (Brain)                          │
│    Orchestrator. Detects patterns. Self-upgrades. Cron.     │
│    Writes reasoning diary to Obsidian.                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌──────────┬─────────┴──────────┬──────────┐
        │          │                    │          │
        ▼          ▼                    ▼          ▼
   ┌────────┐ ┌─────────┐        ┌──────────┐ ┌────────┐
   │SKILLS  │ │ MEMORY  │        │ CONFIG   │ │PROJECTS│
   │Git Repo│ │Obsidian │        │Dashboard │ │Registry│
   │        │ │Vault    │        │DB + YAML │ │+ Manifest
   └────────┘ └─────────┘        └──────────┘ └────────┘
        │          │                    │          │
        ▼          ▼                    ▼          ▼
   ┌────────┐ ┌─────────┐        ┌──────────┐ ┌────────┐
   │pi.dev  │ │Agents   │        │Ghostty   │ │Any AI  │
   │Claude* │ │Swarm    │        │zshrc     │ │via     │
   │Kimi    │ │Dashboard│        │Hermes    │ │Adapter │
   └────────┘ └─────────┘        └──────────┘ └────────┘
```

## Components

| Component | Source of Truth | Mirror | Sync Trigger |
|-----------|----------------|--------|--------------|
| Skills | Git repo | Obsidian vault folder | Webhook on push |
| Memory | Obsidian vault | — | Real-time write |
| Config | Dashboard DB | Obsidian YAML + Git | On change |
| Secrets | Dashboard DB (encrypted) | Vault encrypted file | Manual export |
| Projects | Dashboard registry | .project.yaml in repo | On register |

### Skills: Single Source of Truth

**Anti-pattern**: Copy skills from repo to `~/.hermes/skills/` and `~/.agents/skills/` via rsync. Copies drift, get wiped on sync, and skills created directly in agent dirs disappear.

**Correct pattern**: Symlink agent skills dirs to the git repo. Both Hermes and pi.dev read directly from `gt-core/skills-repo/`.

```bash
# Remove copies (back up first)
mv ~/.hermes/skills ~/.hermes/skills.backup
mv ~/.agents/skills ~/.agents/skills.backup

# Create symlinks
ln -s /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo ~/.hermes/skills
ln -s /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo ~/.agents/skills
```

Hermes config: set `skills.external_dirs` to repo path so it resolves skills even without the symlink:
```bash
hermes config set skills.external_dirs '["/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo"]'
```

Sync script (`sync-skills.py`) detects symlinks and skips the copy step, still running validation and git pull.

**Rule**: All skills MUST be created in `gt-core/skills-repo/` and committed. Never create skills directly in `~/.hermes/skills/` or they will be lost on the next sync.

## Directory Structure

```
agent-home/
├── gt-core/
│   ├── skills-repo/              # Git repo with categorized skills
│   ├── config/
│   │   ├── gt-config.yaml        # Unified config (YAML)
│   │   └── schemas/
│   │       └── gt-config-schema.json
│   ├── scripts/
│   │   ├── validate-skills.py    # Validates all SKILL.md files
│   │   ├── sync-skills.py        # Webhook handler → syncs to agents
│   │   ├── bundle-skills.py     # Creates skill bundles for export
│   │   ├── apply-config.py       # Propagates config to all agents
│   │   ├── switch-provider.py    # One-click provider switch + rollback
│   │   ├── hermes-upgrade.py     # Self-upgrade: patterns, perf, deps
│   │   ├── hermes-diary.py       # Structured diary to Obsidian
│   │   ├── project-detect.py     # Auto-detects .project.yaml
│   │   ├── validate-manifest.py  # Validates project manifests
│   │   ├── export-to-claude.py   # Exports skills to CLAUDE.md
│   │   ├── integration-test.py   # Tests all components
│   │   └── setup-cron.py         # Installs maintenance cron jobs
│   ├── templates/
│   │   ├── skill-bundle.yaml
│   │   └── project-manifest.yaml
│   ├── schemas/
│   │   └── project-manifest-schema.json
│   ├── claude-export/            # Claude Code format exports
│   └── logs/                     # Cron job logs
├── dashboard/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── routers/
│   │   │   │   └── gt_core.py    # All GT API endpoints
│   │   │   ├── models.py         # GTConfig, Secret, GTProject
│   │   │   ├── schemas.py        # Pydantic schemas
│   │   │   └── database.py       # DB + inline migrations
│   │   └── data/
│   │       └── app.db            # SQLite database
│   └── frontend/
│       └── src/
│           ├── pages/
│           │   ├── GTCenter.tsx  # Main sci-fi dashboard
│           │   └── Secrets.tsx   # Secrets management
│           ├── components/
│           │   ├── StatusBar.tsx
│           │   ├── Sidebar.tsx
│           │   ├── HUDPanel.tsx
│           │   └── Layout.tsx
│           └── styles/
│               └── scifi.css     # Global sci-fi effects
└── docs/
    └── plans/
        └── 2026-05-08-gt-centralized-system.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/webhooks/skills-sync` | Git webhook → sync skills |
| GET | `/api/gt/config` | All config sections |
| PUT | `/api/gt/config/{section}` | Update config section |
| POST | `/api/gt/config/apply` | Propagate to agents |
| GET | `/api/gt/secrets` | List secrets (masked) |
| POST | `/api/gt/secrets` | Add secret (encrypted) |
| PUT | `/api/gt/secrets/{id}/activate` | Switch provider |
| GET | `/api/gt/projects` | List projects |
| POST | `/api/gt/projects` | Create project |
| POST | `/api/gt/projects/scan` | Auto-detect scan |

## Setup

### 1. Initialize Skills Repo
```bash
cd /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo
git init
git add -A
git commit -m "init: gt-skills repo"
```

### 2. Install Cron Jobs
```bash
cd /Users/gt/Public/MyFiles/agent-home
python3 gt-core/scripts/setup-cron.py --install
```

### 3. Run Integration Test
```bash
python3 gt-core/scripts/integration-test.py
```

### 4. Open Dashboard
```bash
cd /Users/gt/Public/MyFiles/agent-home/dashboard/frontend
npm run dev
# Open http://localhost:5173/gt-center
```

## Daily Workflow

1. **Morning**: Check dashboard GT Center page for health score
2. **Work**: Hermes auto-detects patterns, suggests skills
3. **Evening**: Diary writer logs day's activity to Obsidian
4. **Weekly**: Upgrade check suggests optimizations

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Skills not syncing | Run `python3 gt-core/scripts/sync-skills.py` |
| Config not applying | Check dashboard DB, run `apply-config.py --dry-run` |
| Provider switch failed | Check `provider-switches.md` in Obsidian for rollback |
| Webhook 500 | Git pull fails without remote — sync still works |
| Python 3.14 breaks pyyaml | Use dashboard venv: `dashboard/backend/venv/bin/python3` |

## Related Skills
- `frontend-developer` — React/Tailwind implementation
- `ui-ux-designer` — Sci-fi interface design
- `dashboard-architect` — Dashboard layout patterns
- `subagent-driven-development` — Multi-agent execution
- `pi-coding-agent` — pi.dev delegation patterns
