@echo off
echo ========================================
echo   AI Cover Visualizer
echo ========================================
echo.
echo Welcome! This launcher will help you get started.
echo.

:: Move to project root
cd /d "%~dp0\.."

:: Check if Python dependencies are installed
echo Checking if setup is complete...
python -c "import librosa, numpy, PIL" >nul 2>&1

if errorlevel 1 (
    echo.
    echo First time setup required!
    echo.
    echo Would you like to:
    echo   [1] Run full setup (install dependencies and launch)
    echo   [2] Just check what's installed
    echo   [3] Launch anyway (if you know dependencies are installed)
    echo.
    
    set /p choice="Enter choice (1-3): "
    
    if "!choice!"=="1" (
        echo.
        echo Starting full setup...
        pause
        powershell -ExecutionPolicy Bypass -File "scripts\Setup.ps1"
    ) else if "!choice!"=="2" (
        call scripts\Check-Setup.bat
    ) else (
        goto menu
    )
) else (
    echo Setup complete! Dependencies already installed.
    goto menu
)

:menu
cls
echo ========================================
echo   AI Cover Visualizer - Main Menu
echo ========================================
echo.
echo Choose an option:
echo.
echo   [1] Start Web Interface (Recommended)
echo       Modern web UI with drag and drop
       Access at http://localhost:3000
echo.
echo   [2] Start Desktop GUI
echo       Traditional desktop application
echo.
echo   [3] Check Setup
echo       Verify all dependencies are installed
echo.
echo   [4] Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    call scripts\Start-Web-Server.bat
) else if "%choice%"=="2" (
    call scripts\Launch-Visualizer.bat
) else if "%choice%"=="3" (
    call scripts\Check-Setup.bat
) else (
    echo.
    echo Goodbye!
    exit /b 0
)
