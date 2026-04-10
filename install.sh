#!/usr/bin/env bash
# ContextRefinery — One-Line Mac/Linux Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/neerajbhargav/context-refinery/master/install.sh | bash
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "  ${CYAN}========================================${NC}"
echo -e "  ${CYAN} ContextRefinery Installer${NC}"
echo -e "  ${CYAN}========================================${NC}"
echo ""

INSTALL_DIR="$HOME/.local/share/context-refinery"
REPO="https://github.com/neerajbhargav/context-refinery.git"

# ── Check prerequisites ────────────────────────────────────────────

check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo -e "${GREEN}[OK]${NC} $2 found"
        return 0
    else
        echo -e "${RED}[MISSING]${NC} $2 — $3"
        return 1
    fi
}

ok=true
check_cmd python3 "Python 3.11+" "Install from python.org or: brew install python" || ok=false
check_cmd node "Node.js 18+" "Install from nodejs.org or: brew install node" || ok=false
check_cmd git "Git" "Install from git-scm.com or: brew install git" || ok=false

if [ "$ok" = false ]; then
    echo ""
    echo -e "${YELLOW}Please install the missing prerequisites and re-run this script.${NC}"
    exit 1
fi

# ── Clone or update ────────────────────────────────────────────────

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[UPDATE]${NC} Pulling latest changes..."
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    echo -e "${YELLOW}[INSTALL]${NC} Cloning repository..."
    git clone "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ── Python backend setup ──────────────────────────────────────────

echo -e "${YELLOW}[SETUP]${NC} Setting up Python backend..."
cd src-backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q
if [ ! -f ".env" ]; then
    cp .env.example .env
fi
deactivate
cd ..

# ── Node frontend setup ──────────────────────────────────────────

echo -e "${YELLOW}[SETUP]${NC} Setting up frontend..."
if ! command -v pnpm &>/dev/null; then
    npm install -g pnpm
fi
pnpm install

# ── Create launcher symlink ──────────────────────────────────────

chmod +x start.sh
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/start.sh" "$HOME/.local/bin/context-refinery"

# ── macOS: create .app bundle ────────────────────────────────────

if [ "$(uname)" = "Darwin" ]; then
    APP_DIR="$HOME/Applications/ContextRefinery.app/Contents/MacOS"
    mkdir -p "$APP_DIR"
    cat > "$APP_DIR/ContextRefinery" << 'APPEOF'
#!/bin/bash
cd "$HOME/.local/share/context-refinery"
open "http://localhost:1420" &
exec ./start.sh
APPEOF
    chmod +x "$APP_DIR/ContextRefinery"

    # Info.plist
    cat > "$HOME/Applications/ContextRefinery.app/Contents/Info.plist" << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>ContextRefinery</string>
    <key>CFBundleIdentifier</key><string>com.contextrefinery.app</string>
    <key>CFBundleVersion</key><string>0.1.0</string>
    <key>CFBundleExecutable</key><string>ContextRefinery</string>
</dict>
</plist>
PLISTEOF
    echo -e "${GREEN}[OK]${NC} Created ~/Applications/ContextRefinery.app"
fi

# ── Linux: create .desktop entry ─────────────────────────────────

if [ "$(uname)" = "Linux" ]; then
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/context-refinery.desktop" << DESKTOPEOF
[Desktop Entry]
Name=ContextRefinery
Comment=AI Context Orchestration Engine
Exec=bash -c 'cd $INSTALL_DIR && ./start.sh'
Terminal=true
Type=Application
Categories=Development;
DESKTOPEOF
    echo -e "${GREEN}[OK]${NC} Created desktop entry"
fi

echo ""
echo -e "  ${GREEN}========================================${NC}"
echo -e "  ${GREEN} Installation complete!${NC}"
echo -e "  ${GREEN}========================================${NC}"
echo ""
echo -e "  Installed to: ${CYAN}$INSTALL_DIR${NC}"
echo ""
echo -e "  To start:"
echo -e "    ${CYAN}context-refinery${NC}                    (if ~/.local/bin is in PATH)"
echo -e "    ${CYAN}cd $INSTALL_DIR && ./start.sh${NC}       (direct)"
if [ "$(uname)" = "Darwin" ]; then
    echo -e "    Or open ${CYAN}ContextRefinery${NC} from ~/Applications"
fi
echo ""

read -p "Launch ContextRefinery now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    cd "$INSTALL_DIR"
    exec ./start.sh
fi
