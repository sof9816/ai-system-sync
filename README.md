# GT AI System — Second Brain

One place for everything. Hermes + Pi + Kimi + Obsidian + Swarm Agents.

> **pi.dev is your lead developer and CTO.** Use the dashboard to orchestrate coding projects, review architecture, and scaffold new apps — starting with iOS.

## Stack

| Component | Role | Command |
|-----------|------|---------|
| **Hermes** | General AI assistant, tool-calling, skills | `ai "question"` |
| **Pi** | Coding agent, file editing, project work | `code-ai "task"` |
| **Swarm** | Permanent specialized agents (CFO, CTO, etc.) | `agent`, `swarm` |
| **Kimi** | LLM backend (K2.6) | All of the above |
| **Obsidian** | Persistent memory, knowledge base, notes | `~/Hermes Vault/Hermes/` |
| **Dashboard** | Unified web control panel | `./run-dashboard.sh` |

## Quick Start

```bash
# List all agents
agents

# Talk to a specific agent
cto "review this architecture"
cfo "analyze my spending"
researcher "what's new in Swift 6"

# Multi-agent swarm mode
swarm "I want to build a crypto tracking app"

# General questions (Hermes)
ai "what's the weather in Tokyo?"

# Coding tasks (Pi)
code-ai "refactor this function to use async/await"

# Web Dashboard
./run-dashboard.sh        # starts backend + frontend + opens browser
./run-dashboard.sh --stop # kills dashboard processes
```

## Dashboard Features (v0.3.0)

| Page | What it does |
|------|-------------|
| **Overview** | System stats, health checks, disk usage, pi.dev CTO banner, quick actions, activity feed |
| **Work** | Agents, swarm, sessions |
| **Billing & Usage** | API balances, token usage, recent calls |
| **Obsidian** | Browse agent memories and search vault |
| **Notifications** | Alert rules and system events |
| **AI Config** | Models & profiles, config file editor, system settings |
| **Hermes** | Hermes control panel (model, tools, skills) |
| **pi.dev** | Pi control panel (config, projects) |
| **Ghostty** | Terminal emulator config |

## Agents

| Agent | Role | Trigger |
|-------|------|---------|
| `cto` | Chief Technology Officer | Tech decisions, stack review, architecture |
| `cfo` | Chief Financial Officer | Budget, investments, financial analysis |
| `coo` | Chief Operations Officer | Project management, productivity, execution |
| `cmo` | Chief Marketing Officer | ASO, growth, content strategy |
| `architect` | Software Architect | System design, patterns, deep technical design |
| `researcher` | Research Analyst | Deep research, trend analysis, reports |
| `reviewer` | Code Reviewer | Security audit, code review, quality checks |
| `pi` | AI Coder (pi.dev) | Coding, refactoring, scaffolding |

## Memory & Persistence

Every agent has persistent memory in Obsidian:

```
Hermes Vault/Hermes/
├── System Memory — GT AI Dashboard v0.3.0.md
├── agents/
│   ├── cto/
│   ├── cfo/
│   └── ...
├── sessions/
└── swarm-log.md
```

Agents remember context across sessions. The more you use them, the better they understand your preferences.

## Directory Structure

```
agent-home/
├── README.md
├── setup.sh            # Reproducible installer
├── run-dashboard.sh    # Start web dashboard
├── agents/             # Agent definitions (YAML)
├── swarm/              # Orchestrator code
├── skills/             # Hermes/Pi skills (.md)
├── hermes/             # Hermes config
│   ├── config.json
│   └── memory/
├── pi/                 # Pi coding agent config
│   ├── pi.json
│   └── projects.json
├── projects/           # iOS and other project scaffolds
└── dashboard/          # Web dashboard (FastAPI + React)
    ├── backend/
    ├── frontend/
    └── data/
```

## Configuration

API keys are read from environment and config files:
- `KIMI_CODE_API_KEY` — Kimi Code (primary, all systems)
- `KIMI_API_KEY` — Legacy Moonshot platform (billing checks only)

Config files managed by the dashboard:
- `pi/pi.json`
- `hermes/config.json`
- `~/.hermes/config.yaml`
- `~/.hermes/.env`
- `dashboard/backend/.env`

## Adding a New Agent

1. Create `agents/<name>.yaml` with role, system_prompt, skills, etc.
2. Run `agents` to verify it appears
3. Add alias to `~/.zshrc`: `alias <name>="agent --agent <name>"`
4. Restart shell or `source ~/.zshrc`

## Swarm Mode

Swarm uses keyword-based routing to dispatch queries to the right specialists in parallel, then synthesizes their outputs.

```bash
# Automatically routes to relevant agents
swarm "what's the best tech stack for a real-time chat app and how much will it cost?"
# → Routes to cto + cfo in parallel, then synthesizes

# Force multi-agent with specific context
swarm "cmo + cfo: should we invest $50k in TikTok ads for our app?"
```

## Reinstall on a New Machine

```bash
cd ~/Public/MyFiles/agent-home
# Install Hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
# Install Pi
npm install -g @mariozechner/pi-coding-agent
# Source aliases
source ~/.zshrc
# Verify
agents
ai --version && pi --version
```

## Tech Notes

- **Python:** Use `python3.11` explicitly. Python 3.14 breaks pydantic-core.
- **Dashboard Backend:** FastAPI on port 7373, auto-reload in dev.
- **Dashboard Frontend:** Vite + React 19 + Tailwind on port 3000, proxied to backend `/api`.
- **PWA:** Installable. Built with `vite-plugin-pwa`. Update manifest in `frontend/vite.config.ts`.
