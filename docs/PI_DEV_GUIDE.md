# GT Centralized System — pi.dev Integration Guide

> **Version:** 1.0  
> **Updated:** 2026-05-09  
> **Path:** `/Users/gt/Public/MyFiles/agent-home/docs/PI_DEV_GUIDE.md`

---

## 1. Overview

The **GT Centralized System** is a unified AI operations platform that connects multiple agents, skills, projects, and tools under one roof. It lives at:

```
/Users/gt/Public/MyFiles/agent-home/
```

**pi.dev** is the lead coding agent / CTO within this system. It writes code, reviews architecture, scaffolds projects, and works with the GT skill registry. This guide tells pi.dev how to read from and write to the GT system.

### What the system does
- **Skills repo** (`gt-core/skills-repo/`): Centralized, categorized skill library (200+ skills)
- **Config hub** (`gt-core/config/gt-config.yaml`): Single source of truth for AI providers, agents, integrations
- **Project registry** (`projects/` + dashboard API): Tracks active projects and their metadata
- **Agent swarm** (`agents/` + `swarm/`): 8 specialized C-suite agents (CTO, CFO, COO, etc.)
- **Dashboard** (`dashboard/`): Web UI on http://localhost:7373
- **Obsidian vault** (`Hermes Vault/`): Persistent memory and diary

### How pi.dev fits in
- pi.dev reads skills from `gt-core/skills-repo/` before starting work
- pi.dev reads config from `gt-core/config/gt-config.yaml` to know which provider/model to use
- pi.dev can register new projects via `project-detect.py`
- pi.dev can add new skills to `gt-core/skills-repo/` and run validation
- pi.dev can call dashboard APIs to update project status, secrets, or config

---

## 2. Directory Structure

```
/Users/gt/Public/MyFiles/agent-home/
├── README.md                          # System overview & quick start
├── setup.sh                           # Reproducible installer
├── run-dashboard.sh                   # Start web dashboard
│
├── gt-core/                           # ← CORE SYSTEM
│   ├── config/
│   │   ├── gt-config.yaml             # Unified config (providers, agents, integrations)
│   │   └── schemas/
│   │       └── gt-config-schema.json  # JSON Schema for validation
│   ├── skills-repo/                   # Centralized skill library (Git-tracked)
│   │   ├── apple/
│   │   ├── architecture/
│   │   ├── autonomous-ai-agents/
│   │   ├── creative/
│   │   ├── data-science/
│   │   ├── devops/
│   │   ├── dogfood/
│   │   ├── email/
│   │   ├── gaming/
│   │   ├── github/
│   │   ├── ios-development/
│   │   ├── mcp/
│   │   ├── media/
│   │   ├── mlops/
│   │   ├── note-taking/
│   │   ├── productivity/
│   │   ├── red-teaming/
│   │   ├── research/
│   │   ├── smart-home/
│   │   ├── social-media/
│   │   ├── software-development/
│   │   ├── superpowers/
│   │   └── yuanbao/
│   ├── scripts/                       # Automation scripts
│   │   ├── apply-config.py            # Propagate config to all agents
│   │   ├── switch-provider.py         # Switch AI provider with rollback
│   │   ├── project-detect.py          # Auto-detect & register projects
│   │   ├── sync-skills.py             # Sync skills repo → agent skill dirs
│   │   ├── validate-config.py         # Validate gt-config.yaml against schema
│   │   ├── validate-skills.py         # Validate all SKILL.md files
│   │   ├── validate-manifest.py       # Validate project manifest YAML
│   │   ├── bundle-skills.py           # Bundle skills into single YAML
│   │   ├── export-to-claude.py        # Export skills to Claude Code format
│   │   ├── migrate-skills.py          # Migrate old skills into skills-repo
│   │   ├── hermes-upgrade.py          # Self-upgrade suggestions for Hermes
│   │   ├── hermes-diary.py            # Write daily diary to Obsidian
│   │   ├── integration-test.py        # Full system health check
│   │   └── setup-cron.py              # Install GT cron jobs
│   ├── bundles/                       # Pre-built skill bundles
│   ├── templates/
│   │   ├── project-manifest.yaml      # Template for new projects
│   │   └── skill-bundle.yaml          # Template for skill bundles
│   ├── schemas/
│   │   └── project-manifest-schema.json
│   ├── logs/                          # Cron & script logs
│   ├── test-skills/                   # Test fixtures for validation
│   └── claude-export/                 # Exported Claude Code skills
│
├── agents/                            # Agent definitions (YAML)
│   ├── architect.yaml
│   ├── cfo.yaml
│   ├── cmo.yaml
│   ├── coo.yaml
│   ├── cto.yaml
│   ├── orchestrator.yaml
│   ├── researcher.yaml
│   └── reviewer.yaml
│
├── swarm/                             # Swarm orchestrator
│   ├── swarm.py
│   └── agent
│
├── skills/                            # Legacy flat skills (migrated to gt-core/skills-repo)
│
├── hermes/                            # Hermes config & memory
│   ├── config.json
│   └── memory/
│
├── pi/                                # Pi coding agent config
│   ├── pi.json
│   └── projects.json
│
├── projects/                          # Active project scaffolds
│   └── ios/
│       └── CarPlaySounds/
│           ├── PROJECT.md
│           └── project.yml
│
├── dashboard/                         # Web dashboard (FastAPI + React)
│   ├── backend/
│   ├── frontend/
│   ├── data/
│   └── logs/
│
├── daily-digest/                      # Daily digest builder outputs
│
├── config-backups/                    # Auto-generated config backups
│
├── memories/                          # Session memories
│
└── Hermes Vault/                          # Obsidian vault (persistent memory)
    └── hermes/
        ├── system/
        ├── diary/
        └── agents/
```

---

## 3. How to Read / Write Skills

### Location
```
gt-core/skills-repo/<category>/<skill-name>/SKILL.md
```

### Structure of a SKILL.md
Every skill **must** have YAML frontmatter:

```markdown
---
name: swiftui-expert
description: |
  Expert-level SwiftUI development skill covering state management,
  performance optimization, and custom view composition.
category: ios-development
tags: [swiftui, ios, ui]
version: "1.0.0"
author: gt
---

# SwiftUI Expert

... skill content ...
```

### Read a skill
```bash
# Direct file read
cat /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/ios-development/swiftui-expert/SKILL.md

# Or via Python
python3 -c "
from pathlib import Path
skill = Path('/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/ios-development/swiftui-expert/SKILL.md')
print(skill.read_text())
"
```

### Write a new skill
1. Pick or create a category directory under `gt-core/skills-repo/`
2. Create a subdirectory with kebab-case name: `my-new-skill/`
3. Write `SKILL.md` with valid YAML frontmatter
4. Run validation:
   ```bash
   cd /Users/gt/Public/MyFiles/agent-home
   python3 gt-core/scripts/validate-skills.py gt-core/skills-repo
   ```
5. Commit to Git:
   ```bash
   cd gt-core/skills-repo
   git add .
   git commit -m "feat: add my-new-skill"
   ```

### Sync skills to agents
```bash
python3 gt-core/scripts/sync-skills.py
```
This pulls latest from `skills-repo`, validates, and copies to `~/.hermes/skills/` and `~/.agents/skills/`.

---

## 4. How to Read Config

### Primary config file
```
/Users/gt/Public/MyFiles/agent-home/gt-core/config/gt-config.yaml
```

### Current config (as of 2026-05-09)
```yaml
ai:
  primary_provider: kimi-coding
  backup_provider: openrouter
  model: kimi-k2.6
  thinking: medium

providers:
  kimi-coding:
    base_url: https://api.moonshot.cn/v1
    api_key_env: KIMI_API_KEY
    active: true
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key_env: OPENROUTER_API_KEY
    active: true
  anthropic:
    base_url: https://api.anthropic.com/v1
    api_key_env: ANTHROPIC_API_KEY
    active: false

agents:
  hermes:
    skills_dir: /Users/gt/Public/MyFiles/agent-home/gt-core/skills/hermes
    config_file: /Users/gt/Public/MyFiles/agent-home/gt-core/config/hermes.yaml
  pi:
    skills_dir: /Users/gt/Public/MyFiles/agent-home/gt-core/skills/pi
    config_file: /Users/gt/Public/MyFiles/agent-home/gt-core/config/pi.yaml

integrations:
  obsidian:
    vault_path: /Users/gt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault
  ghostty:
    config_path: /Users/gt/Library/Application Support/com.mitchellh.ghostty/config
  claude_code:
    enabled: true

secrets:
  rotation_policy: 90d
  vault_file: /Users/gt/Public/MyFiles/agent-home/gt-core/secrets/vault.yaml
```

### Read via API
```bash
curl -s http://localhost:7373/api/gt/config | python3 -m json.tool
```

### Validate config
```bash
python3 gt-core/scripts/validate-config.py
```

---

## 5. How to Use Scripts

### apply-config.py
Propagates unified config to all agent config files.

```bash
# Preview changes without applying
python3 gt-core/scripts/apply-config.py --dry-run

# Apply changes (backs up every file before modifying)
python3 gt-core/scripts/apply-config.py --apply
```

**Targets:**
- `~/.hermes/config.yaml`
- `~/.pi/agent/settings.json`
- `~/.config/ghostty/config`
- `~/.zshrc` (GT aliases block)
- `dashboard/backend/.env`

### switch-provider.py
Switch AI provider with rollback support.

```bash
# Switch to openrouter (dry run)
python3 gt-core/scripts/switch-provider.py openrouter --dry-run

# Switch to openrouter (apply)
python3 gt-core/scripts/switch-provider.py openrouter
```

**What it does:**
1. Reads `gt-config.yaml`
2. Tests API key against provider
3. Backs up Hermes & Pi configs
4. Updates provider in all configs
5. Logs switch to Obsidian vault

### project-detect.py
Auto-detect project type and register with dashboard.

```bash
# Detect project in current directory
python3 gt-core/scripts/project-detect.py .

# Detect and register via dashboard API
python3 gt-core/scripts/project-detect.py . --register
```

**Detection logic:**
- Looks for `.project.yaml`
- If not found, guesses from files (`Package.swift` → iOS, `package.json` → Node, etc.)
- Generates suggested `.project.yaml`

### sync-skills.py
Triggered by Git webhook or run manually.

```bash
# Manual sync
python3 gt-core/scripts/sync-skills.py

# With webhook payload
 cat webhook.json | python3 gt-core/scripts/sync-skills.py
```

### validate-skills.py
Validate all SKILL.md files in a directory.

```bash
python3 gt-core/scripts/validate-skills.py gt-core/skills-repo
```

**Checks:**
- YAML frontmatter present
- Required fields: `name`, `description`
- No broken quoted strings
- No duplicate names
- Valid directory naming

### integration-test.py
Full system health check.

```bash
python3 gt-core/scripts/integration-test.py
```

**Tests:**
1. Skills repo validation
2. Config API responds
3. Projects API responds
4. Secrets API responds
5. Webhook endpoint responds
6. Today's diary file exists
7. Cron jobs installed
8. Dashboard backend/frontend running

---

## 6. API Endpoints pi.dev Can Call

The dashboard backend exposes these endpoints (port `7373`):

### Config
```bash
GET  /api/gt/config          # Full gt-config.yaml as JSON
POST /api/gt/config          # Update config (partial)
```

### Projects
```bash
GET    /api/gt/projects              # List all projects
POST   /api/gt/projects              # Register new project
GET    /api/gt/projects/{id}         # Get project details
PUT    /api/gt/projects/{id}       # Update project
DELETE /api/gt/projects/{id}       # Delete project
```

### Secrets
```bash
GET    /api/gt/secrets               # List secrets (masked)
POST   /api/gt/secrets               # Add secret
PUT    /api/gt/secrets/{id}          # Update secret
DELETE /api/gt/secrets/{id}          # Delete secret
```

### Skills
```bash
GET /api/gt/skills                  # List all skills
GET /api/gt/skills/{category}       # List skills in category
GET /api/gt/skills/search?q=swift   # Search skills
```

### Webhooks
```bash
POST /api/webhooks/skills-sync      # Trigger skills sync
POST /api/webhooks/config-update    # Trigger config reload
```

### Health
```bash
GET /api/health                     # System health status
```

### Example: Register a project via API
```bash
curl -X POST http://localhost:7373/api/gt/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyNewApp",
    "type": "ios",
    "description": "A new SwiftUI app",
    "skills": ["ios-development/swiftui-expert"],
    "agents": ["cto", "reviewer"]
  }'
```

---

## 7. How to Add a New Skill (Workflow)

### Step-by-step

1. **Choose category**
   ```bash
   ls /Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/
   ```
   If no category fits, create one: `mkdir gt-core/skills-repo/new-category`

2. **Create skill directory**
   ```bash
   mkdir gt-core/skills-repo/software-development/my-skill
   ```
   Use kebab-case names.

3. **Write SKILL.md**
   ```markdown
   ---
   name: my-skill
   description: |
     A clear, concise description of what this skill does.
   category: software-development
   tags: [python, automation]
   version: "1.0.0"
   author: gt
   ---

   # My Skill

   ## Overview
   ...

   ## Usage
   ...
   ```

4. **Validate**
   ```bash
   python3 gt-core/scripts/validate-skills.py gt-core/skills-repo
   ```

5. **Bundle (optional)**
   ```bash
   python3 gt-core/scripts/bundle-skills.py my-bundle \
     software-development/my-skill \
     software-development/another-skill
   ```

6. **Export to Claude (optional)**
   ```bash
   python3 gt-core/scripts/export-to-claude.py --bundle my-skill,another-skill
   ```

7. **Commit**
   ```bash
   cd gt-core/skills-repo
   git add .
   git commit -m "feat: add my-skill"
   ```

8. **Sync**
   ```bash
   python3 gt-core/scripts/sync-skills.py
   ```

---

## 8. How to Register a Project

### Method A: project-detect.py (recommended)
```bash
cd /path/to/project
python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/project-detect.py . --register
```

### Method B: Manual manifest
Create `.project.yaml` in project root:

```yaml
project:
  name: "CarPlaySounds"
  type: "ios"
  description: "CarPlay sounds app with widgets"

gt_system:
  skills:
    - "ios-development/swiftui-expert"
    - "ios-development/swift-concurrency-pro"
  agents:
    - "cto"
    - "reviewer"
  memory_vault: "obsidian://vault/projects/carplay-sounds"
  config_profile: "default"

dependencies:
  swift_version: "5.9"
  xcode_version: "15.0"
  ios_deployment_target: "16.0"

team:
  lead: "cto"
  reviewer: "reviewer"
```

Then validate:
```bash
python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/validate-manifest.py .project.yaml
```

And register:
```bash
curl -X POST http://localhost:7373/api/gt/projects \
  -H "Content-Type: application/json" \
  -d @.project.yaml
```

---

## 9. Troubleshooting

### "Config API not responding"
```bash
# Check if dashboard backend is running
curl -s http://localhost:7373/api/health

# If not running, start it
cd /Users/gt/Public/MyFiles/agent-home/dashboard/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 7373 --reload
```

### "Skills validation failed"
```bash
# Run validator with verbose output
python3 gt-core/scripts/validate-skills.py gt-core/skills-repo

# Common issues:
# - Missing YAML frontmatter
# - Broken quoted strings in description (use | or > for multi-line)
# - Duplicate skill names
# - Invalid directory names (must be kebab-case)
```

### "Provider switch failed"
```bash
# Check API key is set
echo $KIMI_API_KEY

# Check provider is defined in gt-config.yaml
cat gt-core/config/gt-config.yaml | grep -A3 "kimi-coding"

# Rollback from backup
ls -la ~/.hermes/config.yaml.bak.*
cp ~/.hermes/config.yaml.bak.20250509_120000 ~/.hermes/config.yaml
```

### "Sync skills not updating"
```bash
# Check Git status
cd gt-core/skills-repo && git status

# Manual pull
git pull --ff-only

# Run sync manually
python3 gt-core/scripts/sync-skills.py
```

### "Cron jobs not running"
```bash
# Check if GT cron jobs are installed
python3 gt-core/scripts/setup-cron.py --list

# Install them
python3 gt-core/scripts/setup-cron.py --install

# View logs
tail -f /Users/gt/Public/MyFiles/agent-home/gt-core/logs/cron-skills-sync.log
tail -f /Users/gt/Public/MyFiles/agent-home/gt-core/logs/cron-hermes-upgrade.log
```

### Dashboard frontend not loading
```bash
# Check frontend process
curl -s http://localhost:3000

# Restart frontend
cd /Users/gt/Public/MyFiles/agent-home/dashboard/frontend
npm run dev
```

### General debug
```bash
# Full system health check
python3 gt-core/scripts/integration-test.py

# Check all logs
ls -la /Users/gt/Public/MyFiles/agent-home/gt-core/logs/
ls -la /Users/gt/Public/MyFiles/agent-home/dashboard/logs/
```

---

## 10. Quick Reference Card

| Task | Command |
|------|---------|
| Read config | `cat gt-core/config/gt-config.yaml` |
| Validate config | `python3 gt-core/scripts/validate-config.py` |
| Apply config | `python3 gt-core/scripts/apply-config.py --apply` |
| Switch provider | `python3 gt-core/scripts/switch-provider.py openrouter` |
| List skills | `ls gt-core/skills-repo/` |
| Validate skills | `python3 gt-core/scripts/validate-skills.py gt-core/skills-repo` |
| Sync skills | `python3 gt-core/scripts/sync-skills.py` |
| Add skill | Write to `gt-core/skills-repo/<category>/<name>/SKILL.md`, then validate + commit |
| Detect project | `python3 gt-core/scripts/project-detect.py . --register` |
| Validate manifest | `python3 gt-core/scripts/validate-manifest.py .project.yaml` |
| Health check | `python3 gt-core/scripts/integration-test.py` |
| Install cron | `python3 gt-core/scripts/setup-cron.py --install` |
| Dashboard | http://localhost:7373 |
| Obsidian vault | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes Vault` |

---

## 11. Contact & Updates

- This guide is maintained in `/Users/gt/Public/MyFiles/agent-home/docs/PI_DEV_GUIDE.md`
- System updates are tracked in `Hermes Vault/Hermes/system/upgrade-suggestions.md`
- Daily diary entries go to `Hermes Vault/Hermes/diary/`
- For issues, run `integration-test.py` and check logs

**When in doubt, read the README:** `/Users/gt/Public/MyFiles/agent-home/README.md`
