# AI Cover Visualizer - Linux Setup Guide

Complete setup guide for running the AI Cover Visualizer on a Linux homeserver with NVIDIA GPU support.

## 🖥️ System Requirements

### Hardware
- **CPU**: Any modern x86_64 processor
- **RAM**: 4GB minimum (8GB recommended)
- **GPU**: NVIDIA RTX 4070 (or any NVIDIA GPU with NVENC support)
- **Storage**: 10GB free space for dependencies and temp files

### Operating System
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / Any modern Linux distro
- 64-bit architecture (x86_64)

## 📦 Dependencies Installation

### 1. Install System Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential curl wget git

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js (v18 LTS)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
python3 --version  # Should be 3.8+
node --version     # Should be v18+
npm --version
```

### 2. Install FFmpeg with NVIDIA Support

```bash
# Install ffmpeg
sudo apt install -y ffmpeg

# Verify ffmpeg has NVIDIA support
ffmpeg -encoders 2>/dev/null | grep nvenc

# You should see: V..... h264_nvenc NVIDIA NVENC H.264 encoder
```

### 3. Install NVIDIA GPU Drivers (RTX 4070)

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install NVIDIA driver
sudo apt update
sudo apt install -y nvidia-driver-535  # Or latest version

# Install CUDA toolkit (required for NVENC)
sudo apt install -y nvidia-cuda-toolkit

# Reboot to load drivers
sudo reboot
```

After reboot, verify GPU is detected:
```bash
nvidia-smi
```

You should see your RTX 4070 listed with driver version.

## 🎵 Application Setup

### 1. Clone/Copy the Application

```bash
# Create application directory
mkdir -p ~/apps
cd ~/apps

# Copy the visualizer files (from your Windows machine or git)
# Option A: If using git
git clone <your-repo-url> ai-cover-visualizer

# Option B: Copy from Windows via SCP
# From Windows PowerShell:
# scp -r C:\Users\jigsg\Documents\Suno\Riley user@your-linux-server:~/apps/ai-cover-visualizer

# Option C: Copy via rsync
# rsync -avz /path/to/Riley user@server:~/apps/ai-cover-visualizer

cd ai-cover-visualizer
```

### 2. Install Python Dependencies

```bash
# Install Python packages
pip3 install -r requirements.txt

# If you get permission errors, use --user flag
pip3 install --user -r requirements.txt

# Or create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Required Python packages (from requirements.txt):
- librosa>=0.10.0
- numpy>=1.24.0
- Pillow>=10.0.0
- soundfile>=0.12.0
- audioread>=3.0.0

### 3. Install Node.js Dependencies

```bash
cd src/node

# Install dependencies
npm install

# This creates node_modules/ directory
cd ../..
```

## 🔧 Configuration

### 1. Create Required Directories

```bash
# Create folders for uploads and outputs
mkdir -p uploads output temp

# Set proper permissions
chmod 755 uploads output temp
```

### 2. Configure Firewall (if enabled)

```bash
# Allow port 3000 (web server)
sudo ufw allow 3000/tcp

# Or if using firewalld
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

### 3. Create Systemd Service (Optional but Recommended)

Create a service file to auto-start on boot:

```bash
sudo tee /etc/systemd/system/visualizer.service > /dev/null <<EOF
[Unit]
Description=AI Cover Visualizer Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/apps/ai-cover-visualizer/src/node
Environment=PATH=/usr/bin:/usr/local/bin
Environment=NODE_ENV=production
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable visualizer

# Start the service
sudo systemctl start visualizer

# Check status
sudo systemctl status visualizer
```

## 🚀 Running the Application

### Option 1: Manual Start (Development)

```bash
cd ~/apps/ai-cover-visualizer/src/node

# Start the server
node server.js

# Server will run on http://localhost:3000
```

### Option 2: Using PM2 (Production)

PM2 is a process manager for Node.js:

```bash
# Install PM2 globally
sudo npm install -g pm2

# Start with PM2
cd ~/apps/ai-cover-visualizer/src/node
pm2 start server.js --name visualizer

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup systemd

# Follow the instructions PM2 gives you (usually involves running a sudo command)
```

### Option 3: Using Screen/Tmux

```bash
# Install screen
sudo apt install -y screen

# Create new session
screen -S visualizer

# Start server
cd ~/apps/ai-cover-visualizer/src/node
node server.js

# Detach: Press Ctrl+A then D
# Reattach: screen -r visualizer
```

## 🌐 Accessing the Web Interface

### Local Access
```
http://localhost:3000
```

### Remote Access (from another device)

Find your server IP:
```bash
ip addr show | grep "inet " | head -1
```

Access via:
```
http://YOUR-SERVER-IP:3000
```

### Using Nginx Reverse Proxy (Recommended for external access)

```bash
# Install nginx
sudo apt install -y nginx

# Create nginx config
sudo tee /etc/nginx/sites-available/visualizer > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Or your server IP

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/visualizer /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default if exists

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

Now access via: `http://your-domain.com` or `http://YOUR-SERVER-IP`

## 🎮 Using NVIDIA GPU (RTX 4070)

### Verify GPU Encoding Works

```bash
# Check NVENC is available
ffmpeg -encoders 2>/dev/null | grep nvenc

# Expected output:
# V..... h264_nvenc NVIDIA NVENC H.264 encoder
```

### In the Web Interface

1. Open the web interface
2. Upload audio and image files
3. In **"Processing Mode"** dropdown, select:
   **"NVIDIA GPU (GTX 10 series or newer) - NVENC Hardware Encoder"**
4. Click **"Generate Video"**

### Performance Expectations (RTX 4070)

- **3-minute song at 1080p30**: ~1-2 minutes (vs 5-15 min on CPU)
- **GPU Utilization**: 30-60% during encoding
- **Quality**: Same as CPU mode, just faster!

## 📝 File Locations

```
~/apps/ai-cover-visualizer/
├── input/                    # Put your audio/images here
├── output/                   # Generated videos appear here
├── uploads/                  # Temporary upload storage
├── temp/                     # Temporary processing files
├── src/
│   ├── node/                # Node.js backend
│   │   ├── server.js
│   │   └── package.json
│   └── python/              # Python video generator
│       └── generate_video.py
├── web/public/              # Web frontend
│   ├── index.html
│   ├── css/
│   └── js/
└── scripts/                 # Helper scripts (Linux versions)
```

## 🔧 Troubleshooting

### Issue: "nvidia-smi not found"
**Solution**: NVIDIA drivers not installed properly
```bash
# Reinstall drivers
sudo apt purge nvidia-*
sudo apt install -y nvidia-driver-535
sudo reboot
```

### Issue: "ffmpeg h264_nvenc not found"
**Solution**: FFmpeg compiled without NVENC support
```bash
# Install ffmpeg from NVIDIA repository
sudo apt install -y ffmpeg-nvidia

# Or compile ffmpeg with NVENC (advanced)
```

### Issue: "Permission denied" on upload
**Solution**: Fix folder permissions
```bash
chmod -R 755 ~/apps/ai-cover-visualizer/{uploads,output,temp}
```

### Issue: "Cannot find module"
**Solution**: Reinstall Node.js dependencies
```bash
cd ~/apps/ai-cover-visualizer/src/node
rm -rf node_modules
npm install
```

### Issue: Server not accessible remotely
**Solution**: Check firewall
```bash
# Check if port is open
sudo ufw status
# or
sudo firewall-cmd --list-ports

# Allow port 3000
sudo ufw allow 3000/tcp
```

## 🔄 Updating the Application

```bash
cd ~/apps/ai-cover-visualizer

# Pull latest changes (if using git)
git pull

# Or copy new files from Windows

# Update Python dependencies
pip3 install -r requirements.txt

# Update Node.js dependencies
cd src/node
npm install
cd ../..

# Restart service
sudo systemctl restart visualizer
# or
pm2 restart visualizer
```

## 📊 Monitoring

### Check GPU Usage
```bash
watch -n 1 nvidia-smi
```

### Check Server Logs
```bash
# If using systemd
sudo journalctl -u visualizer -f

# If using PM2
pm2 logs visualizer

# Manual mode
cd ~/apps/ai-cover-visualizer/src/node
node server.js 2>&1 | tee server.log
```

### Check Disk Space
```bash
df -h ~/apps/ai-cover-visualizer
du -sh ~/apps/ai-cover-visualizer/output
```

## 🎵 Quick Start Commands

```bash
# 1. Navigate to app
cd ~/apps/ai-cover-visualizer

# 2. Start server (choose one method)
# Method A: Direct
node src/node/server.js

# Method B: PM2
pm2 start src/node/server.js --name visualizer

# Method C: Systemd
sudo systemctl start visualizer

# 3. Open browser to http://your-server-ip:3000

# 4. Upload files and select "NVIDIA GPU" mode

# 5. Generate video!
```

## 🆘 Getting Help

If you encounter issues:

1. Check server logs
2. Verify GPU: `nvidia-smi`
3. Verify ffmpeg: `ffmpeg -encoders | grep nvenc`
4. Check file permissions: `ls -la uploads/ output/ temp/`
5. Restart server and try again

## 📄 License

This application is provided as-is for personal use on your homeserver.

---

**Your RTX 4070 should provide excellent performance for video generation! Enjoy your AI Cover Visualizer! 🎵🚀**
