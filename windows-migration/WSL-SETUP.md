# GT AI System — WSL2 Setup (Recommended)

Hermes Agent is built for Unix-like environments. For full feature parity with macOS, run the entire stack inside WSL2 + Ubuntu.

## 1. Install WSL2

```powershell
# Run in PowerShell as Administrator
wsl --install -d Ubuntu
# Restart PC when prompted
```

## 2. Inside Ubuntu (WSL)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install deps
sudo apt install -y python3 python3-pip python3-venv nodejs npm git curl

# Install Hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc

# Install pi.dev
npm install -g @mariozechner/pi-coding-agent

# Verify
hermes --version
pi --version
```

## 3. Mount Windows agent-home

WSL auto-mounts Windows drives at `/mnt/`:

```bash
# Create symlink so paths work
sudo ln -s /mnt/c/Users/$USER/agent-home /home/$USER/agent-home
export AGENT_HOME=/home/$USER/agent-home
```

Or copy it into WSL for better performance:

```bash
cp -r /mnt/c/Users/$USER/agent-home /home/$USER/
```

## 4. Link configs (inside WSL)

```bash
mkdir -p ~/.hermes
ln -sf ~/agent-home/hermes/config.yaml ~/.hermes/config.yaml
ln -sf ~/agent-home/hermes/config.json ~/.hermes/config.json
ln -sf ~/agent-home/pi/pi.json ~/.pi.json
```

## 5. Add aliases to ~/.bashrc

```bash
cat >> ~/.bashrc << 'EOF'

# GT SWARM AGENTS
export AGENT_HOME="/home/$USER/agent-home"
export PATH="$AGENT_HOME/swarm:$PATH"

alias cto="agent --agent cto"
alias cfo="agent --agent cfo"
alias coo="agent --agent coo"
alias cmo="agent --agent cmo"
alias architect="agent --agent architect"
alias researcher="agent --agent researcher"
alias reviewer="agent --agent reviewer"
alias swarm="agent --swarm"
alias agents="agent --list"
alias ai="hermes"
alias ai-review="hermes --skill code-reviewer"
alias ai-arch="hermes --skill architecture"
alias code-ai="$AGENT_HOME/gt-core/scripts/pi-start.py --provider kimi-coding --model kimi-k2.6"
alias ai-ios="hermes --skill ios-developer,swiftui-pro,swift-concurrency-pro,swift-testing-pro,xcode-build-orchestrator,xcode-project-analyzer,mobile-security-coder,mobile-ui,miswag-ios-developer"
alias code-ios="$AGENT_HOME/gt-core/scripts/pi-start.py --provider kimi-coding --model kimi-k2.6 --no-auto-skills --skill ios-developer,swiftui-pro,swift-concurrency-pro,swift-testing-pro,xcode-build-orchestrator,xcode-project-analyzer,mobile-security-coder,mobile-ui,miswag-ios-developer"
alias ai-node="hermes --skill frontend-developer,testing-patterns"
alias code-node="$AGENT_HOME/gt-core/scripts/pi-start.py --provider kimi-coding --model kimi-k2.6 --no-auto-skills --skill frontend-developer,testing-patterns"
alias ai-python="hermes --skill testing-patterns"
alias code-python="$AGENT_HOME/gt-core/scripts/pi-start.py --provider kimi-coding --model kimi-k2.6 --no-auto-skills --skill testing-patterns"
alias gtdashboard="cd $AGENT_HOME/dashboard && ./start.sh"
EOF
source ~/.bashrc
```

## 6. Dashboard

```bash
cd ~/agent-home/dashboard/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd ~/agent-home/dashboard/frontend
npm install
```

Start:
```bash
gtdashboard
```

Access from Windows browser at `http://localhost:3000` (WSL forwards ports automatically).

## 7. Obsidian

Install Obsidian on **Windows** (not WSL). Point vault to:
- `C:\Users\<you>\Documents\Obsidian Vault` (Windows path)
- Or `\\wsl$\Ubuntu\home\<you>\agent-home\GT Vault` (WSL path)

## 8. API Keys

Add to `~/.bashrc` inside WSL:

```bash
export KIMI_CODE_API_KEY="your-key"
export KIMI_API_KEY="your-key"
export OPENROUTER_API_KEY="optional"
```

## Architecture

```
Windows Host
├── Obsidian (native app)
├── Browser → localhost:3000 (auto-forwarded from WSL)
└── WSL2 Ubuntu
    ├── Hermes Agent
    ├── pi.dev
    ├── Dashboard backend + frontend
    └── agent-home/
```
