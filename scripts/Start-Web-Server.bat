@echo off
echo ========================================
echo   AI Cover Visualizer - Web Interface
echo ========================================
echo.

cd /d "%~dp0\..\src\node"

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo Checking dependencies...
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting web server...
echo.
echo Open your browser and go to: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

node server.js
cd /d "%~dp0\.."

if errorlevel 1 (
    echo.
    echo Server stopped with an error.
    pause
)
