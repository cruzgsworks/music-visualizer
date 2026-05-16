@echo off
echo ========================================
echo   AI Cover Visualizer - Launcher
echo ========================================
echo.

:: Move to project root
cd /d "%~dp0\.."

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import tkinter, librosa, PIL, numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting Visualizer GUI...
echo.
python src\python\visualizer_gui.py
if errorlevel 1 (
    echo.
    echo An error occurred. Check the output above.
    pause
)
