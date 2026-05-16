# AI Cover Visualizer

Create stunning audio-reactive music visualizer videos. Deployed at **cruzgsworks.space/music-visualizer**.

## Tech Stack

```
Frontend (Browser)              HTML + CSS + JavaScript + jQuery
        ↓ HTTP / WebSocket
Web Server (Node.js)            Express + ws (port 3000)
        ↓ spawn + stdout JSON
Video Generator (Python)        librosa + numpy + Pillow
        ↓ raw RGB24 pipe
Video Encoder (ffmpeg)          h264_nvenc / libx264 + AAC
        ↓
Output Video (MP4)
```

## Architecture

| Layer             | Technology                          | Role                                                                           |
|-------------------|-------------------------------------|--------------------------------------------------------------------------------|
| **Frontend**      | HTML/CSS/JS + Bootstrap 5 + jQuery  | Upload UI, settings panel, real-time progress bar, recent downloads            |
| **Server**        | Node.js + Express + ws              | File upload, job orchestration, WebSocket broadcast, download serve            |
| **Rendering**     | Python 3 + librosa + numpy + Pillow | Audio analysis (STFT), frame generation (bar rendering, compositing)           |
| **Encoding**      | ffmpeg (NVENC/AMF/libx264)          | Raw frame pipe to compressed MP4 with audio muxing                             |
| **Reverse proxy** | Apache 2.4                          | HTTPS termination, path-based routing (`/music-visualizer`), WebSocket upgrade |
| **OS**            | Ubuntu 24.04 + systemd              | Service management, auto-start                                                 |

## Hardware

- **CPU:** AMD Ryzen 7 8845HS (8C/16T)
- **GPU:** NVIDIA GeForce RTX 4070 Laptop (8GB VRAM)
- **RAM:** 32GB

## Features

### Current
- **Teal/cyan glassmorphism UI** matching cruzgsworks.space/vocal-ref theme
- **Real-time WebSocket progress** — frame-by-frame progress bar with smooth shimmer animation
- **Two visualizer styles:**
  - **Circular Orb** — radial bars around centre image with 2x supersampled anti-aliasing
  - **Horizontal Mirrored Bars** — mirrored left/right bars with rounded-square centre image
- **Recent Downloads panel** — persisted in localStorage across page refreshes
- **Smart filename** — `{sanitized_songname}_{jobId}.mp4` with filesystem-safe sanitization
- **Persistent filename mapping** — `_mapping.json` survives server restarts; legacy `output_{jobId}.mp4` fallback
- **GPU auto-detect** — tries NVENC, then AMF, falls back to libx264
- **Presets:** YouTube (1920x1080), TikTok (1080x1920), Instagram (1080x1080)
- **Customizable:** resolution, FPS (15-60), bar count (32-128), glow intensity, bar sensitivity, GPU mode
- **Two file upload** (audio + image) with drag-and-drop
- **Systemd service** with auto-restart on crash/boot
- **Apache reverse proxy** with WebSocket upgrade support

## Optimization Progress

| Phase | Change                                                            | Status     | Speedup         |
|-------|-------------------------------------------------------------------|------------|-----------------|
| —     | Original: PNG frames to disk, per-frame FFT, PIL bars, CPU encode | Baseline   | 1x              |
| P1    | Raw RGB24 pipe to ffmpeg stdin (no disk I/O)                      | ✅ Deployed | **~3-5x**       |
| P1    | Pre-rendered background (once per job, not per frame)             | ✅ Deployed | **~1.3x**       |
| P1    | Batch STFT via librosa (vs per-frame FFT)                         | ✅ Deployed | **~5x** audio   |
| P1    | Numpy slice bars (horizontal style)                               | ✅ Deployed | **~2-5x**       |
| P1    | Auto GPU detect + NVENC `p4` preset                               | ✅ Deployed | **~10x** encode |
| P2    | Multiprocessing frame pool                                        | ⏳ Planned  | **~6-8x**       |
| P2    | Threaded ffmpeg pipe (producer-consumer)                          | ⏳ Planned  | **~1.5-2x**     |
| P3    | ModernGL + GLSL shader rendering                                  | 🔮 Future  | **~10-20x**     |

**Estimated current speedup: 10-30x** over original (3-min 1080p video: ~15 min to ~30-90 s)

## API Endpoints

| Method | Path                   | Purpose                                 |
|--------|------------------------|-----------------------------------------|
| `POST` | `/api/upload`          | Upload audio + image files (multipart)  |
| `POST` | `/api/generate`        | Start video generation (returns job ID) |
| `POST` | `/api/cancel/:jobId`   | Cancel running job                      |
| `GET`  | `/api/download/:jobId` | Download completed video                |
| `GET`  | `/api/status/:jobId`   | Check if output file exists             |
| `WS`   | `/api/ws`              | WebSocket — real-time progress events   |

### WebSocket Events

```json
{"type": "log",       "jobId": "...", "message": "..."}
{"type": "progress",  "jobId": "...", "value": 45.2, "message": "Frame 900/1836"}
{"type": "complete",  "jobId": "...", "success": true,
                      "downloadUrl": "api/download/...", "filename": "song_....mp4"}
{"type": "complete",  "jobId": "...", "success": false, "error": "..."}
{"type": "cancelled", "jobId": "..."}
```

## Deployment

### Dependencies
```bash
cd /path/to/music-visualizer

# Node.js
cd src/node && npm install

# Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ffmpeg (with NVENC support for NVIDIA GPUs)
sudo apt install ffmpeg
```

### systemd Service
```bash
sudo cp music-visualizer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now music-visualizer.service
```

### Apache Reverse Proxy
```apache
ProxyPass /music-visualizer http://127.0.0.1:3000
ProxyPassReverse /music-visualizer http://127.0.0.1:3000

RewriteCond %{HTTP:Upgrade} =websocket [NC]
RewriteRule ^/music-visualitor(/.*)?$ ws://127.0.0.1:3000$1 [P,L]
```

## File Layout

```
music-visualizer/
├── src/
│   ├── node/
│   │   ├── server.js          Express + WebSocket + job orchestration
│   │   └── package.json
│   └── python/
│       └── generate_video.py  Frame rendering + ffmpeg pipe
├── web/public/
│   ├── index.html             UI
│   ├── css/style.css          Teal/cyan glassmorphism theme
│   └── js/app.js              Client logic + WebSocket + localStorage
├── uploads/                   Uploaded audio/image files (auto-cleaned)
├── output/                    Generated MP4 files
│   └── _mapping.json          jobId to filename persistence
├── apache-proxy.conf          Apache proxy template
├── music-visualizer.service   systemd unit template
├── requirements.txt
└── README.md
```

## CLI Usage (standalone, no web server needed)

```bash
cd src/python
source ../venv/bin/activate

python generate_video.py \
  --audio "input/song.mp3" \
  --image "input/cover.png" \
  --output "output/video.mp4" \
  --resolution "1920x1080" \
  --fps 30 \
  --bars 64 \
  --glow 50 \
  --bar-sensitivity 60 \
  --gpu-mode auto \
  --style circular \
  --job-id "my-job"
```

## Roadmap

### Phase 2 — Parallelism
- [ ] `multiprocessing.Pool` for parallel frame rendering (6-8x speedup)
- [ ] Threaded ffmpeg pipe with producer-consumer queue (1.5-2x)
- [ ] Benchmark to confirm bottleneck

### Phase 3 — GPU Rendering (if needed)
- [ ] ModernGL offscreen FBO + GLSL fragment shaders
- [ ] Upload FFT data as GPU uniforms
- [ ] Single draw call renders entire frame on GPU

### Polish
- [ ] Progress ETA estimate
- [ ] Keyboard shortcuts
- [ ] Drag-and-drop recent downloads reordering

## License

MIT
