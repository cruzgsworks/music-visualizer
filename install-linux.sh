#!/bin/bash
# AI Cover Visualizer - Automated Linux Installer
# This script installs everything needed to run the visualizer on Linux

set -e  # Exit on error

echo "=================================================="
echo "  AI Cover Visualizer - Linux Installer"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run as root (sudo). Run as your normal user."
    exit 1
fi

# Get app directory
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_DIR="$APP_DIR/src/node"

echo "Installing to: $APP_DIR"
echo ""

# Update system
echo "Step 1/7: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# Install basic dependencies
echo ""
echo "Step 2/7: Installing basic dependencies..."
sudo apt install -y build-essential curl wget git software-properties-common
print_success "Basic dependencies installed"

# Install Python
echo ""
echo "Step 3/7: Installing Python..."
if ! command -v python3 &> /dev/null; then
    sudo apt install -y python3 python3-pip python3-venv
fi
print_success "Python installed: $(python3 --version)"

# Install Node.js
echo ""
echo "Step 4/7: Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi
print_success "Node.js installed: $(node --version)"

# Install ffmpeg
echo ""
echo "Step 5/7: Installing ffmpeg..."
sudo apt install -y ffmpeg

# Check for GPU support
if ffmpeg -encoders 2>/dev/null | grep -q nvenc; then
    print_success "ffmpeg installed with NVIDIA NVENC support"
elif ffmpeg -encoders 2>/dev/null | grep -q amf; then
    print_success "ffmpeg installed with AMD AMF support"
else
    print_warning "ffmpeg installed but no GPU encoder found. Will use CPU encoding."
    print_warning "For GPU support, install NVIDIA or AMD drivers first."
fi

# Install Python dependencies
echo ""
echo "Step 6/7: Installing Python packages..."
cd "$APP_DIR"

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Created Python virtual environment"
fi

# Activate virtual environment and install packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

print_success "Python packages installed"

# Install Node.js dependencies
echo ""
echo "Step 7/7: Installing Node.js packages..."
cd "$NODE_DIR"
if [ ! -d "node_modules" ]; then
    npm install
fi
print_success "Node.js packages installed"

# Create required directories
echo ""
echo "Creating directories..."
cd "$APP_DIR"
mkdir -p uploads output temp
chmod 755 uploads output temp
print_success "Directories created"

# Make scripts executable
chmod +x "$APP_DIR/start-server.sh"

# Check for NVIDIA GPU
echo ""
echo "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | while read line; do
        echo "  - $line"
    done
    echo ""
    echo "💡 You can use GPU acceleration by selecting 'NVIDIA GPU' in the web interface"
else
    print_warning "No NVIDIA GPU detected. Will use CPU encoding."
    echo "   To use GPU acceleration, install NVIDIA drivers:"
    echo "   sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit"
    echo "   Then reboot your system."
fi

echo ""
echo "=================================================="
echo "  Installation Complete!"
echo "=================================================="
echo ""
echo "📁 Installation directory: $APP_DIR"
echo ""
echo "🚀 To start the server, run:"
echo "   cd $APP_DIR"
echo "   ./start-server.sh start"
echo ""
echo "🌐 Then open your browser to:"
echo "   http://localhost:3000"
echo ""
echo "📖 For more information, see: LINUX_SETUP.md"
echo ""
echo "🎵 Happy visualizing!"
