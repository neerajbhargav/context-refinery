# ContextRefinery — One-Line Windows Installer
# Usage: irm https://raw.githubusercontent.com/neerajbhargav/context-refinery/master/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host "   ContextRefinery Installer" -ForegroundColor Cyan
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""

$INSTALL_DIR = "$env:LOCALAPPDATA\ContextRefinery"
$REPO = "https://github.com/neerajbhargav/context-refinery.git"

# ── Check prerequisites ────────────────────────────────────────────

function Check-Command($cmd, $name, $installHint) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "[MISSING] $name — $installHint" -ForegroundColor Red
        return $false
    }
    Write-Host "[OK] $name found" -ForegroundColor Green
    return $true
}

$ok = $true
if (!(Check-Command "python" "Python 3.11+" "Install from python.org")) { $ok = $false }
if (!(Check-Command "node" "Node.js 18+" "Install from nodejs.org")) { $ok = $false }
if (!(Check-Command "git" "Git" "Install from git-scm.com")) { $ok = $false }

if (!$ok) {
    Write-Host ""
    Write-Host "Please install the missing prerequisites and re-run this script." -ForegroundColor Yellow
    exit 1
}

# ── Clone or update ────────────────────────────────────────────────

if (Test-Path $INSTALL_DIR) {
    Write-Host "[UPDATE] Pulling latest changes..." -ForegroundColor Yellow
    Push-Location $INSTALL_DIR
    git pull --ff-only
    Pop-Location
} else {
    Write-Host "[INSTALL] Cloning repository..." -ForegroundColor Yellow
    git clone $REPO $INSTALL_DIR
}

Push-Location $INSTALL_DIR

# ── Python backend setup ──────────────────────────────────────────

Write-Host "[SETUP] Setting up Python backend..." -ForegroundColor Yellow
Push-Location src-backend
if (!(Test-Path ".venv")) {
    python -m venv .venv
}
& .venv\Scripts\pip.exe install -r requirements.txt -q
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
Pop-Location

# ── Node frontend setup ──────────────────────────────────────────

Write-Host "[SETUP] Setting up frontend..." -ForegroundColor Yellow
if (!(Get-Command "pnpm" -ErrorAction SilentlyContinue)) {
    npm install -g pnpm
}
pnpm install

# ── Create desktop shortcut ──────────────────────────────────────

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "ContextRefinery.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $INSTALL_DIR "start.bat"
$shortcut.WorkingDirectory = $INSTALL_DIR
$shortcut.Description = "ContextRefinery — Context Orchestration Engine"
$shortcut.Save()

# ── Create Start Menu entry ──────────────────────────────────────

$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$startShortcut = $WshShell.CreateShortcut("$startMenuPath\ContextRefinery.lnk")
$startShortcut.TargetPath = Join-Path $INSTALL_DIR "start.bat"
$startShortcut.WorkingDirectory = $INSTALL_DIR
$startShortcut.Description = "ContextRefinery — Context Orchestration Engine"
$startShortcut.Save()

Pop-Location

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Green
Write-Host "   Installation complete!" -ForegroundColor Green
Write-Host "  ========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Installed to: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host "  Desktop shortcut: ContextRefinery" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To start: double-click the desktop shortcut" -ForegroundColor White
Write-Host "         or: cd $INSTALL_DIR && .\start.bat" -ForegroundColor White
Write-Host ""

# Ask to launch now
$launch = Read-Host "Launch ContextRefinery now? (Y/n)"
if ($launch -ne "n") {
    Push-Location $INSTALL_DIR
    & .\start.bat
}
