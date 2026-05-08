#!/bin/bash
# GT AI System Setup Script
# Run this on a new machine to recreate the full stack
#
# Location: /Users/gt/Public/MyFiles/agent-home/setup.sh

set -e

AGENT_HOME="/Users/gt/Public/MyFiles/agent-home"
SKILLS_SOURCE="/Users/gt/Public/MyFiles/01-Work/Miswag/miswag-ios/.agent/skills"

echo "=== GT AI System Setup ==="

# 1. Verify deps
echo "[1/6] Checking dependencies..."
which python3 || (echo "Python 3 required"; exit 1)
which node || (echo "Node.js required for Pi"; exit 1)

# 2. Install Hermes
if ! which hermes >/dev/null 2>&1; then
    echo "[2/6] Installing Hermes Agent..."
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
else
    echo "[2/6] Hermes already installed: $(hermes --version)"
fi

# 3. Install Pi
if ! which pi >/dev/null 2>&1; then
    echo "[3/6] Installing Pi coding agent..."
    npm install -g @mariozechner/pi-coding-agent
else
    echo "[3/6] Pi already installed: $(pi --version)"
fi

# 4. Link configs
echo "[4/6] Linking configs..."
mkdir -p ~/.hermes
ln -sf "$AGENT_HOME/hermes/config.json" ~/.hermes/config.json 2>/dev/null || true
ln -sf "$AGENT_HOME/pi/pi.json" ~/.pi.json 2>/dev/null || true

# 5. Source aliases
echo "[5/6] Updating shell..."
if ! grep -q "GT SWARM AGENTS" ~/.zshrc 2>/dev/null; then
    cat >> ~/.zshrc << 'EOF'

# ============================================
# GT SWARM AGENTS
# ============================================
export AGENT_HOME="/Users/gt/Public/MyFiles/agent-home"
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
EOF
    echo "Aliases added to ~/.zshrc"
else
    echo "Aliases already present"
fi

# 6. Seed skills
echo "[6/6] Seeding Hermes with skills..."
if [ -d "$SKILLS_SOURCE" ]; then
    for dir in "$SKILLS_SOURCE"/*/; do
        skill_name=$(basename "$dir")
        if [ -f "$dir/SKILL.md" ] && [ "$skill_name" != "docs" ]; then
            cp "$dir/SKILL.md" "$AGENT_HOME/skills/${skill_name}.md"
            echo "    Copied: $skill_name"
        fi
    done
fi
hermes skills import "$AGENT_HOME/skills/" 2>/dev/null || echo "    (hermes skills import not available)"

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "  1. Add KIMI_API_KEY to your shell env or ~/.zshrc"
echo "  2. source ~/.zshrc"
echo "  3. agents          # list agents"
echo "  4. cto 'hello'     # test an agent"
echo "  5. cd \$AGENT_HOME/dashboard && ./start.sh  # start web dashboard"
