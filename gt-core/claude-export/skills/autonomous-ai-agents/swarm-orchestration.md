# swarm-orchestration

> Multi-agent swarm management: parallel execution, max 3 concurrent agents, test checkpoints, swarm vs sequential mode, and distributed error handling.

## Metadata

- **Version:** 1.0.0
- **Author:** Hermes Agent
- **License:** MIT
- **Tags:** swarm, multi-agent, orchestration, parallel, distributed, autonomous-ai-agents
- **Related Skills:** hermes-agent, pi-coding-agent, claude-code
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/autonomous-ai-agents/swarm-orchestration/SKILL.md`

## Skill Body

# Swarm Orchestration

Manage multiple AI agents working in parallel on a single task. This skill covers swarm patterns, concurrency limits, checkpoint validation, and error recovery when coordinating distributed agent work.

## What is a Swarm

A swarm is a group of autonomous agents executing sub-tasks in parallel, coordinated by an orchestrator (Hermes). Swarms are useful when:

- A large task decomposes into independent sub-tasks
- Different expertise is needed simultaneously (e.g., UI + backend + tests)
- Speed matters more than strict sequential dependency
- You want to explore multiple approaches in parallel

## Swarm vs Sequential

| | Swarm Mode | Sequential Mode |
|--|------------|-----------------|
| Use when | Sub-tasks are independent | Each step depends on the previous |
| Speed | Faster (parallel) | Slower (linear) |
| Coordination | Orchestrator merges results | Single agent maintains context |
| Error handling | Isolated per agent | Cascading risk |
| Context sharing | Limited — agents work in isolation | Full context carry-forward |
| Best for | Exploration, independent modules | Debugging, architecture, tight coupling |

**Default to sequential.** Use swarm only when independence is clear.

## Max 3 Concurrent Agents

Hard limit: **never run more than 3 agents concurrently**.

Reasons:
- API rate limits and cost control
- Context window pressure on the orchestrator
- Merge complexity grows super-linearly
- Debugging parallel failures is exponentially harder

### Agent roles in a 3-agent swarm

| Slot | Typical Role | Responsibility |
|------|--------------|----------------|
| Agent 1 | Implementer | Writes code, builds features |
| Agent 2 | Tester / QA | Writes tests, validates behavior |
| Agent 3 | Reviewer / Docs | Reviews code, writes docs, checks style |

Alternative configurations:
- **Explore swarm**: 3 agents each try a different approach, best result wins
- **Layer swarm**: 1 UI agent, 1 API agent, 1 data agent
- **Fix swarm**: 1 agent patches, 1 agent writes tests, 1 agent verifies

## Parallel Execution Patterns

### Pattern 1: Independent Modules

```
Task: Build a new feature with UI, API, and data layers

1. Hermes decomposes into 3 independent modules
2. Spawn Agent 1 → Build UI layer (SwiftUI views)
3. Spawn Agent 2 → Build API layer (networking client)
4. Spawn Agent 3 → Build Data layer (model + persistence)
5. Wait for all 3 to complete
6. Hermes integrates the modules
7. Run integration tests
```

### Pattern 2: Parallel Exploration

```
Task: Find the best algorithm for image resizing

1. Hermes defines the evaluation criteria (speed, quality, memory)
2. Spawn Agent 1 → Implement vImage approach
3. Spawn Agent 2 → Implement Core Image approach
4. Spawn Agent 3 → Implement Metal compute approach
5. Wait for all 3
6. Hermes benchmarks and picks the winner
7. Discard losing branches (or archive for reference)
```

### Pattern 3: Review Swarm

```
Task: Review a large PR thoroughly

1. Hermes splits the PR into logical chunks
2. Spawn Agent 1 → Review architecture and API design
3. Spawn Agent 2 → Review tests and edge cases
4. Spawn Agent 3 → Review style, docs, and accessibility
5. Wait for all 3
6. Hermes merges findings into a single coherent review
```

## Test Checkpoints Between Phases

**Never proceed to the next phase without validation.**

### Checkpoint structure

```
Phase 1: Planning
  └─ Checkpoint: Plan reviewed, sub-tasks clearly defined

Phase 2: Parallel Execution
  └─ Checkpoint: All agents completed, outputs received

Phase 3: Integration
  └─ Checkpoint: Combined code compiles, no merge conflicts

Phase 4: Validation
  └─ Checkpoint: All tests pass, manual smoke test done

Phase 5: Delivery
  └─ Checkpoint: Final review, user sign-off
```

### What to validate at each checkpoint

| Checkpoint | Validation |
|------------|------------|
| Plan reviewed | Sub-tasks are truly independent, no hidden dependencies |
| Agents complete | All agents returned output, none timed out or errored |
| Integration | Code merges cleanly, imports resolve, builds pass |
| Tests pass | Unit tests, integration tests, lint checks all green |
| Delivery | User requirements met, no regressions introduced |

### Failing a checkpoint

If any checkpoint fails:
1. **Stop** — do not proceed to the next phase
2. **Diagnose** — which agent failed, what was the error
3. **Repair** — fix the issue or re-delegate the sub-task
4. **Re-validate** — run the checkpoint again before continuing

## Spawning Agents

### From Hermes

```bash
# Spawn a sub-agent with a specific skill and task
hermes spawn --skill pi-coding-agent --prompt "Implement the UserProfileView in SwiftUI"

# Spawn with context file
hermes spawn --skill swiftui-pro --context ./Designs/profile-mock.png --prompt "Build this profile screen"

# Spawn with working directory scoped
hermes spawn --cwd ./Modules/Auth --skill ios-developer --prompt "Write the AuthService class"
```

### Spawning pi.dev agents via CLI

For coding tasks, delegate to pi.dev directly through the CLI. pi.dev works best with small, focused single-file tasks.

```bash
# Basic pi.dev delegation
pi -p "TASK_DESCRIPTION" --context FILE_PATH

# Scoped to project directory
pi -p "Refactor asteroid.py to add crystal type" --cwd /Users/gt/Public/MyFiles/06-GameDev/final-escape

# Task file pattern (best for complex tasks)
# 1. Hermes writes a focused task file
# 2. pi reads and executes
pi -p "Read /Users/gt/task-asteroid-crystal.md and implement the changes in entities/asteroid.py"
```

**Critical**: pi.dev chokes on large multi-file prompts. Always:
- One file per pi task
- Include build/run verification command
- Hermes validates output before next task

### Documentation agent (Obsidian)

Always document plans and progress in the user's Obsidian vault:

```bash
# After creating a plan, write it to Obsidian
hermes spawn --skill obsidian --prompt "Create note 'GT Vault/hermes/final-escape-plan.md' with the following plan: [PASTE PLAN]"

# Update progress after each phase
hermes spawn --skill obsidian --prompt "Update note 'GT Vault/hermes/final-escape-plan.md' — mark Phase 1 as complete, Phase 2 in progress"
```

**GT's preference**: Document in `GT Vault/hermes/` unless asked otherwise. Use the obsidian skill for all note operations.

### Agent contract

Every spawned agent must return:
1. **Status**: success, partial, failed
2. **Output**: files changed, code produced, or error log
3. **Summary**: 1-2 sentence description of what was done
4. **Blockers**: anything that prevents the next phase from proceeding

## Error Handling in Distributed Tasks

### Isolated failure

One agent fails while others succeed.

```
Agent 1: Success (UI layer built)
Agent 2: Failed (API layer — network timeout)
Agent 3: Success (Data layer built)

Response:
1. Do not discard Agent 1 and 3 outputs
2. Retry Agent 2 with a simpler prompt or different approach
3. If retry fails, Hermes takes over the failed sub-task
4. Re-run integration checkpoint after repair
```

### Cascading failure

Multiple agents fail due to a shared bad assumption.

```
Agent 1: Failed (missing shared model)
Agent 2: Failed (missing shared model)
Agent 3: Failed (missing shared model)

Response:
1. Stop all agents
2. Hermes identifies the root cause (missing dependency)
3. Hermes fixes the shared dependency first
4. Re-spawn all agents with corrected context
```

### Timeout / stall

Agent hangs or exceeds time budget.

```
Response:
1. Kill the stalled agent process
2. Check partial output — sometimes useful work was done
3. Re-spawn with a smaller, more focused prompt
4. If still stalling, switch to sequential mode for that sub-task
```

### Merge conflict

Two agents modified the same file.

```
Response:
1. Hermes reads both versions
2. Hermes decides which changes to keep (or combines them)
3. Hermes manually resolves the conflict
4. Re-run build/test checkpoint
```

## Swarm Workflow Checklist

Before starting a swarm:

- [ ] Task decomposed into independent sub-tasks
- [ ] No hidden dependencies between sub-tasks
- [ ] Max 3 agents defined with clear roles
- [ ] Each agent has a focused, bounded prompt
- [ ] Checkpoints defined for each phase
- [ ] Rollback plan if a checkpoint fails
- [ ] Integration strategy defined (how Hermes merges results)
- [ ] **Environment reconnaissance done** — checked git history, project docs, zshrc, existing rules
- [ ] **Obsidian documentation queued** — plan will be written to GT Vault/hermes/
- [ ] **pi.dev task files prepared** (if using pi) — one file per task, with build verification
- [ ] **Hermes monitors only** — user preference: spawn agents to work, Hermes orchestrates and monitors, does NOT write game code directly

## Orchestrator vs Worker Boundary

**Critical user preference**: When the user says "spawn agents to work on each task and not you, you just monitor those agents" — respect this boundary absolutely.

| Role | What Hermes Does | What Agents Do |
|------|------------------|----------------|
| **Hermes (Orchestrator)** | Plan, delegate, monitor, commit, document | NEVER write game code, NEVER edit .gd/.tscn files |
| **pi.dev (Godot Specialist)** | Implement GDScript, edit scenes, fix gameplay bugs | Focused game code tasks only |
| **kimi CLI (General Engineer)** | iOS integration, code review, documentation | Non-Godot tasks, Swift, general coding |

**Hermes orchestration duties**:
1. Check git status and commits before spawning
2. Create plans in Obsidian
3. Spawn agents with precise, bounded prompts
4. Review agent output for correctness
5. Commit changes with descriptive messages
6. Update Obsidian with progress
7. Report status to user — do NOT do the work yourself

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|--------------|--------------|
| "Everyone do everything" | Agents duplicate work, conflicts everywhere |
| No checkpoints | Errors compound, hard to debug |
| 5+ agents | Rate limits, chaos, impossible to merge |
| Shared mutable state | Race conditions, corrupted files |
| Fire-and-forget | Agents return garbage, no validation |
| Nested swarms | Orchestrator loses track, exponential complexity |

## Agent Roles in GT's Stack

| Agent | CLI | Skills | Responsibility |
|-------|-----|--------|----------------|
| **Hermes** | `hermes` | orchestrator | Plans, delegates, monitors, commits, documents |
| **pi.dev** | `pi --provider kimi-coding --model kimi-k2.6` | caveman, godot, game-development | GDScript, Godot scenes, gameplay logic |
| **kimi CLI** | `code-ai` (alias) | caveman, superpowers, context-manager | iOS/Swift, code review, general coding |

### Activation commands

```bash
# pi.dev with caveman skill (minimal tokens)
cd /Users/gt/Public/MyFiles/06-GameDev/final-escape-g
pi --skill caveman

# pi.dev with godot skill
pi --skill godot

# kimi CLI (via alias in ~/.zshrc)
code-ai

# Hermes (orchestrator — you are here)
```

### Task assignment rules

| Task Type | Primary Agent | Secondary |
|-----------|--------------|-----------|
| GDScript / Godot scenes | pi.dev | kimi CLI |
| iOS / Swift integration | kimi CLI | pi.dev |
| UI/UX design | Hermes (plan) + pi.dev (implement) | kimi CLI |
| Audio/SFX | pi.dev | kimi CLI |
| Documentation | Hermes | kimi CLI |
| Code review | kimi CLI | Hermes |

## Quick Reference

```bash
# Spawn a single agent
hermes spawn --skill SKILL_NAME --prompt "TASK"

# Spawn with context
hermes spawn --skill SKILL_NAME --context FILE --prompt "TASK"

# Check active agents
hermes agents list

# Kill a stalled agent
hermes agents kill AGENT_ID

# pi.dev delegation
pi -p "TASK" --context FILE --cwd PROJECT_DIR

# Task file pattern
pi -p "Read /path/to/task.md and implement changes in target_file.py"
```

## References

- `references/pi-dev-task-file-template.md` — Template for creating focused pi.dev task files
- `references/final-escape-g-session-log.md` — Example swarm session: 6 agents, 2 commits, Godot game dev

## Summary

1. **Default to sequential** — use swarm only for independent sub-tasks
2. **Max 3 agents** — never exceed
3. **Checkpoints between phases** — validate before proceeding
4. **Hermes is the orchestrator** — plans, delegates, integrates, validates
5. **Agents are workers** — focused, bounded, return structured output
6. **Fail fast, repair, re-validate** — never skip a failed checkpoint
