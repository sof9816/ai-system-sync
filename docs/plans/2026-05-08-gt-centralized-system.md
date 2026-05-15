# GT Centralized System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **For Hermes:** Dispatch subagent per task. Parallel where possible.

**Goal:** Build GT Centralized System — one source of truth for skills, memory, config, secrets, projects across all AI agents.

**Architecture:** Dashboard DB = source of truth. Obsidian = human-readable mirror. Git = backup + distribution. Hermes = brain/orchestrator.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, React 19, Git, Obsidian Markdown.

**Workdir:** `/Users/gt/Public/MyFiles/agent-home`

---

## Phase 1: Skills Git Repo + Webhook Sync

### Task 1.1: Initialize gt-skills Git Repo

**Files:**
- Create: `gt-core/skills-repo/.git/`
- Create: `gt-core/skills-repo/README.md`
- Create: `gt-core/skills-repo/.gitignore`

**Step 1:** Init repo
```bash
cd /Users/gt/Public/MyFiles/agent-home
git init gt-core/skills-repo
cd gt-core/skills-repo
git remote add origin https://github.com/gt/gt-skills.git  # placeholder
```

**Step 2:** Write README
- Purpose: Centralized skills vault for GT AI System
- Structure: category/skill-name/SKILL.md
- Contribution: How to add skills
- Sync: Webhook to Hermes

**Step 3:** Write .gitignore
```
*.pyc
__pycache__/
.drafts/
```

**Step 4:** Commit
```bash
git add README.md .gitignore
git commit -m "init: gt-skills repo"
```

---

### Task 1.2: Migrate Existing Skills to Repo

**Files:**
- Create: `gt-core/skills-repo/{categories}/`
- Read: `agent-home/skills/*.md`
- Read: `~/.hermes/skills/**/SKILL.md`

**Step 1:** Map existing skills to categorized structure
```
gt-core/skills-repo/
├── ios-development/
│   ├── swiftui-expert/
│   ├── core-data-expert/
│   └── ...
├── software-development/
│   ├── clean-code/
│   └── testing-patterns/
├── superpowers/
│   ├── brainstorming/
│   └── writing-plans/
└── ...
```

**Step 2:** Copy each skill with proper YAML frontmatter
- Name must match directory name (PI compatibility)
- Description uses folded block (`>`)
- All YAML valid

**Step 3:** Validate with script
```bash
python3 gt-core/scripts/validate-skills.py gt-core/skills-repo/
```

**Step 4:** Commit
```bash
git add -A
git commit -m "migrate: all existing skills from hermes + agent-home"
```

---

### Task 1.3: Create Skill Validation Script

**Files:**
- Create: `gt-core/scripts/validate-skills.py`

**Step 1:** Write validation script
- Check YAML frontmatter valid
- Check `name` matches parent directory
- Check no duplicate skill names
- Check description uses proper multi-line format
- Check required fields: name, description

**Step 2:** Test on existing skills
```bash
python3 gt-core/scripts/validate-skills.py gt-core/skills-repo/
```
Expected: All skills pass or list of errors

**Step 3:** Commit
```bash
git add gt-core/scripts/validate-skills.py
git commit -m "feat: skill validation script"
```

---

### Task 1.4: Create Webhook Sync Script

**Files:**
- Create: `gt-core/scripts/sync-skills.py`
- Modify: `dashboard/backend/app/routers/gt_core.py`

**Step 1:** Write sync script
- Input: Git webhook payload (push event)
- Action: Pull latest skills from repo
- Validate with validate-skills.py
- Sync to `~/.hermes/skills/` (rsync or copy)
- Sync to `~/.agents/skills/` (rsync or copy)
- Log to Obsidian

**Step 2:** Add webhook endpoint to dashboard
```python
@router.post("/webhooks/skills-sync")
async def skills_sync_webhook(payload: dict):
    # Trigger sync script
    # Return 200 on success, 500 on error
```

**Step 3:** Test webhook
```bash
curl -X POST http://localhost:7373/api/webhooks/skills-sync \
  -H "Content-Type: application/json" \
  -d '{"ref": "refs/heads/main"}'
```

**Step 4:** Commit
```bash
git add gt-core/scripts/sync-skills.py
git commit -m "feat: skill webhook sync"
```

---

### Task 1.5: Create Skill Bundle System

**Files:**
- Create: `gt-core/scripts/bundle-skills.py`
- Create: `gt-core/templates/skill-bundle.yaml`

**Step 1:** Write bundle script
- Input: List of skill names
- Output: Single YAML bundle file
- Use case: Export bundle for Claude Code, new project setup

**Step 2:** Write bundle template
```yaml
bundle:
  name: "ios-dev-bundle"
  description: "iOS development essentials"
  skills:
    - ios-development/swiftui-expert
    - ios-development/core-data-expert
    - ios-development/swift-concurrency
  version: "1.0.0"
```

**Step 3:** Test bundle creation
```bash
python3 gt-core/scripts/bundle-skills.py ios-dev-bundle \
  ios-development/swiftui-expert \
  ios-development/core-data-expert
```

**Step 4:** Commit
```bash
git add -A
git commit -m "feat: skill bundle system"
```

---

## Phase 2: Unified Config System

### Task 2.1: Create GT Config Schema

**Files:**
- Create: `gt-core/config/gt-config.yaml`
- Create: `gt-core/config/schemas/gt-config-schema.json`

**Step 1:** Write unified config YAML
- Section: ai (provider, model, thinking)
- Section: providers (kimi-coding, openrouter, etc.)
- Section: agents (hermes, pi, paths)
- Section: integrations (obsidian, ghostty, claude_code)
- Section: secrets (rotation_policy, vault_file)

**Step 2:** Write JSON schema for validation
- All fields typed
- Required vs optional
- Enum values (thinking levels, provider names)

**Step 3:** Validate schema
```bash
python3 -c "import yaml, jsonschema; ..."
```

**Step 4:** Commit
```bash
git add -A
git commit -m "feat: unified config schema"
```

---

### Task 2.2: Dashboard DB Models for Config

**Files:**
- Create: `dashboard/backend/app/models/gt_core.py`
- Modify: `dashboard/backend/app/database.py`

**Step 1:** Add GTConfig model
```python
class GTConfig(Base):
    __tablename__ = "gt_configs"
    id = Column(Integer, primary_key=True)
    section = Column(String)  # "ai", "providers", "agents"
    key = Column(String)
    value = Column(JSON)
    updated_at = Column(DateTime)
```

**Step 2:** Add migration
```bash
alembic revision -m "add gt_config table"
```

**Step 3:** Test migration
```bash
alembic upgrade head
```

---

### Task 2.3: Config API Endpoints

**Files:**
- Create: `dashboard/backend/app/routers/gt_core.py`
- Modify: `dashboard/backend/app/main.py`

**Step 1:** Write CRUD endpoints
```python
@router.get("/config")
async def get_config() -> dict

@router.put("/config/{section}")
async def update_config(section: str, data: dict)

@router.post("/config/apply")
async def apply_config()  # Propagate to all agents
```

**Step 2:** Add to main.py
```python
app.include_router(gt_core.router, prefix="/api/gt")
```

**Step 3:** Test endpoints
```bash
curl http://localhost:7373/api/gt/config
curl -X PUT http://localhost:7373/api/gt/config/ai \
  -H "Content-Type: application/json" \
  -d '{"model": "kimi-for-coding"}'
```

---

### Task 2.4: Config Propagation Script

**Files:**
- Create: `gt-core/scripts/apply-config.py`

**Step 1:** Write propagation script
- Read from dashboard DB API
- Write to:
  - `~/.hermes/config.yaml`
  - `~/.pi/agent/settings.json`
  - `~/.config/ghostty/config`
  - `~/.zshrc`
  - `dashboard/backend/.env`
- Restart services if needed
- Log to Obsidian

**Step 2:** Test propagation
```bash
python3 gt-core/scripts/apply-config.py --dry-run
python3 gt-core/scripts/apply-config.py --apply
```

**Step 3:** Commit
```bash
git add -A
git commit -m "feat: config propagation script"
```

---

### Task 2.5: GT Config UI Page

**Files:**
- Create: `dashboard/frontend/src/pages/GTCore.tsx`
- Modify: `dashboard/frontend/src/App.tsx`

**Step 1:** Create React component
- Sections: AI, Providers, Agents, Integrations
- Form fields for each config value
- "Apply" button triggers propagation
- "Export to Obsidian" button

**Step 2:** Add route
```tsx
<Route path="/gt-core" element={<GTCore />} />
```

**Step 3:** Test UI
- Open dashboard
- Navigate to GT Core page
- Change a value, click Apply
- Verify config files updated

---

## Phase 3: Project Registry + Auto-Detect

### Task 3.1: Project Manifest Schema

**Files:**
- Create: `gt-core/templates/project-manifest.yaml`
- Create: `gt-core/schemas/project-manifest-schema.json`

**Step 1:** Write manifest template
```yaml
project:
  name: ""
  type: ""  # ios, web, python, etc.
  description: ""
  gt_system:
    skills: []
    agents: []
    memory_vault: ""
    config_profile: ""
```

**Step 2:** Write JSON schema

**Step 3:** Test validation
```bash
python3 -c "import yaml, jsonschema; ..."
```

---

### Task 3.2: Dashboard DB Models for Projects

**Files:**
- Modify: `dashboard/backend/app/models/gt_core.py`

**Step 1:** Add Project model
```python
class Project(Base):
    __tablename__ = "gt_projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    path = Column(String)
    type = Column(String)
    manifest = Column(JSON)
    status = Column(String)  # active, archived
    created_at = Column(DateTime)
```

**Step 2:** Add migration

**Step 3:** Test

---

### Task 3.3: Auto-Detect Script

**Files:**
- Create: `gt-core/scripts/project-detect.py`

**Step 1:** Write detection script
- Scan directory for `.project.yaml`
- Read manifest
- Validate against schema
- Register in dashboard DB
- Pull skills from gt-skills
- Create Obsidian vault folder

**Step 2:** Test
```bash
python3 gt-core/scripts/project-detect.py ~/Projects/myapp
```

---

### Task 3.4: Projects UI Page

**Files:**
- Create: `dashboard/frontend/src/pages/Projects.tsx`

**Step 1:** Create React component
- List all projects
- Show status, type, agents assigned
- "Scan for new projects" button
- "Create project" button (generates manifest)

---

## Phase 4: Secrets Vault + Provider Switch

### Task 4.1: Secrets DB Model

**Files:**
- Modify: `dashboard/backend/app/models/gt_core.py`

**Step 1:** Add Secret model
```python
class Secret(Base):
    __tablename__ = "gt_secrets"
    id = Column(Integer, primary_key=True)
    name = Column(String)  # "kimi-coding", "openrouter"
    key_encrypted = Column(String)  # Fernet encrypted
    status = Column(String)  # active, standby, deprecated
    provider = Column(String)
    last_tested = Column(DateTime)
```

**Step 2:** Add migration

---

### Task 4.2: Secrets API Endpoints

**Files:**
- Modify: `dashboard/backend/app/routers/gt_core.py`

**Step 1:** Add endpoints
```python
@router.get("/secrets")
@router.post("/secrets")
@router.put("/secrets/{id}/activate")
@router.post("/secrets/{id}/test")
```

**Step 2:** Add encryption/decryption
- Use Fernet from cryptography library
- Key from env var `GT_ENCRYPTION_KEY`

---

### Task 4.3: Provider Switch Script

**Files:**
- Create: `gt-core/scripts/switch-provider.py`

**Step 1:** Write switch script
- Input: New provider name
- Action:
  - Deactivate current provider
  - Activate new provider
  - Update all config files
  - Test connectivity with ping
  - Restart agents
- Log to Obsidian

**Step 2:** Test
```bash
python3 gt-core/scripts/switch-provider.py openrouter
```

---

### Task 4.4: Secrets UI Page

**Files:**
- Create: `dashboard/frontend/src/pages/Secrets.tsx`

**Step 1:** Create React component
- List all secrets (masked)
- Add new secret form
- "Test" button per secret
- "Switch to this provider" button
- Audit log view

---

## Phase 5: Hermes Self-Upgrade Loop

### Task 5.1: Pattern Detection Script

**Files:**
- Create: `gt-core/scripts/self-upgrade.py`

**Step 1:** Write pattern detection
- Read task history from Obsidian diary
- Count repeated task types
- If count >= 3 → flag as pattern
- Draft skill in `gt-skills/.drafts/`

**Step 2:** Write config optimization
- Read performance data (token usage, time per task)
- Compare against config settings
- Suggest tweaks

**Step 3:** Write dependency tracker
- Check versions of pi, dashboard, plugins
- Compare against latest available
- Alert if outdated

---

### Task 5.2: Diary Writer

**Files:**
- Create: `gt-core/scripts/write-diary.py`

**Step 1:** Write diary entry
- Date: YYYY-MM-DD
- Tasks completed
- Patterns detected
- Suggestions made
- Config changes
- Provider status

**Step 2:** Save to Obsidian
```
Hermes Vault/Hermes/diary/2026-05-08.md
```

---

### Task 5.3: Cron Job Setup

**Files:**
- Modify: `~/.hermes/cron.yaml` or Hermes cron system

**Step 1:** Add cron job
```yaml
cron:
  - name: "hermes-self-upgrade"
    schedule: "0 */6 * * *"  # Every 6 hours
    command: "python3 /Users/gt/Public/MyFiles/agent-home/gt-core/scripts/self-upgrade.py"
```

---

## Phase 6: Claude Code Adapter

### Task 6.1: Export Script

**Files:**
- Create: `gt-core/scripts/export-claude.py`

**Step 1:** Write export script
- Read skills from gt-skills
- Convert to CLAUDE.md format
- Convert to .cursorrules format
- Write to `gt-core/export/claude/`

**Step 2:** Test
```bash
python3 gt-core/scripts/export-claude.py
```

---

### Task 6.2: Export UI Button

**Files:**
- Modify: `dashboard/frontend/src/pages/GTCore.tsx`

**Step 1:** Add "Export for Claude" button
- Triggers export script
- Shows download link
- Logs last export time

---

## Phase 7: Documentation + Integration Test

### Task 7.1: Update README

**Files:**
- Modify: `agent-home/README.md`

**Step 1:** Add GT Core section
- What is GT Core
- How to use
- Architecture diagram
- Quick start

---

### Task 7.2: Write Integration Tests

**Files:**
- Create: `gt-core/tests/test_skills_sync.py`
- Create: `gt-core/tests/test_config_propagation.py`
- Create: `gt-core/tests/test_project_detect.py`

**Step 1:** Write tests
- Test skill sync webhook
- Test config propagation
- Test project auto-detect
- Test provider switch

---

### Task 7.3: End-to-End Test

**Step 1:** Full system test
1. Add new skill to gt-skills
2. Git push → webhook → sync to agents
3. Change config in dashboard → propagate
4. Clone test project → auto-detect
5. Switch provider → verify all agents updated

---

## Commit Strategy

Each task commits separately. Phase commits tagged:
- `p1-skills-repo`
- `p2-config-system`
- `p3-project-registry`
- `p4-secrets-vault`
- `p5-self-upgrade`
- `p6-claude-adapter`
- `p7-docs-tests`

---

## Testing Checkpoints

After each phase:
1. Run validation scripts
2. Test API endpoints
3. Verify UI renders
4. Check Obsidian logs
5. GT approval before next phase
