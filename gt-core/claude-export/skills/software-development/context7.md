# context7

> Use Upstash Context7 to pull version-specific documentation and code examples from source repositories into LLM context. Connects via MCP server or REST API.

## Metadata

- **Version:** 1.0.0
- **Author:** GT Core
- **License:** MIT
- **Tags:** mcp, documentation, context, upstash, context7
- **Related Skills:** native-mcp
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/context7/SKILL.md`

## Skill Body

# Context7 Skill

Context7 by Upstash fetches up-to-date, version-specific documentation and code examples from source repositories and injects them into your LLM context. Eliminates hallucinations from stale training data.

## What It Does

- Resolves library/version → fetches docs from source repo
- Returns structured markdown with code examples
- Works via MCP server or direct REST API
- Supports: npm, PyPI, crates.io, Go packages, GitHub repos

## MCP Server Setup

### Install

```bash
npm install -g @upstash/context7-mcp
# or
npx @upstash/context7-mcp
```

### Configure in Hermes

Add to `~/.hermes/config.yaml` under `mcp.servers`:

```yaml
mcp:
  servers:
    context7:
      command: npx
      args: ["-y", "@upstash/context7-mcp"]
      env:
        UPSTASH_REDIS_REST_URL: "https://your-db.upstash.io"
        UPSTASH_REDIS_REST_TOKEN: "your-token"
```

Or use HTTP transport if hosted:

```yaml
mcp:
  servers:
    context7:
      url: "https://context7-api.upstash.com/sse"
```

### Test

```bash
hermes mcp test context7
```

## REST API Usage

Direct API calls without MCP:

```bash
curl -s "https://context7.com/api/v1/libraries?query=fastapi" | jq '.libraries[:3]'
```

Resolve and fetch docs:

```bash
# 1. Resolve library to repo
curl -s "https://context7.com/api/v1/resolve?library=fastapi" | jq '.repository'

# 2. Fetch docs for version
curl -s "https://context7.com/api/v1/docs?repo=tiangolo/fastapi&version=0.115.0" | jq '.docs[:2]'
```

## Tools Available (MCP)

| Tool | Purpose |
|------|---------|
| `context7_resolve` | Resolve package name → GitHub repo |
| `context7_fetch` | Fetch docs for repo + version |
| `context7_search` | Search within fetched docs |
| `context7_list_versions` | List available versions |

## Usage Patterns

### Pattern 1: Before Coding Task

```
User: "Build FastAPI auth with JWT"
→ Call context7_resolve("fastapi")
→ Call context7_fetch("tiangolo/fastapi", "latest")
→ Inject docs into context
→ Proceed with implementation
```

### Pattern 2: Debugging Library Issue

```
User: "Pydantic v2 validator not working"
→ Call context7_resolve("pydantic")
→ Call context7_fetch("pydantic/pydantic", "2.9.0")
→ Search docs for "validator"
→ Fix based on actual docs
```

### Pattern 3: Version-Specific Migration

```
User: "Migrate React 17 → 18"
→ Call context7_fetch("facebook/react", "18.3.0")
→ Call context7_fetch("facebook/react", "17.0.2")
→ Compare docs, generate migration guide
```

## Environment Variables

| Var | Required | Description |
|-----|----------|-------------|
| `UPSTASH_REDIS_REST_URL` | Yes* | Upstash Redis REST endpoint |
| `UPSTASH_REDIS_REST_TOKEN` | Yes* | Upstash Redis REST token |
| `CONTEXT7_API_KEY` | No | Rate limit increase |

*Only if using MCP server with Upstash Vector backend. Direct REST API needs no auth.

## Rate Limits

- Free tier: 100 requests/day
- Pro: 10,000 requests/day
- Cache fetched docs locally to minimize API calls

## Integration with GT Core

1. Add MCP server to `~/.hermes/config.yaml`
2. Skill auto-loads when `mcp` toolset enabled
3. Use in any coding task: `/skill context7` or auto-trigger on package names

## Links

- Repo: https://github.com/upstash/context7
- Docs: https://context7.com/
- MCP Package: `@upstash/context7-mcp`
- SDK Package: `@upstash/context7-sdk`
