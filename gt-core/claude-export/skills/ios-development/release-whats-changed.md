# release-whats-changed

> Generate structured release notes or "what changed" summaries for this repository. Use when the user asks what changed between releases, wants a changelog between release branches/tags, or asks for changes in the new version. By default, compare the newest release branch to the immediately previous release branch unless the user specifies refs.

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/ios-development/release-whats-changed/SKILL.md`

## Skill Body

# Release Whats Changed

Use this skill to produce a clean, reusable "what changed" summary from git history in this repository.

## When To Use

Trigger this skill when the user asks any of the following:

- what changed in the new version
- changes between two releases
- compare release branches or release tags
- generate release notes / changelog / QA summary

Use it even when the user gives informal wording like "what changed since last release".

## Default Behavior

If the user does **not** specify refs:

1. Find release refs that look like `release/x.y.z` from local and remote refs.
2. Prefer remote release branches when available, especially `origin/release/*`, to avoid including local-only commits.
3. Sort release versions by semantic version.
4. Compare the newest release branch against the immediately previous release branch.
5. State explicitly which refs were compared.

Default comparison target:

- `origin/release/<latest>` vs `origin/release/<previous>` when both exist
- otherwise fall back to the best available local release refs

If the user specifies refs, use those exact refs unless they are missing. If one specified ref is missing locally but a matching remote ref exists, use the remote ref and say so.

## Commands To Use

Prefer small, inspectable git commands:

```bash
git branch -a --list 'release/*'
git show-ref | rg 'refs/(heads|remotes/origin)/release/'
git tag --list
git log --oneline --no-merges <from>..<to>
git diff --stat <from>..<to>
git diff --name-status <from>..<to>
git rev-list --count --no-merges <from>..<to>
```

Use `git show --stat --summary --format=fuller <commit>` on the most important commits to understand intent before writing the summary.

## How To Summarize

Start from commits and changed files, then group changes into product-level themes.

Prioritize:

- customer-facing behavior changes
- bug fixes
- crash/stability fixes
- analytics or tracking changes
- checkout/cart/payment/account changes
- deep link or navigation changes

De-emphasize or collapse:

- internal agent/tooling/docs churn
- pure refactors with no user impact
- version bump-only commits
- test-only cleanup unless it matters for release confidence

If the diff contains lots of repo-maintenance noise, separate it into a short `Internal / Tooling` section instead of mixing it into user-facing notes.

## Output Format

Default to this structure:

```md
**Release X vs Y**

Compared `<from>..<to>`
Total non-merge commits: `N`

**New / Improved**
- ...

**Bug Fixes**
- ...

**UI / UX Changes**
- ...

**Tests / Stability**
- ...

**Internal / Tooling**
- ...

**Short user-facing version**
- ...
```

Adapt section names if the diff is smaller or mostly fixes.

## Important Rules

- Always mention the exact refs compared.
- Always verify whether local release branches differ from remote release branches before choosing refs.
- Prefer `origin/release/*` over local `release/*` when both exist and the user asked for release-to-release changes.
- Exclude merge commits unless the user asks for a full history.
- If there is a local-only commit on the target branch, call that out and avoid including it by default.
- If the comparison is ambiguous, make the safest assumption and state it clearly.
- Keep the final summary concise and structured so it can be pasted into release notes, QA notes, or stakeholder updates.

## Nice Follow-Ups

Offer one short follow-up tailored to the result, for example:

- PM-friendly release notes
- QA checklist
- App Store / stakeholder summary
- full commit list
