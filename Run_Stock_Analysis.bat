@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo AUTOMATED IDX STOCK ANALYSIS SYSTEM
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment was not found.
    echo Expected location:
    echo .venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "generate_report.py"

echo.
echo ============================================================
echo Application finished.
echo Press any key to close this window.
echo ============================================================

pause > nul