# game-dev-orchestration

> Orchestrate game development projects (especially pygame/Godot) using Hermes + pi.dev swarm. Covers: reconnaissance, grill-me planning, pi.dev task file creation, Obsidian documentation, and build verification.

## Metadata

- **Version:** 1.0.0
- **Author:** Hermes Agent
- **License:** MIT
- **Tags:** game-dev, pygame, godot, swarm, pi.dev, orchestration
- **Related Skills:** swarm-orchestration, pi-coding-agent, grill-me, obsidian
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/gaming/game-dev-orchestration/SKILL.md`

## Skill Body

# Game Development Orchestration

Orchestrate game development projects using a hybrid Hermes/pi.dev workflow. Hermes handles planning, architecture, and documentation. pi.dev handles focused code implementation (one file at a time).

## Trigger Conditions

Use this skill when:
- User mentions "game", "pygame", "Godot", "Final Escape", or similar game project
- User wants to add features to an existing game codebase
- User mentions "plan", "swarm", "agents", or "pi.dev" in a game context
- User references commits, assets, or game mechanics

## Pre-Flight Reconnaissance (MANDATORY)

Before asking questions or making plans, always gather current state.

**CRITICAL: Verify the correct project directory first.** The user may have multiple related projects (e.g., `final-escape` pygame vs `final-escape-g` Godot). If they mention a path, use it. If unsure, ask: "Which project directory?" before running any commands.

### For Pygame Projects
```bash
cd PROJECT_DIR && git log --oneline -20
cd PROJECT_DIR && git status --short
cd PROJECT_DIR && find . -name "*.py" | grep -v venv | grep -v __pycache__ | head -30
cd PROJECT_DIR && ls assets/ 2>/dev/null || echo "No assets dir"
cd PROJECT_DIR && find . -name "*.mdc" -o -name ".cursorrules" 2>/dev/null
cd PROJECT_DIR && find . -name "*.md" | grep -v venv | grep -v .buildozer | head -20
```

### For Godot Projects
```bash
cd PROJECT_DIR && git log --oneline -20
cd PROJECT_DIR && git status --short
cd PROJECT_DIR && find . -name "*.gd" | grep -v .godot | head -30
cd PROJECT_DIR && find . -name "*.tscn" | grep -v .godot | head -20
cd PROJECT_DIR && find assets -type f | sort | head -40
cd PROJECT_DIR && cat project.godot | head -30
cd PROJECT_DIR && find . -name "*.mdc" -o -name ".cursorrules" 2>/dev/null
cd PROJECT_DIR && find . -name "*.md" | grep -v .godot | head -20
```

**Why**: The user often references commits, files, or prior work that may not exist in the current branch. Checking first prevents asking questions about stale or missing context. Also detects engine type (pygame vs Godot) automatically from file extensions.

## The Grill-Me Phase

If the user says "grill me" or presents multiple plans:

1. **Acknowledge**: "Starting grill process. One question at a time."
2. **Run reconnaissance FIRST** — always do pre-flight before grilling
3. **Show reconnaissance findings**: "Current state: [X commits, Y assets, Z power-ups]"
4. **Adapt if reconnaissance answers the question** — if git/assets reveal the answer, note it and move on
5. **Ask questions one at a time** — walk the design tree branch by branch
6. **Provide recommended answers** with each question
7. **Document the resolved plan** in Obsidian before execution

**Pitfall**: The user may jump ahead with critical context (correcting project path, missing commits, asset locations). Do not rigidly stick to the question sequence if reconnaissance or the user has already resolved a branch. Adapt the grill to the remaining unresolved decisions.

**Pitfall**: The user may say "the project is at PATH" or provide other critical context before you've finished all grill questions. This is NOT a failure of the grill — it's the user being efficient. Immediately pivot: acknowledge the correction, update your mental model, and skip questions that are now answered by the new context. Continue grilling only on remaining unresolved branches.

## Planning Phase

After grilling, create a merged plan:

1. **Mark done vs remaining** — check what's already implemented
2. **Prioritize** — user usually wants immediate-impact items first
3. **Decompose into pi.dev-sized chunks** — one file per task, <3000 char prompts
4. **Document in Obsidian** — write to `GT Vault/hermes/PROJECT_NAME-plan.md`

## pi.dev Task File Creation

For each coding task, create a focused task file:

```bash
# Create task file
cat > /tmp/pi-task-NAME.md << 'EOF'
# Task: [BRIEF DESCRIPTION]

## File to modify
[ABSOLUTE_PATH]

## Current state
[2-3 sentences]

## Required changes
1. [Specific change]
2. [Specific change]
3. [Specific change]

## Constraints
- Do NOT modify [FILES]
- [Build/test command] must pass

## Context
[Paste relevant 20-30 lines]
EOF
```

**Rules**:
- One file per pi task
- Absolute paths only
- Include verification command
- Delete task file after completion
- Hermes validates output before next task

## Swarm Execution

Max 3 concurrent agents:

| Slot | Role | Typical Task |
|------|------|-------------|
| Agent 1 | pi.dev Coder | Implement feature in target file |
| Agent 2 | pi.dev Coder | Implement related feature in second file |
| Agent 3 | Hermes/Reviewer | Review output, run tests, document |

**Never** parallelize tasks that touch the same file.

## Checkpoints Between Phases

1. **Plan reviewed** — user approves merged plan
2. **Reconnaissance done** — git, assets, docs checked
3. **Task files created** — all pi.dev prompts ready
4. **Agents complete** — all code delivered
5. **Integration** — Hermes merges, resolves conflicts
6. **Validation** — game runs, no regressions
7. **Documentation** — Obsidian updated with progress
8. **Delivery** — user sign-off

## Post-Execution

After agents complete:

1. **Hermes reviews all changes** — read modified files
2. **Run verification**:
   - Pygame: `cd PROJECT_DIR && python main.py`
   - Godot: `cd PROJECT_DIR && godot --headless --script tests/verify.gd` or open in Godot editor and run (F5)
3. **Update Obsidian** — mark completed tasks
4. **Git commit** — `git add -A && git commit -m "feat: ..."`
5. **Report to user** — summary of what changed

## Pitfalls

| Pitfall | Prevention |
|---------|-----------|
| pi.dev times out | Keep prompts <3000 chars, one file per task |
| Merge conflicts | Never parallelize same-file edits |
| Missing assets | Check `assets/` dir before asking about sprites/sounds |
| Stale context | Always check git log first — commits may be on different branch |
| Wrong project | Verify project directory before reconnaissance (pygame vs Godot variants) |
| Broken game | Run verification after every phase (pygame: `python main.py`, Godot: editor run or headless script) |
| Undocumented work | Write to Obsidian before AND after execution |
| User jumps ahead during grill | If user provides critical context (correct project path, missing commits, asset locations) mid-grill, adapt immediately. Do not rigidly stick to the question sequence. Note what was resolved and continue with remaining unresolved decisions only. |
| Incomplete skin asset audit | When checking skin systems, verify BOTH the skin folder contents AND what the code expects. A metadata.json may list assets that don't exist on disk, or disk assets may not be referenced in code. Also check for hardcoded `load()` calls that bypass the skin system. |
| User jumps ahead during grill | If user provides critical context (correct project path, missing commits, asset locations) mid-grill, adapt immediately. Do not rigidly stick to the question sequence. Note what was resolved and continue with remaining unresolved decisions only. |
| Test screen in production | Test screens must be debug-only (`OS.is_debug_build()`). Never add test screens to main menu in production. Use hidden key combos or debug-only buttons. |
| Test screen asset loading | Test screens should use the same asset loading paths as the real game. If the game uses AssetManager/skin system, the test screen must too — don't hardcode `load("res://assets/images/3x/...")` paths. |
| SVG skin folder mismatch | If `_get_skin_path()` appends `resolution + "/"` but SVG skins are in flat folders, assets won't resolve. Verify code path matches folder structure for each skin type. |

## Quick Reference

```bash
# Reconnaissance
cd PROJECT_DIR && git log --oneline -20 && git status --short

# Create pi task file
cat > /tmp/pi-task.md << 'EOF'
# Task: ...
## File to modify: /abs/path/to/file.py
## Required changes: ...
EOF

# Delegate to pi
pi -p "Read /tmp/pi-task.md and implement" --cwd PROJECT_DIR

# Verify
cd PROJECT_DIR && python main.py

# Document in Obsidian
hermes spawn --skill obsidian --prompt "Update GT Vault/hermes/PROJECT.md with: [PROGRESS]"
```

## References

- `references/pi-task-template.md` — Copy-paste task file template
- `references/pygame-project-structure.md` — Typical pygame project layout
- `references/godot-reconnaissance.md` — Godot project state-check checklist and gotchas, including skin system asset audit
- `references/godot-test-screen.md` — Debug-only test screen patterns, spawn separation, and access control
