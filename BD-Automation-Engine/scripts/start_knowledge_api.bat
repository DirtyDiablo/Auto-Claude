@echo off
echo ============================================
echo   BD Knowledge API Startup
echo ============================================
echo.

cd /d "%~dp0.."

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Starting Knowledge API on http://localhost:8100
echo Press Ctrl+C to stop
echo.

python Engine8_Knowledge/api.py

pause
