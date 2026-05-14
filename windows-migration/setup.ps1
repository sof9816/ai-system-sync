# GT AI System — Windows Setup Script
# Run as Administrator in PowerShell
# This recreates the full macOS stack on Windows

$ErrorActionPreference = "Stop"

# ============================================
# CONFIG — adjust these paths if needed
# ============================================
$AgentHome = "C:\Users\$env:USERNAME\agent-home"
$ObsidianVault = "C:\Users\$env:USERNAME\Documents\Obsidian Vault"
$HermesDir = "$env:USERPROFILE\.hermes"
$PiConfig = "$env:USERPROFILE\.pi.json"

# ============================================
# 0. CHECK ADMIN
# ============================================
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Run this script as Administrator" -ForegroundColor Red
    exit 1
}

Write-Host "=== GT AI System Windows Setup ===" -ForegroundColor Cyan
Write-Host "Agent Home: $AgentHome"
Write-Host ""

# ============================================
# 1. DEPENDENCIES
# ============================================
Write-Host "[1/9] Checking dependencies..." -ForegroundColor Yellow

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "Python not found. Install from python.org (3.11 recommended)" -ForegroundColor Red
    exit 1
}
$pyVersion = & $python.Source --version
Write-Host "  Python: $pyVersion"

# Check Node
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "Node.js not found. Install from nodejs.org (LTS recommended)" -ForegroundColor Red
    exit 1
}
$nodeVersion = & node --version
Write-Host "  Node: $nodeVersion"

# Check Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git not found. Install from git-scm.com" -ForegroundColor Red
    exit 1
}
Write-Host "  Git: OK"

# Check GitHub CLI
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    Write-Host "  WARNING: gh CLI not found. Install: winget install GitHub.cli" -ForegroundColor DarkYellow
} else {
    Write-Host "  gh: OK"
}

# ============================================
# 2. EXTRACT AGENT-HOME ARCHIVE
# ============================================
Write-Host ""
Write-Host "[2/9] Setting up agent-home..." -ForegroundColor Yellow

if (-not (Test-Path "$PSScriptRoot\agent-home.zip")) {
    Write-Host "ERROR: agent-home.zip not found in same directory as this script" -ForegroundColor Red
    Write-Host "Make sure you copied the entire windows-migration folder" -ForegroundColor Red
    exit 1
}

if (Test-Path $AgentHome) {
    Write-Host "  agent-home already exists at $AgentHome"
    $overwrite = Read-Host "  Overwrite? (y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Remove-Item -Recurse -Force $AgentHome
    } else {
        Write-Host "  Skipping extraction"
    }
}

if (-not (Test-Path $AgentHome)) {
    Expand-Archive -Path "$PSScriptRoot\agent-home.zip" -DestinationPath (Split-Path $AgentHome -Parent) -Force
    Write-Host "  Extracted to $AgentHome"
}

# ============================================
# 3. INSTALL HERMES AGENT
# ============================================
Write-Host ""
Write-Host "[3/9] Installing Hermes Agent..." -ForegroundColor Yellow

$hermesBin = "$env:USERPROFILE\.local\bin\hermes.exe"
if (Test-Path $hermesBin) {
    Write-Host "  Hermes already installed"
} else {
    # Hermes doesn't have a Windows installer yet — use pip install from source or WSL
    Write-Host "  Hermes Windows native binary not available. Options:" -ForegroundColor DarkYellow
    Write-Host "    A) Install in WSL2 (recommended — full feature parity)" -ForegroundColor White
    Write-Host "    B) Use pip install from Hermes git repo (limited)" -ForegroundColor White
    $choice = Read-Host "  Choose (A/B)"
    if ($choice -eq "A" -or $choice -eq "a") {
        Write-Host "  Install WSL2 + Ubuntu, then run the Linux setup script inside WSL"
        Write-Host "  See WSL-SETUP.md for instructions"
    } else {
        Write-Host "  Attempting pip install from source..."
        & $python.Source -m pip install git+https://github.com/nousresearch/hermes-agent.git
    }
}

# ============================================
# 4. INSTALL PI.DEV
# ============================================
Write-Host ""
Write-Host "[4/9] Installing pi.dev..." -ForegroundColor Yellow

$piBin = "$env:APPDATA\npm\pi.cmd"
if (Test-Path $piBin) {
    Write-Host "  pi.dev already installed"
} else {
    npm install -g @mariozechner/pi-coding-agent
    Write-Host "  pi.dev installed"
}

# ============================================
# 5. LINK CONFIGS
# ============================================
Write-Host ""
Write-Host "[5/9] Linking configs..." -ForegroundColor Yellow

# Hermes config
$hermesConfigSource = "$AgentHome\hermes\config.yaml"
$hermesConfigDest = "$HermesDir\config.yaml"
if (Test-Path $hermesConfigSource) {
    New-Item -ItemType Directory -Force -Path $HermesDir | Out-Null
    Copy-Item -Path $hermesConfigSource -Destination $hermesConfigDest -Force
    Write-Host "  Copied Hermes config.yaml"
} else {
    Write-Host "  WARNING: hermes/config.yaml not found in agent-home" -ForegroundColor DarkYellow
}

# Hermes config.json
$hermesJsonSource = "$AgentHome\hermes\config.json"
$hermesJsonDest = "$HermesDir\config.json"
if (Test-Path $hermesJsonSource) {
    Copy-Item -Path $hermesJsonSource -Destination $hermesJsonDest -Force
    Write-Host "  Copied Hermes config.json"
}

# Pi config
$piJsonSource = "$AgentHome\pi\pi.json"
if (Test-Path $piJsonSource) {
    Copy-Item -Path $piJsonSource -Destination $PiConfig -Force
    Write-Host "  Copied pi.json"
} else {
    Write-Host "  WARNING: pi/pi.json not found" -ForegroundColor DarkYellow
}

# ============================================
# 6. SET ENVIRONMENT VARIABLES
# ============================================
Write-Host ""
Write-Host "[6/9] Setting environment variables..." -ForegroundColor Yellow

[Environment]::SetEnvironmentVariable("AGENT_HOME", $AgentHome, "User")
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;$AgentHome\swarm", "User")

# Add to current session
$env:AGENT_HOME = $AgentHome
$env:PATH += ";$AgentHome\swarm"

Write-Host "  AGENT_HOME = $AgentHome"
Write-Host "  Added swarm to PATH"

# ============================================
# 7. SETUP OBSIDIAN VAULT
# ============================================
Write-Host ""
Write-Host "[7/9] Setting up Obsidian vault..." -ForegroundColor Yellow

if (-not (Test-Path $ObsidianVault)) {
    New-Item -ItemType Directory -Force -Path $ObsidianVault | Out-Null
    Write-Host "  Created Obsidian vault at $ObsidianVault"
} else {
    Write-Host "  Obsidian vault already exists"
}

# Copy GT Vault contents if present in agent-home
$gtVaultSource = "$AgentHome\GT Vault"
if (Test-Path $gtVaultSource) {
    Copy-Item -Path "$gtVaultSource\*" -Destination $ObsidianVault -Recurse -Force
    Write-Host "  Copied GT Vault contents"
}

# ============================================
# 8. SETUP DASHBOARD
# ============================================
Write-Host ""
Write-Host "[8/9] Setting up dashboard..." -ForegroundColor Yellow

$backendDir = "$AgentHome\dashboard\backend"
$frontendDir = "$AgentHome\dashboard\frontend"

if (Test-Path $backendDir) {
    Write-Host "  Setting up Python backend..."
    Set-Location $backendDir
    & $python.Source -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    deactivate
    Write-Host "  Backend venv ready"
}

if (Test-Path $frontendDir) {
    Write-Host "  Setting up Node frontend..."
    Set-Location $frontendDir
    npm install
    Write-Host "  Frontend deps installed"
}

Set-Location $PSScriptRoot

# ============================================
# 9. CREATE ALIASES (PowerShell profile)
# ============================================
Write-Host ""
Write-Host "[9/9] Creating PowerShell aliases..." -ForegroundColor Yellow

$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
}

$aliases = @"

# ============================================
# GT SWARM AGENTS
# ============================================
`$env:AGENT_HOME = "$AgentHome"
`$env:PATH += ";$AgentHome\swarm"

function cto { agent --agent cto `@args }
function cfo { agent --agent cfo `@args }
function coo { agent --agent coo `@args }
function cmo { agent --agent cmo `@args }
function architect { agent --agent architect `@args }
function researcher { agent --agent researcher `@args }
function reviewer { agent --agent reviewer `@args }
function swarm { agent --swarm `@args }
function agents { agent --list }

function ai { hermes `@args }
function ai-review { hermes --skill code-reviewer `@args }
function ai-arch { hermes --skill architecture `@args }
function code-ai { & "$AgentHome\gt-core\scripts\pi-start.py" --provider kimi-coding --model kimi-k2.6 `@args }
function ai-ios { hermes --skill ios-developer,swiftui-pro,swift-concurrency-pro,swift-testing-pro,xcode-build-orchestrator,xcode-project-analyzer,mobile-security-coder,mobile-ui,miswag-ios-developer `@args }
function code-ios { & "$AgentHome\gt-core\scripts\pi-start.py" --provider kimi-coding --model kimi-k2.6 --no-auto-skills --skill ios-developer,swiftui-pro,swift-concurrency-pro,swift-testing-pro,xcode-build-orchestrator,xcode-project-analyzer,mobile-security-coder,mobile-ui,miswag-ios-developer `@args }
function ai-node { hermes --skill frontend-developer,testing-patterns `@args }
function code-node { & "$AgentHome\gt-core\scripts\pi-start.py" --provider kimi-coding --model kimi-k2.6 --no-auto-skills --skill frontend-developer,testing-patterns `@args }
function ai-python { hermes --skill testing-patterns `@args }
function code-python { & "$AgentHome\gt-core\scripts\pi-start.py" --provider kimi-coding --model kimi-k2.6 --no-auto-skills --skill testing-patterns `@args }

function gtdashboard {
    `$backendDir = "$AgentHome\dashboard\backend"
    `$frontendDir = "$AgentHome\dashboard\frontend"
    `$logDir = "$AgentHome\dashboard\logs"
    New-Item -ItemType Directory -Force -Path `$logDir | Out-Null

    # Kill existing
    Get-NetTCPConnection -LocalPort 7373 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id `$_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id `$_.OwningProcess -Force -ErrorAction SilentlyContinue }

    # Start backend
    Set-Location `$backendDir
    .\venv\Scripts\Activate.ps1
    Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "app.main:app --host 0.0.0.0 --port 7373" -RedirectStandardOutput "`$logDir\backend.log" -RedirectStandardError "`$logDir\backend.err"
    deactivate

    # Start frontend
    Set-Location `$frontendDir
    Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run dev" -RedirectStandardOutput "`$logDir\frontend.log" -RedirectStandardError "`$logDir\frontend.err"

    Set-Location "$AgentHome"
    Start-Sleep 3
    Start-Process "http://localhost:3000"
}

function gtdashboard-stop {
    Get-NetTCPConnection -LocalPort 7373 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id `$_.OwningProcess -Force }
    Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id `$_.OwningProcess -Force }
    Write-Host "Dashboard stopped"
}
"@

if (-not (Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
}

if (-not (Select-String -Path $PROFILE -Pattern "GT SWARM AGENTS" -Quiet)) {
    Add-Content -Path $PROFILE -Value $aliases
    Write-Host "  Aliases added to PowerShell profile"
    Write-Host "  Run `. `$PROFILE` to load in current session"
} else {
    Write-Host "  Aliases already present in profile"
}

# ============================================
# DONE
# ============================================
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Add API keys to environment variables (User or System):" -ForegroundColor White
Write-Host "     KIMI_CODE_API_KEY" -ForegroundColor Gray
Write-Host "     KIMI_API_KEY" -ForegroundColor Gray
Write-Host "     OPENROUTER_API_KEY (optional)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Restart PowerShell to load new profile" -ForegroundColor White
Write-Host ""
Write-Host "  3. Test:" -ForegroundColor White
Write-Host "     hermes --version" -ForegroundColor Gray
Write-Host "     pi --version" -ForegroundColor Gray
Write-Host "     agents" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Start dashboard:" -ForegroundColor White
Write-Host "     gtdashboard" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Install Obsidian from obsidian.md and open vault at:" -ForegroundColor White
Write-Host "     $ObsidianVault" -ForegroundColor Gray
Write-Host ""
Write-Host "IMPORTANT: Hermes on Windows" -ForegroundColor Yellow
Write-Host "  For full feature parity, install WSL2 + Ubuntu and run Hermes there." -ForegroundColor White
Write-Host "  See WSL-SETUP.md in this folder." -ForegroundColor White
