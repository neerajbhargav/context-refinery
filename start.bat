@echo off
title ContextRefinery
echo.
echo   ========================================
echo    ContextRefinery - Starting...
echo   ========================================
echo.

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

:: Check Node
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)

:: Setup Python venv if needed
if not exist "src-backend\.venv" (
    echo [SETUP] Creating Python virtual environment...
    cd src-backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
) else (
    call src-backend\.venv\Scripts\activate.bat
)

:: Install Node deps if needed
if not exist "node_modules" (
    echo [SETUP] Installing frontend dependencies...
    call npm install -g pnpm 2>nul
    call pnpm install
)

:: Start backend in background
echo [START] Backend on http://127.0.0.1:8741
start /B "ContextRefinery-Backend" cmd /c "cd src-backend && .venv\Scripts\python.exe main.py"

:: Wait for backend
echo [WAIT] Waiting for backend...
:wait_loop
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:8741/api/health >nul 2>&1
if %ERRORLEVEL% neq 0 goto wait_loop
echo [OK] Backend ready!

:: Start frontend
echo [START] Frontend on http://localhost:1420
echo.
echo   ========================================
echo    Open http://localhost:1420 in your browser
echo    Press Ctrl+C to stop
echo   ========================================
echo.
call pnpm dev
