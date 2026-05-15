# pi-coding-agent

> Delegate coding tasks to pi.dev CLI. Best practices for prompt chunking, hybrid Hermes/pi workflows, and recovery when pi chokes.

## Metadata

- **Version:** 1.0.0
- **Author:** Hermes Agent
- **License:** MIT
- **Tags:** pi.dev, coding-agent, delegation, cli, autonomous-ai-agents
- **Related Skills:** hermes-agent, claude-code, codex
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/autonomous-ai-agents/pi-coding-agent/SKILL.md`

## Skill Body

# pi.dev Coding Agent

pi.dev is an autonomous coding agent by Inflection AI that runs in the terminal. This skill covers how to delegate coding tasks to pi effectively, manage prompt chunking, recover from failures, and build hybrid workflows where Hermes plans and pi executes.

## What is pi.dev

- Terminal-based AI coding assistant (similar to Claude Code, Codex, Hermes Agent)
- Uses tool calling to read files, run commands, edit code, and execute tests
- Optimized for fast, iterative code generation
- Best for: focused implementation tasks, refactors, test generation, boilerplate

## When to Use pi.dev

| Scenario | Delegate to pi? |
|----------|----------------|
| Implement a single function or method | Yes |
| Write unit tests for existing code | Yes |
| Refactor a single file or module | Yes |
| Generate boilerplate / scaffolding | Yes |
| Fix a specific compiler error | Yes |
| Architecture decisions across the codebase | No — Hermes plans |
| Multi-file coordination requiring context | No — Hermes plans |
| Complex debugging with system-wide tracing | No — Hermes plans |
| Tasks requiring external API research | No — Hermes plans |

## pi.dev CLI Patterns

### Basic invocation

```bash
# Interactive session
pi

# Single prompt (fire-and-forget)
pi -p "Add error handling to the fetchUser function in UserService.swift"

# With context file
pi -p "Refactor this view model" --context ./ViewModels/ProfileViewModel.swift

# Run in specific directory
pi -p "Create a Swift Package for this module" --cwd ./Modules/Networking
```

### Common flags

| Flag | Purpose |
|------|---------|
| `-p, --prompt` | Single prompt string (non-interactive) |
| `--context` | Attach file(s) as context |
| `--cwd` | Set working directory |
| `--model` | Override default model |
| `--no-confirm` | Auto-accept tool calls (use with caution) |
| `--dry-run` | Preview what pi would do without executing |

### Reading pi output programmatically

```bash
# Capture output for parsing
pi -p "List all public methods in UserService" --no-confirm > /tmp/pi_output.txt

# JSON mode for structured output
pi -p "Return a JSON array of all TODO comments in this codebase" --format json
```

## Best Practices for pi Prompts

### 1. Small chunks win

pi works best with **focused, bounded tasks**. Break large tasks into sequential small chunks.

```
Bad:  "Build the entire authentication flow"
Good: "Create a LoginViewModel with email/password validation"
Good: "Add a password reset method to AuthService"
Good: "Write unit tests for the new password reset method"
```

### 2. Provide context, not history

```
Bad:  "Remember we discussed using Combine last week..."
Good: "Use Combine. Here is the relevant Publisher type: [paste 20 lines]"
```

### 3. Be explicit about constraints

```
Good: "Use Swift 6 strict concurrency. Avoid @MainActor on the service layer."
Good: "Do not add third-party dependencies. Use only Foundation and SwiftUI."
Good: "Target iOS 17+. Do not use APIs introduced in iOS 18."
```

### 4. Specify output format

```
Good: "Return only the function body. No imports, no wrapper code."
Good: "Provide the full file contents, ready to save."
Good: "Return a diff-style output showing before/after."
```

## Task File Delegation Pattern

For complex multi-step tasks (e.g., redesign a dashboard page), write a task file with explicit requirements instead of a long inline prompt. pi.dev reads the file and executes better than with inline prompts.

### Why it works
- pi.dev chokes on large inline prompts (>60s timeout)
- Task file stays under 3000 chars, focused on one file
- Requirements are explicit and numbered
- Backend/frontend split: Hermes does API changes, pi.dev does UI

### Example task file

Create `/Users/gt/Public/MyFiles/agent-home/dashboard/pi-task-billing.md`:

```markdown
# Billing Tab Redesign

## File to modify
/Users/gt/Public/MyFiles/agent-home/dashboard/frontend/src/pages/Billing.tsx

## Required changes
1. Two main cards: Kimi Code (usage-based) + Kimi Platform (balance)
2. Fetch from `/api/billing/usage/by-model?provider=kimi-coding`
3. Add top-up buttons linking to platform.moonshot.cn
4. Keep sci-fi aesthetic
5. Build must pass: `npm run build`

## Data structures
[ paste API response shapes ]

## Important
- Do NOT change backend files
- Do NOT add new dependencies
```

### Delegation command

```bash
pi -p "Read the task file at /Users/gt/Public/MyFiles/agent-home/dashboard/pi-task-billing.md and modify Billing.tsx accordingly. Do NOT change backend files. Build must pass."
```

### Rules for task files
1. **One file per task** — pi.dev works best with single-file focus
2. **Backend already done** — Hermes handles API changes first
3. **Include data structures** — paste expected API response shapes
4. **Include build command** — pi.dev must verify before finishing
5. **Delete task file after** — keep workspace clean

## Game Development Workflow (GT's Pattern)

For Godot game projects (e.g., `final-escape-g`), follow this exact sequence:

1. **Check git** — `git log --oneline -10`, `git status`
2. **Grill the user** — use `grill-me` skill to ask 5 questions about requirements
3. **Document in Obsidian** — write plan to `Hermes Vault/Hermes/final-escape-*.md`
4. **Spawn pi.dev agents** — one task per agent, max 3 concurrent
5. **Monitor only** — Hermes does NOT write .gd or .tscn files
6. **Commit after each phase** — descriptive messages with change summary
7. **Check `.cursor/rules/`** — if exists, verify agent followed project rules

### pi.dev task format for Godot

```bash
# Task file pattern (one file, <3000 chars)
pi -p "Read /path/to/task.md and implement changes in target_file.gd. Do NOT run the game. Verify code compiles mentally."

# Direct prompt pattern (small chunks)
pi -p "In scripts/asteroid.gd, add crystal asteroid type 7. Use AssetManager.load_asteroid_sprite_with_skin(). Add _spawn_crystal_shatter_effect(). Do NOT modify other types."
```

### pi.dev constraints for game dev
- **Never run Godot editor** — pi.dev has no GUI access
- **Verify paths exist** — check `res://` paths before referencing
- **One file per task** — pi.dev chokes on multi-file coordination
- **Use caveman skill** — `pi --skill caveman` for minimal token usage
- **Check .tscn references** — changing script paths requires updating scene files

## When pi Chokes — Recovery Guide

### Symptom: pi loops or stalls

1. **Cancel** (Ctrl+C) and retry with a smaller prompt
2. Remove ambiguous language ("make it better", "clean up")
3. Add explicit step-by-step instructions

### Symptom: pi produces incorrect / hallucinated code

1. **Pin the error**: paste the exact compiler error or failing test output
2. **Add constraints**: explicitly forbid the incorrect approach
3. **Provide a reference**: paste a working similar function from the same codebase

### Symptom: pi ignores part of the prompt

1. **Number your requirements**: "1. Do X. 2. Do Y. 3. Do Z."
2. **Repeat constraints at the end**: "Remember: no third-party deps, Swift 6 only."
3. **Use the --context flag** instead of pasting large blocks inline

### Symptom: pi modifies files you did not ask it to touch

1. Always review the tool-call preview before confirming
2. Use `--dry-run` to inspect the planned changes
3. Scope with `--cwd` to limit file visibility

### Symptom: API calls return 404/401 after provider URL changes

When working with Kimi/Moonshot APIs, env var naming collisions cause wrong base URLs:
- `KIMI_BASE_URL` often points to Kimi Code (`api.kimi.com/coding`), not old Moonshot (`api.moonshot.ai`)
- Provider `kimi` resolves to `KIMI_BASE_URL` by default, which is wrong for old Moonshot keys
- **Fix**: Use explicit provider-to-env-var mapping in backend code
- See `references/kimi-api-provider-quirks.md` for full reproduction

### Symptom: pi.dev warns "Model not found for provider"

Kimi Code API uses model ID `kimi-for-coding`, not `kimi-k2.6`:
- `kimi-k2.6` is the display name, `kimi-for-coding` is the API model ID
- pi.json config must use `"model": "kimi-for-coding"` for provider `kimi-coding`
- Wrong model ID causes: `Warning: Model "kimi-k2.6" not found for provider "kimi-coding"`
- **Fix**: Update `pi.json` model field to match provider's actual model ID from `/v1/models`

### Symptom: pi runs tests that fail but claims success

1. Ask pi to show the **full** test output, not a summary
2. Run tests independently after pi finishes: `swift test` or `pytest`
3. Paste the actual failure back into a new pi prompt

## Hybrid Delegation: Hermes Plans, pi Executes

The most effective workflow combines Hermes' long-context planning with pi's fast execution.

### Pattern: Hermes Architect → pi Builder

```
1. Hermes analyzes the full codebase
2. Hermes writes a detailed implementation plan (files, functions, tests)
3. Hermes breaks the plan into small, independent chunks
4. For each chunk, Hermes delegates to pi via a precise prompt
5. Hermes reviews pi's output and runs tests
6. Hermes assembles the pieces and validates integration
```

### Example workflow

```bash
# Step 1: Hermes analyzes and plans
# (Hermes reads the project, identifies the change needed)

# Step 2: Hermes delegates chunk 1 to pi
pi -p "In UserRepository.swift, add a method fetchUserByEmail(_:)
that queries Core Data and returns User?. Use existing NSManagedObjectContext.
Return only the new method." \
  --context ./Data/UserRepository.swift

# Step 3: Hermes validates the output
swift build

# Step 4: Hermes delegates chunk 2 to pi
pi -p "Write unit tests for fetchUserByEmail in UserRepositoryTests.swift.
Use the existing CoreDataTestStack. Test: found, not found, and invalid email." \
  --context ./Data/UserRepository.swift \
  --context ./Tests/UserRepositoryTests.swift

# Step 5: Hermes runs tests
swift test --filter UserRepositoryTests

# Step 6: Hermes integrates and reviews
```

### Rules for hybrid delegation

1. **Hermes never delegates architecture to pi** — pi lacks full codebase context
2. **Hermes validates every pi output** — compile, test, lint before accepting
3. **Hermes maintains the plan** — if pi deviates, Hermes corrects or re-prompts
4. **One chunk at a time** — do not parallelize pi tasks that touch the same files
5. **Hermes owns error handling** — when pi fails, Hermes decides retry, re-prompt, or switch approach

## pi.dev vs Other Agents

| | pi.dev | Claude Code | Codex | Hermes Agent |
|--|--------|-------------|-------|--------------|
| Strength | Fast iteration, focused tasks | Deep reasoning, large context | OpenAI ecosystem integration | Skills, memory, multi-platform |
| Best for | Small chunks, quick edits | Complex analysis, debugging | GitHub-integrated workflows | Long-running, personalized tasks |
| Context window | Large | Very large | Large | Large |
| Tool calling | Yes | Yes | Yes | Yes |
| Self-improvement | Limited | Limited | Limited | Skills system |

## Safety and Review

- **Never use --no-confirm on production codebases** without a backup
- **Always run tests after pi edits** — pi may miss edge cases
- **Review diffs before committing** — pi sometimes deletes comments or formatting
- **Keep pi scoped** — use `--cwd` and `--context` to limit what it can see and touch

## Quick Reference

```bash
# Single task
pi -p "PROMPT" --context FILE

# Scoped to directory
pi -p "PROMPT" --cwd ./Subproject

# Dry run
pi -p "PROMPT" --dry-run

# Interactive
pi

# Capture output
pi -p "PROMPT" > output.txt
```

## References

- `references/kimi-api-provider-quirks.md` — Kimi Code vs Moonshot API URLs, model IDs, env var collisions, Python 3.14 venv fix
- `references/godot-project-structure.md` — Final Escape Godot project layout, architecture patterns, common pitfalls
