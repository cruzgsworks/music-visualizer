# AI Cover Visualizer

Create stunning music visualizer videos from audio files and center images. Now with a modern web interface!

## 📁 Project Structure

```
📁 ai-cover-visualizer/
├── 📁 input/                   ⬅️ Put your audio/image files here
├── 📁 output/                  ⬅️ Generated videos saved here
├── 📁 scripts/                 ⬅️ Launch scripts (double-click these!)
│   ├── Start Web Server.bat    ⭐ Start the web interface
│   ├── Launch Visualizer.bat   🖥️ Launch desktop GUI
│   └── Setup.ps1               🔧 Setup script
├── 📁 src/
│   ├── 📁 python/              🐍 Python scripts
│   │   ├── generate_video.py   (Video generator - used by web)
│   │   ├── visualizer_gui.py   (Desktop GUI)
│   │   ├── create_visualizer.py (CLI version)
│   │   └── test_button.py      (Test script)
│   └── 📁 node/                🟢 Node.js backend
│       ├── server.js           (Web server)
│       └── package.json        (Dependencies)
├── 📁 web/
│   └── 📁 public/              🌐 Web interface files
│       ├── index.html          (Main page)
│       ├── 📁 css/
│       │   └── style.css       (Styles)
│       └── 📁 js/
│           └── app.js          (JavaScript)
├── 📄 requirements.txt         Python dependencies
├── 📄 package.json             (in src/node)
└── 📄 README.md                This file
```

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

**Easiest way:**
1. Install [Node.js](https://nodejs.org) (if not installed)
2. **Double-click** `scripts/Start Web Server.bat`
3. Open browser to **http://localhost:3000**
4. Upload your audio and image files
5. Click **Generate Video**

### Option 2: Desktop GUI

**Double-click** `scripts/Launch Visualizer.bat`

### Option 3: Command Line

```bash
cd src/python
python generate_video.py --audio "../../input/song.mp3" --image "../../input/cover.png" --output "../../output/video.mp4" --job-id "my-job"
```

## ✨ Features

- 🎵 Audio-reactive visualizer bars
- 🖼️ Circular center image with glow effect
- 📐 Multiple presets (YouTube, TikTok, Instagram, 4K)
- 🌐 Modern web interface with drag & drop
- 📊 Real-time progress tracking
- 🎨 Customizable settings

## 📋 Requirements

- **Node.js** v14+ (for web interface)
- **Python** 3.8+ (for video generation)
- **ffmpeg** (for video encoding)
  - Windows: `choco install ffmpeg`
  - Download: https://ffmpeg.org/download.html

## 📦 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- librosa (audio analysis)
- numpy (computations)
- Pillow (image processing)
- soundfile, audioread (audio support)

### 2. Install Node.js Dependencies

```bash
cd src/node
npm install
```

## 🎯 Usage Guide

### Web Interface

1. **Upload Files:**
   - Drag & drop or click to browse
   - Audio: MP3, WAV, FLAC, M4A, AAC
   - Image: PNG, JPG, JPEG, GIF, BMP, WEBP

2. **Select Preset:**
   - **YouTube:** 1920×1080 (16:9)
   - **TikTok:** 1080×1920 (9:16)
   - **Instagram:** 1080×1080 (1:1)

3. **Customize (Optional):**
   - Resolution: 4K, 1080p, 720p, or custom
   - Frame Rate: 15-60 FPS
   - Visualizer Bars: 32-128 bars
   - Glow Intensity: 0-100%

4. **Generate:**
   - Click "Generate Video"
   - Watch real-time progress
   - Download when complete!

### Settings Explained

| Setting | Description | Default |
|---------|-------------|---------|
| **Resolution** | Output video dimensions | 1920×1080 |
| **Frame Rate** | Frames per second (higher = smoother) | 30 |
| **Visualizer Bars** | Number of frequency bars | 64 |
| **Glow Intensity** | Brightness of image glow | 50% |

## 🎬 How It Works

1. **Upload** your audio and image via the web interface
2. **Server** receives files and validates them
3. **Python** analyzes audio frequencies using librosa
4. **Frames** are generated with reactive visualizer bars
5. **FFmpeg** combines frames and audio into MP4
6. **Download** your finished video!

## 🐛 Troubleshooting

### "Cannot find module"
```bash
cd src/node
npm install
```

### "Python not found"
- Install Python from https://python.org
- Check "Add Python to PATH" during installation

### "ffmpeg not found"
- Install ffmpeg: `choco install ffmpeg`
- Or download from https://ffmpeg.org/download.html

### "Port 3000 already in use"
Edit `src/node/server.js` and change: `const PORT = process.env.PORT || 3000;`

### Slow rendering
- Video generation is CPU-intensive
- 3-minute song takes 5-15 minutes depending on:
  - Resolution (4K takes longer than 1080p)
  - Frame rate (60fps takes longer than 30fps)
  - Your CPU speed

## 📂 File Locations

- **Input files:** Place audio/images in `input/`
- **Output videos:** Generated videos saved to `output/`
- **Temporary files:** Auto-cleaned after generation

## 📝 Command Line Options

```bash
python src/python/generate_video.py \
  --audio "input/song.mp3" \
  --image "input/cover.png" \
  --output "output/video.mp4" \
  --resolution "1920x1080" \
  --fps 30 \
  --bars 64 \
  --glow 50 \
  --job-id "unique-id"
```

## 🛠️ Development

### Project Architecture

```
Frontend (Browser)
    ↓ HTTP/WebSocket
Web Server (Node.js/Express)
    ↓ Spawn Process
Video Generator (Python)
    ↓ FFmpeg
Output Video (MP4)
```

### Adding Features

- **Frontend:** Edit `web/public/` files
- **Backend:** Edit `src/node/server.js`
- **Video Logic:** Edit `src/python/generate_video.py`

## 📄 License

MIT License - Feel free to use and modify!

---

**Created with ❤️ for AI music covers**

Need help? Check the docs or create an issue!
