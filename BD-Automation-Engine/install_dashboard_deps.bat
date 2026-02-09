@echo off
REM ═══════════════════════════════════════════════════
REM PTS BD Dashboard — Quick Dependency Installer
REM Run from BD-Automation-Engine root directory
REM ═══════════════════════════════════════════════════

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  PTS BD Dashboard - Dependency Installation      ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Find the frontend directory
IF EXIST "frontend\package.json" (
    set FRONTEND_DIR=frontend
) ELSE IF EXIST "dashboard\package.json" (
    set FRONTEND_DIR=dashboard
) ELSE IF EXIST "package.json" (
    set FRONTEND_DIR=.
) ELSE (
    echo ERROR: Cannot find package.json. Run from project root.
    exit /b 1
)

echo Found frontend at: %FRONTEND_DIR%
cd %FRONTEND_DIR%

echo.
echo [1/6] Installing dashboard analytics...
call npm install @tremor/react

echo.
echo [2/6] Installing data management...
call npm install @tanstack/react-table react-hook-form @hookform/resolvers zod

echo.
echo [3/6] Installing drag-and-drop...
call npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities

echo.
echo [4/6] Installing UI utilities...
call npm install cmdk framer-motion date-fns

echo.
echo [5/6] Installing graph visualization (G6 v5)...
call npm install @antv/g6

echo.
echo [6/6] Verifying installation...
echo.
echo Checking installed packages:
call npm list @tremor/react @tanstack/react-table @dnd-kit/core cmdk framer-motion @antv/g6 zod react-hook-form date-fns --depth=0 2>nul

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  Installation complete!                          ║
echo ║  Run: npm run dev   to start the dashboard      ║
echo ╚══════════════════════════════════════════════════╝
echo.

cd ..
