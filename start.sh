#!/usr/bin/env bash
set -e

echo ""
echo "  ========================================"
echo "   ContextRefinery — Starting..."
echo "  ========================================"
echo ""

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 not found. Install Python 3.11+ first."
    exit 1
fi

# Check Node
if ! command -v node &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Node.js not found. Install Node.js 18+ first."
    exit 1
fi

# Setup Python venv if needed
if [ ! -d "src-backend/.venv" ]; then
    echo -e "${YELLOW}[SETUP]${NC} Creating Python virtual environment..."
    cd src-backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    source src-backend/.venv/bin/activate
fi

# Install Node deps if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[SETUP]${NC} Installing frontend dependencies..."
    npm install -g pnpm 2>/dev/null || true
    pnpm install
fi

# Start backend in background
echo -e "${GREEN}[START]${NC} Backend on http://127.0.0.1:8741"
(cd src-backend && python3 main.py) &
BACKEND_PID=$!

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for backend
echo -e "${YELLOW}[WAIT]${NC} Waiting for backend..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8741/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} Backend ready!"
        break
    fi
    sleep 1
done

# Start frontend
echo -e "${GREEN}[START]${NC} Frontend on http://localhost:1420"
echo ""
echo "  ========================================"
echo "   Open http://localhost:1420 in your browser"
echo "   Press Ctrl+C to stop"
echo "  ========================================"
echo ""
pnpm dev

cleanup
