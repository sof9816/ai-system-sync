# AI System Sync

Unified configuration sync for GT's multi-agent AI infrastructure.

## What It Syncs

| Component | Path in Repo | Local Path (Mac) | Local Path (PC)
|-----------|-------------|------------------|-----------------|
| Hermes Config | `hermes/config.yaml` | `~/.hermes/config.yaml` | `~/.hermes/config.yaml` |
| Hermes Scripts | `hermes/scripts/` | `~/.hermes/scripts/` | `~/.hermes/scripts/` |
| pi.dev Config | `pi/config.json` | `~/.pi/config.json` | `~/.pi/config.json` |
| GT Dashboard Agents | `gt-dashboard/` | `~/Public/MyFiles/agent-home/agents/` | `~/agent-home/agents/` |
| Obsidian Hermes Vault | `obsidian/hermes-vault-config/` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes/Hermes/.obsidian/` | iCloud or manual |
| Obsidian GT Vault | `obsidian/gt-vault-config/` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault/.obsidian/` | iCloud or manual |

## What It Does NOT Sync

- **Skills repo** — already has its own Git repo (`sof9816/ai-skills`)
- **Vault content** — managed by iCloud Obsidian sync
- **Secrets / API keys** — never commit these; use env vars

## Setup

### Mac (Primary)

Already done. Cron runs every 15 minutes.

### PC (Windows + WSL2)

1. Install Git for Windows or use WSL2 Ubuntu
2. Clone this repo: `git clone https://github.com/sof9816/ai-system-sync.git ~/.ai-system-sync`
3. Run: `bash ~/.ai-system-sync/scripts/sync-ai-system.sh`
4. Add to Task Scheduler or WSL cron:
   ```bash
   # In WSL:
   crontab -e
   # Add:
   */15 * * * * bash ~/.ai-system-sync/scripts/sync-ai-system.sh >> ~/.ai-system-sync/sync.log 2>&1
   ```

## Manual Sync

```bash
bash ~/.ai-system-sync/scripts/sync-ai-system.sh
```

## Conflict Resolution

If both Mac and PC push simultaneously:
1. Script auto-stashes local changes
2. Pulls remote
3. Pops stash
4. If merge conflict → logs to `sync.log`, manual fix required
