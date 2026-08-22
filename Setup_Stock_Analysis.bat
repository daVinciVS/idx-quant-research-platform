@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo STOCK ANALYSIS - FIRST TIME SETUP
echo ============================================================
echo.

where python >nul 2>nul

if errorlevel 1 (
    echo ERROR: Python was not found.
    echo.
    echo Install Python 3.10 or newer from:
    echo https://www.python.org/downloads/
    echo.
    echo During installation, enable:
    echo Add Python to PATH
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo.
echo Installing required Python libraries...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo ============================================================
echo SETUP COMPLETED SUCCESSFULLY
echo ============================================================
echo.
echo Next step:
echo Double-click Run_Stock_Analysis.bat
echo.
pause