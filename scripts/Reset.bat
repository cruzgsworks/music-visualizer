@echo off
echo ========================================
echo   AI Cover Visualizer - Reset/Cleanup
echo ========================================
echo.
echo This will clean up temporary files and reset the project.
echo.
echo The following will be deleted:
echo   - temp/ folder (temporary files)
echo   - uploads/ folder (uploaded files)
echo   - src/node/node_modules/ (Node dependencies)
echo   - src/python/__pycache__/ (Python cache)
echo.
echo Your input/ and output/ folders will NOT be touched.
echo.
pause

cd /d "%~dp0\.."

echo.
echo Cleaning up...

if exist "temp\" (
    rmdir /s /q "temp"
    echo [OK] Removed temp/ folder
)

if exist "uploads\" (
    rmdir /s /q "uploads"
    echo [OK] Removed uploads/ folder
)

if exist "src\node\node_modules\" (
    rmdir /s /q "src\node\node_modules"
    echo [OK] Removed node_modules/
)

if exist "src\python\__pycache__\" (
    rmdir /s /q "src\python\__pycache__"
    echo [OK] Removed __pycache__/
)

echo.
echo Cleanup complete!
echo.
echo To reinstall dependencies, run: scripts\Setup.ps1
echo.
pause
