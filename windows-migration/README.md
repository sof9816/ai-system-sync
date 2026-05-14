# GT AI System — Windows Migration Package

Complete migration kit to replicate the macOS GT stack on Windows.

## Contents

| File | Purpose |
|------|---------|
| `setup.ps1` | Main Windows PowerShell setup script |
| `WSL-SETUP.md` | Full WSL2 + Ubuntu setup (recommended) |
| `REMOTE-ACCESS.md` | How to give me remote access to your PC |
| `agent-home.zip` | Your full agent-home directory (generated) |

## Quick Start

### Option A: WSL2 (Recommended — 95% parity)

1. Install WSL2: `wsl --install -d Ubuntu` (in Admin PowerShell)
2. Restart PC
3. Copy `agent-home.zip` into WSL: `cp /mnt/c/Users/<you>/Downloads/agent-home.zip ~/`
4. Follow `WSL-SETUP.md`

### Option B: Native Windows (Limited — 60% parity)

1. Install Python 3.11, Node.js LTS, Git
2. Right-click `setup.ps1` → "Run with PowerShell" (as Admin)
3. Follow prompts

**Limitations of native Windows:**
- Hermes Agent may have reduced functionality (built for Unix)
- Some shell scripts won't work without WSL
- pi.dev works fine (Node.js based)
- Dashboard works fine

## What Gets Replicated

| Component | macOS Path | Windows Path | Notes |
|-----------|-----------|--------------|-------|
| Agent Home | `~/Public/MyFiles/agent-home` | `C:\Users\<you>\agent-home` | Full repo |
| Hermes Config | `~/.hermes/config.yaml` | `~/.hermes/config.yaml` | Copied |
| Hermes Config JSON | `~/.hermes/config.json` | `~/.hermes/config.json` | Copied |
| Pi Config | `~/.pi.json` | `~/.pi.json` | Copied |
| Skills | `gt-core/skills-repo/` | Same inside agent-home | 137 skills |
| Dashboard | `dashboard/` | Same | FastAPI + React |
| Swarm Scripts | `swarm/` | Same | Python agent runner |
| Aliases | `.zshrc` | PowerShell profile | Translated |
| Obsidian Vault | `~/Library/Mobile Documents/...` | `~/Documents/Obsidian Vault` | Copied |

## What You Must Do Manually

1. **API Keys**: Add `KIMI_CODE_API_KEY`, `KIMI_API_KEY`, etc. to env vars
2. **GitHub Auth**: `gh auth login` if using GH CLI
3. **Obsidian**: Download from obsidian.md, open vault folder
4. **Hermes Login**: May need to re-auth if using cloud features

## Remote Access

If you want me to do this for you, see `REMOTE-ACCESS.md`.
