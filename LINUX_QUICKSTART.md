# 🚀 Quick Start for Linux Homeserver

Moving your AI Cover Visualizer to a Linux homeserver with RTX 4070? Here's the fastest way:

## ⚡ One-Line Installer

```bash
# 1. Copy files to your Linux server (from Windows PowerShell)
scp -r C:\Users\jigsg\Documents\Suno\Riley user@your-linux-server:~/ai-cover-visualizer

# 2. SSH into your server
ssh user@your-linux-server

# 3. Run the installer
cd ~/ai-cover-visualizer
chmod +x install-linux.sh
./install-linux.sh
```

That's it! The installer will set up everything automatically.

## 🎮 Start the Server

```bash
# Start the server
./start-server.sh start

# Check status
./start-server.sh status

# View logs
./start-server.sh status
```

## 🌐 Access

Open your browser to:
- **Local**: `http://localhost:3000`
- **Network**: `http://your-server-ip:3000`

## 🚀 Using Your RTX 4070

1. Open web interface
2. Upload audio + image
3. Select **"NVIDIA GPU (GTX 10 series or newer)"**
4. Click **Generate Video**

Your RTX 4070 will encode the video **5-10x faster** than CPU!

## 📁 Files Included

- `LINUX_SETUP.md` - Complete detailed guide
- `install-linux.sh` - Automated installer
- `start-server.sh` - Server control script

## 🆘 Need Help?

See `LINUX_SETUP.md` for:
- Detailed setup instructions
- Troubleshooting
- Performance tuning
- Nginx reverse proxy setup
- Systemd service configuration

## ⚡ Performance

**RTX 4070 expected performance:**
- 3-minute song at 1080p30: **1-2 minutes** (vs 5-15 min CPU)
- GPU utilization: 30-60%
- Perfect for 24/7 homeserver operation

---

**Your visualizer is now ready for your Linux homeserver! 🎵🐧**
