@echo off
echo ========================================
echo   AI Cover Visualizer - Quick Test
echo ========================================
echo.

cd /d "%~dp0\.."

echo Testing Python dependencies...
python -c "import librosa; import numpy; import PIL; print('[OK] All Python dependencies found')" 2>&1
if errorlevel 1 (
    echo [X] Python dependencies missing. Run Setup.ps1 first.
    pause
    exit /b 1
)

echo.
echo Testing file structure...

if exist "web\public\index.html" (
    echo [OK] Web interface files found
) else (
    echo [X] Web interface files missing
    exit /b 1
)

if exist "src\python\generate_video.py" (
    echo [OK] Python generator found
) else (
    echo [X] Python generator missing
    exit /b 1
)

echo.
echo All tests passed!
echo.
echo You can now:
echo   1. Run: scripts\Start Web Server.bat
echo   2. Open browser to: http://localhost:3000
echo.
pause
