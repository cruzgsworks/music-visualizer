# AI Cover Visualizer - Setup Script
# Run this PowerShell script to install dependencies and launch the visualizer

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "→ $Text" -ForegroundColor Yellow
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Magenta
}

# Get the directory where this script is located, then go to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Header "AI Cover Visualizer - Setup"

# Verify project structure
Write-Info "Verifying project structure..."
$RequiredFolders = @("input", "output", "src\python", "src\node", "web\public", "scripts")
$MissingFolders = @()

foreach ($folder in $RequiredFolders) {
    if (-not (Test-Path $folder)) {
        $MissingFolders += $folder
    }
}

if ($MissingFolders.Count -gt 0) {
    Write-Error "Missing folders: $($MissingFolders -join ', ')"
    Write-Host "Project structure appears incomplete. Please check your installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Success "Project structure verified"

# Check Python installation
Write-Info "Checking Python installation..."
try {
    $PythonVersion = python --version 2>&1
    Write-Success "Found $PythonVersion"
} catch {
    Write-Error "Python is not installed or not in PATH"
    Write-Host ""
    Write-Host "Please install Python from: https://python.org/downloads" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check pip
Write-Info "Checking pip..."
try {
    $PipVersion = pip --version 2>&1
    Write-Success "Found pip"
} catch {
    Write-Error "pip is not available"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Write-Error "requirements.txt not found in project root"
    Write-Host "Make sure you're running this script from the scripts folder!" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if already installed
Write-Info "Checking if Python dependencies are already installed..."
try {
    python -c "import librosa, numpy, PIL" 2>&1 | Out-Null
    Write-Success "Python dependencies already installed"
    $PythonDepsInstalled = $true
} catch {
    Write-Warning "Python dependencies not found, will install"
    $PythonDepsInstalled = $false
}

# Install Python dependencies if needed
if (-not $PythonDepsInstalled) {
    Write-Header "Installing Python Dependencies"
    Write-Info "This may take a few minutes..."
    Write-Host ""

    try {
        pip install -r requirements.txt
        Write-Success "All Python dependencies installed successfully!"
    } catch {
        Write-Error "Failed to install dependencies"
        Write-Host $_.Exception.Message -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Verify ffmpeg
Write-Info "Checking for ffmpeg..."
$FFmpegCheck = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($FFmpegCheck) {
    Write-Success "ffmpeg is installed"
} else {
    Write-Host ""
    Write-Warning "ffmpeg not found in PATH"
    Write-Host ""
    Write-Host "The visualizer requires ffmpeg to create videos." -ForegroundColor White
    Write-Host ""
    Write-Host "To install ffmpeg:" -ForegroundColor Cyan
    Write-Host "  1. Visit: https://ffmpeg.org/download.html#build-windows" -ForegroundColor White
    Write-Host "  2. Download the Windows build (e.g., from gyan.dev)" -ForegroundColor White
    Write-Host "  3. Extract and add the bin folder to your system PATH" -ForegroundColor White
    Write-Host "     OR use: choco install ffmpeg (if you have Chocolatey)" -ForegroundColor White
    Write-Host ""
    
    $Continue = Read-Host "Continue anyway? (Y/N)"
    if ($Continue -ne 'Y' -and $Continue -ne 'y') {
        exit 0
    }
}

Write-Header "Setup Complete!"
Write-Success "All dependencies are installed"
Write-Host ""

# Ask user what they want to launch
Write-Host "What would you like to launch?" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [1] Web Interface (Recommended) - Modern web UI with drag & drop"
Write-Host "  [2] Desktop GUI - Traditional desktop application"
Write-Host "  [3] Exit"
Write-Host ""

$Choice = Read-Host "Enter your choice (1-3)"

switch ($Choice) {
    "1" {
        Write-Info "Starting Web Interface..."
        Write-Host "The server will start and you can access it at http://localhost:3000" -ForegroundColor Yellow
        Write-Host ""
        
        # Change to node directory and start server
        Set-Location "$ProjectRoot\src\node"
        
        try {
            node server.js
        } catch {
            Write-Error "Failed to start web server"
            Write-Host $_.Exception.Message -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    "2" {
        Write-Info "Starting Desktop GUI..."
        
        try {
            python "$ProjectRoot\src\python\visualizer_gui.py"
        } catch {
            Write-Error "Failed to launch GUI"
            Write-Host $_.Exception.Message -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    default {
        Write-Host ""
        Write-Host "To launch later, run:" -ForegroundColor Cyan
        Write-Host "  Web Interface: scripts\Start Web Server.bat" -ForegroundColor White
        Write-Host "  Desktop GUI:   scripts\Launch Visualizer.bat" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
}
