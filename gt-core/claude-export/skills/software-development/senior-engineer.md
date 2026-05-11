# senior-engineer

> Senior software engineer patterns, code review, architecture decisions, and mentoring. Use this skill when designing systems, reviewing code at depth, making trade-off decisions, or guiding less experienced developers.

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/senior-engineer/SKILL.md`

## Skill Body

# Senior Engineer Skill

This skill captures the mindset, patterns, and practices of a senior software engineer. It is not about writing more code—it is about writing the right code, in the right place, for the right reasons.

## When to Use
Use this skill when:
- **Designing or reviewing architecture**: Trade-offs, scalability, maintainability.
- **Conducting deep code reviews**: Beyond linting—looking at semantics, contracts, and failure modes.
- **Debugging complex issues**: Root-cause analysis, observability, and systematic elimination.
- **Mentoring or pair-programming**: Explaining the "why" behind decisions.
- **Refactoring legacy systems**: Safe evolution without breaking the world.
- **Estimating or planning work**: Breaking down ambiguity into deliverable chunks.

## 1. Architecture Patterns
- **Prefer composition over inheritance**: Favor assembling behaviors from smaller, testable units.
- **Design for change**: Isolate volatility. What changes often should not force recompilation of what does not.
- **Layered architecture**: Keep domain logic free of framework code. UI, application, domain, infrastructure.
- **API contracts**: Version explicitly. Document failure modes, rate limits, and idempotency expectations.
- **Event-driven vs synchronous**: Use events for decoupling; use synchronous calls when consistency is required. Do not mix them blindly.
- **Database per service**: If you have services, give them their own data. Shared databases are shared fate.

## 2. Code Review Checklist
- **Correctness**: Does it handle edge cases? Empty inputs, timeouts, retries, partial failures.
- **Security**: Are inputs validated? Are secrets handled properly? Is there injection risk?
- **Performance**: Are there N+1 queries? Unbounded loops? Memory leaks? Blocking the event loop?
- **Observability**: Are there logs, metrics, or traces? Can you debug this in production at 3 AM?
- **Test coverage**: Are there unit tests for logic, integration tests for boundaries, and contract tests for APIs?
- **Readability**: Can a new team member understand this in 30 seconds? Are names honest?
- **Scope creep**: Is this PR doing one thing? If not, suggest splitting.

## 3. Coding Standards
- **Single Responsibility**: A module, class, or function should have one reason to change.
- **Open/Closed**: Open for extension, closed for modification. Use interfaces and strategies.
- **Fail fast**: Validate preconditions early. Return errors at the boundary, do not let them propagate silently.
- **Immutability by default**: Prefer immutable data structures. Mutation is the source of many bugs.
- **Explicit over implicit**: Magic values, hidden defaults, and side effects erode trust.
- **Dependency direction**: Domain code should not depend on frameworks. Frameworks are details.

## 4. Debugging Strategies
- **Reproduce first**: If you cannot reproduce it, you cannot fix it. Reduce to the smallest failing case.
- **Binary search**: Comment out half the system. Which half contains the bug? Repeat.
- **Change one thing**: Do not change five variables at once. Isolate variables like a scientist.
- **Read the error**: Stack traces tell stories. Read from the bottom up.
- **Add observability**: If you cannot see it, instrument it. A well-placed log line beats hours of guessing.
- **Rubber duck**: Explain the bug out loud. The act of explaining often reveals the flaw.
- **Check assumptions**: Is the config what you think? Is the environment correct? Is the cache stale?

## 5. Mentoring Principles
- **Ask, do not tell**: "What do you think happens here?" builds understanding faster than giving the answer.
- **Explain the trade-off**: There are few absolute wrongs. Explain why A is better than B in this context.
- **Review in person for big items**: Written feedback is great for nits; conversation is better for design issues.
- **Leave the campsite cleaner**: Every PR review is a teaching moment. Suggest a pattern, link to docs.
- **Normalize not knowing**: "I do not know, let us find out" is a senior move.

## 6. Decision Making
- **Optimize for readability first**: Code is read 10x more than it is written.
- **Avoid premature optimization**: Measure before you optimize. Profile, do not guess.
- **Document the "no"**: The decisions you do not make matter. Write down why you rejected alternatives.
- **Two-way door decisions**: If it is reversible, decide quickly. If it is one-way, slow down and gather input.
- **Cost of delay**: Sometimes shipping a 70% solution today beats a 100% solution next quarter.

## 7. Operational Thinking
- **Design for failure**: Assume everything fails. Circuit breakers, retries with backoff, graceful degradation.
- **Observability is not optional**: Metrics, structured logging, distributed tracing. If it is not observed, it does not exist.
- **Rollback plan**: Every deployment should be reversible in under 5 minutes.
- **Security by default**: Least privilege, input validation, output encoding. Do not bolt it on later.

## 8. Communication
- **Write clear commit messages**: Explain the why, not just the what. Future you will thank present you.
- **Document the intent**: Comments should explain why the code is the way it is, not what it does.
- **RFCs for big changes**: Share context before code. A small doc saves days of review churn.
- **Status updates**: Be honest about blockers. Surprises are expensive; early signals are cheap.

## 🛠️ Senior Engineer Checklist
- [ ] Have I considered the failure modes?
- [ ] Is this easy to delete or replace?
- [ ] Can someone else maintain this without asking me?
- [ ] Did I write a test that fails before the fix?
- [ ] Is the commit message explainable to a non-author?
- [ ] Have I documented the trade-offs I considered?
