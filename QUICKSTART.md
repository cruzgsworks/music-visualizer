# 🚀 Quick Start Guide

## First Time Setup

### 1. Install Dependencies

**Python (required for video generation):**
```bash
pip install -r requirements.txt
```

**Node.js (required for web interface):**
```bash
cd src/node
npm install
```

### 2. Install ffmpeg

**Windows (with Chocolatey):**
```bash
choco install ffmpeg
```

**Or download from:** https://ffmpeg.org/download.html

## Using the Visualizer

### 🌐 Web Interface (Recommended)

1. **Double-click:** `scripts/Start-Web-Server.bat`
2. **Open browser:** http://localhost:3000
3. **Upload files:**
   - Audio: Drag & drop your MP3 to the audio zone
   - Image: Drag & drop your cover image
4. **Select preset:** Click YouTube, TikTok, or Instagram
5. **Click:** "Generate Video"
6. **Download** when complete!

### 🖥️ Desktop GUI

1. **Double-click:** `scripts/Launch-Visualizer.bat`
2. Use the file browser to select audio and image
3. Click "Generate Video"

### 💻 Command Line

```bash
cd src/python
python generate_video.py \
  --audio "../../input/Riley (AI Cover).mp3" \
  --image "../../input/center_image.png" \
  --output "../../output/Riley_Visualizer.mp4" \
  --resolution "1920x1080" \
  --fps 30 \
  --bars 64 \
  --glow 50 \
  --job-id "riley-job"
```

## File Locations

- **Put your files here:** `input/`
- **Get your videos here:** `output/`
- **Run from here:** `scripts/`

## Need Help?

See `README.md` for full documentation!
