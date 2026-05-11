# grill-me

> Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/grill-me/SKILL.md`

## Skill Body

# grill-me — Pre-Flight Checklist

When the user says "grill me" or wants to stress-test a plan, do NOT start answering or planning immediately. Follow this sequence:

1. **Acknowledge** — "Starting grill process. One question at a time."
2. **Reconnaissance first** — Before asking questions, gather current state:
   - Check last 10-20 git commits (`git log --oneline -20`)
   - Check project structure and key files
   - Check any existing docs/rules (`.cursor/rules/`, `README.md`, project docs)
   - Check zshrc/env for relevant aliases or configs
3. **Then ask questions** — Only after you understand the current state

## Why reconnaissance first

The user often references commits, files, or prior work that may not exist in the current branch. Checking first prevents asking questions about stale or missing context. It also lets you ask sharper questions grounded in reality.

## Execution

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Adapting to User Corrections

The user may provide critical context mid-grill (correcting project path, revealing asset locations, clarifying prior decisions). This is NOT a failure of the grill — it's efficient communication. When this happens:

1. **Acknowledge the correction** — "Got it — project is at PATH, not the one I checked."
2. **Update your mental model** immediately
3. **Skip resolved questions** — don't ask about things the user just clarified
4. **Continue grilling** on remaining unresolved branches only

The goal is shared understanding, not rigidly completing a questionnaire.
