@echo off
echo ========================================
echo   AI Cover Visualizer - Setup Check
echo ========================================
echo.

cd /d "%~dp0\.."

echo Checking project structure...
echo.

set "errors=0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found
    set /a errors+=1
) else (
    for /f "tokens=*" %%a in ('python --version 2^>^&1') do echo [OK] %%a
)

echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [X] Node.js not found
    set /a errors+=1
) else (
    for /f "tokens=*" %%a in ('node --version') do echo [OK] Node.js %%a
)

echo.

REM Check ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [X] ffmpeg not found
    set /a errors+=1
) else (
    echo [OK] ffmpeg is installed
)

echo.

REM Check folders
echo Checking folders...
if exist "input\" (
    echo [OK] input/ folder exists
) else (
    echo [X] input/ folder missing
    set /a errors+=1
)

if exist "output\" (
    echo [OK] output/ folder exists
) else (
    echo [X] output/ folder missing
    set /a errors+=1
)

if exist "src\python\" (
    echo [OK] src/python/ folder exists
) else (
    echo [X] src/python/ folder missing
    set /a errors+=1
)

if exist "src\node\" (
    echo [OK] src/node/ folder exists
) else (
    echo [X] src/node/ folder missing
    set /a errors+=1
)

if exist "web\public\" (
    echo [OK] web/public/ folder exists
) else (
    echo [X] web/public/ folder missing
    set /a errors+=1
)

echo.

REM Check key files
echo Checking key files...
if exist "requirements.txt" (
    echo [OK] requirements.txt exists
) else (
    echo [X] requirements.txt missing
    set /a errors+=1
)

if exist "src\node\package.json" (
    echo [OK] package.json exists
) else (
    echo [X] package.json missing
    set /a errors+=1
)

if exist "src\node\server.js" (
    echo [OK] server.js exists
) else (
    echo [X] server.js missing
    set /a errors+=1
)

if exist "src\python\generate_video.py" (
    echo [OK] generate_video.py exists
) else (
    echo [X] generate_video.py missing
    set /a errors+=1
)

if exist "web\public\index.html" (
    echo [OK] index.html exists
) else (
    echo [X] index.html missing
    set /a errors+=1
)

if exist "web\public\css\style.css" (
    echo [OK] style.css exists
) else (
    echo [X] style.css missing
    set /a errors+=1
)

if exist "web\public\js\app.js" (
    echo [OK] app.js exists
) else (
    echo [X] app.js missing
    set /a errors+=1
)

echo.
echo ========================================

if %errors%==0 (
    echo All checks passed! Project is ready.
    echo.
    echo To start:
    echo   - Web Interface: Run Start Web Server.bat
    echo   - Desktop GUI: Run Launch Visualizer.bat
) else (
    echo Found %errors% error(s). Please fix the issues above.
)

echo.
pause
