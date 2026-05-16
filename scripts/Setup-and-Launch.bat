@echo off
echo ========================================
echo   AI Cover Visualizer - Setup and Launch
echo ========================================
echo.

:: Move to project root
cd /d "%~dp0\.."

echo Checking prerequisites...
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)
python --version

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js not found. Web interface will not work.
    echo Install from: https://nodejs.org
    echo.
)

:: Check ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ffmpeg not found. Video generation will fail.
    echo Install with: choco install ffmpeg
    echo Or download from: https://ffmpeg.org/download.html
    echo.
)

echo.
echo Checking Python dependencies...
python -c "import librosa" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        pause
        exit /b 1
    )
) else (
    echo [OK] Python dependencies already installed
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo What would you like to launch?
echo.
echo [1] Web Interface (Recommended) - http://localhost:3000
echo [2] Desktop GUI (Python tkinter)
echo [3] Exit
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Starting Web Server...
    echo Open your browser to: http://localhost:3000
    echo.
    cd src\node
    node server.js
) else if "%choice%"=="2" (
    echo.
    echo Starting Desktop GUI...
    python src\python\visualizer_gui.py
) else (
    echo.
    echo Exiting. To launch later:
    echo   Web: scripts\Start-Web-Server.bat
    echo   GUI: scripts\Launch-Visualizer.bat
)

echo.
pause
