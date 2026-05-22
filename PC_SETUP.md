# PC Setup Guide (Windows + WSL2)

## One-Time Setup

### 1. WSL2 Ubuntu — Open Terminal

```bash
# Update packages
sudo apt update && sudo apt install -y git curl

# Clone the sync repo
git clone https://github.com/sof9816/ai-system-sync.git ~/.ai-system-sync

# Run first sync
bash ~/.ai-system-sync/scripts/sync-ai-system.sh
```

### 2. Install Hermes Agent (if not already)

Follow: https://hermes-agent.nousresearch.com/docs

### 3. Install pi.dev (if not already)

Follow pi.dev installation docs.

### 4. Auto-Sync Cron (WSL)

```bash
crontab -e
# Add this line:
*/15 * * * * /bin/bash ~/.ai-system-sync/scripts/sync-ai-system.sh >> ~/.ai-system-sync/sync.log 2>&1
```

### 5. Windows Task Scheduler (Alternative)

If WSL cron is unreliable:
- Open Task Scheduler
- Create Basic Task → "AI Sync"
- Trigger: Every 15 minutes
- Action: Start Program
- Program: `wsl.exe`
- Arguments: `bash ~/.ai-system-sync/scripts/sync-ai-system.sh`

## Directory Mapping

| Mac Path | PC (WSL) Path |
|----------|---------------|
| `~/.hermes/` | `~/.hermes/` |
| `~/.pi/` | `~/.pi/` |
| `~/.agents/` | `~/.agents/` |
| `~/Public/MyFiles/agent-home/agents/` | `~/agent-home/agents/` or `C:\agent-home\agents\` |

## Important Notes

- **Skills repo** is separate: `https://github.com/sof9816/ai-skills.git`
- **Obsidian vault content** syncs via iCloud — install Obsidian on PC and open the same vault
- **Never commit API keys** — the sync script skips `.env`, `tokens.json`, and `credentials`
- If sync conflicts occur, check `~/.ai-system-sync/sync.log`
