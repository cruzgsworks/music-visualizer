const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const WebSocket = require('ws');
const http = require('http');
const { v4: uuidv4 } = require('uuid');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Get project root (parent of src directory)
const projectRoot = path.join(__dirname, '..', '..');

// Middleware - serve static files from web/public with cache control
app.use(express.static(path.join(projectRoot, 'web', 'public'), {
    maxAge: '1h',
    setHeaders: (res, path) => {
        if (path.endsWith('.css') || path.endsWith('.js')) {
            res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
            res.setHeader('Pragma', 'no-cache');
            res.setHeader('Expires', '0');
        }
    }
}));
app.use(express.json());

// Ensure directories exist
const uploadsDir = path.join(projectRoot, 'uploads');
const outputsDir = path.join(projectRoot, 'output');
const tempDir = path.join(projectRoot, 'temp');

[uploadsDir, outputsDir, tempDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// Multer configuration for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadsDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = uuidv4() + path.extname(file.originalname);
        cb(null, uniqueSuffix);
    }
});

const upload = multer({ 
    storage: storage,
    limits: { fileSize: 100 * 1024 * 1024 }, // 100MB limit
    fileFilter: (req, file, cb) => {
        if (file.fieldname === 'audio') {
            const allowedTypes = ['.mp3', '.wav', '.flac', '.m4a', '.aac'];
            const ext = path.extname(file.originalname).toLowerCase();
            if (allowedTypes.includes(ext)) {
                cb(null, true);
            } else {
                cb(new Error('Invalid audio file type'));
            }
        } else if (file.fieldname === 'image') {
            const allowedTypes = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'];
            const ext = path.extname(file.originalname).toLowerCase();
            if (allowedTypes.includes(ext)) {
                cb(null, true);
            } else {
                cb(new Error('Invalid image file type'));
            }
        } else {
            cb(null, true);
        }
    }
});

// Store active jobs
const activeJobs = new Map();

// WebSocket handling
wss.on('connection', (ws) => {
    console.log('Client connected');
    
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Broadcast progress to all connected clients
function broadcastProgress(jobId, data) {
    const message = JSON.stringify({ jobId, ...data });
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// API Routes

// Upload endpoint
app.post('/api/upload', upload.fields([
    { name: 'audio', maxCount: 1 },
    { name: 'image', maxCount: 1 }
]), (req, res) => {
    try {
        if (!req.files || !req.files.audio || !req.files.image) {
            return res.status(400).json({ error: 'Both audio and image files are required' });
        }

        const jobId = uuidv4();
        const audioFile = req.files.audio[0];
        const imageFile = req.files.image[0];

        res.json({
            success: true,
            jobId: jobId,
            audio: {
                filename: audioFile.filename,
                originalname: audioFile.originalname,
                size: audioFile.size
            },
            image: {
                filename: imageFile.filename,
                originalname: imageFile.originalname,
                size: imageFile.size
            }
        });
    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Generate video endpoint
app.post('/api/generate', async (req, res) => {
    const { jobId, audioFilename, imageFilename, settings } = req.body;

    if (!jobId || !audioFilename || !imageFilename) {
        return res.status(400).json({ error: 'Missing required parameters' });
    }

    const audioPath = path.join(uploadsDir, audioFilename);
    const imagePath = path.join(uploadsDir, imageFilename);
    const outputFilename = `output_${jobId}.mp4`;
    const outputPath = path.join(outputsDir, outputFilename);

    // Check files exist
    if (!fs.existsSync(audioPath) || !fs.existsSync(imagePath)) {
        return res.status(404).json({ error: 'Upload files not found' });
    }

    // Start generation process
    res.json({ success: true, jobId, message: 'Generation started' });

    // Spawn Python process
    const pythonScript = path.join(projectRoot, 'src', 'python', 'generate_video.py');
    const args = [
        pythonScript,
        '--audio', audioPath,
        '--image', imagePath,
        '--output', outputPath,
        '--resolution', settings.resolution || '1920x1080',
        '--fps', String(settings.fps || 30),
        '--bars', String(settings.barCount || 64),
        '--glow', String(settings.glowIntensity || 50),
        '--bar-sensitivity', String(settings.barSensitivity || 60),
        '--gpu-mode', settings.gpuMode || 'cpu',
        '--job-id', jobId
    ];

    console.log('Starting Python process:', 'python', args.join(' '));

    const pythonProcess = spawn('python', args, {
        cwd: __dirname,
        stdio: ['ignore', 'pipe', 'pipe']
    });

    activeJobs.set(jobId, { process: pythonProcess, outputPath });

    // Handle Python output
    pythonProcess.stdout.on('data', (data) => {
        const lines = data.toString().split('\n').filter(line => line.trim());
        lines.forEach(line => {
            try {
                const progress = JSON.parse(line);
                broadcastProgress(jobId, progress);
            } catch (e) {
                console.log('Python output:', line);
                broadcastProgress(jobId, { type: 'log', message: line });
            }
        });
    });

    pythonProcess.stderr.on('data', (data) => {
        const message = data.toString().trim();
        console.error('Python stderr:', message);
        broadcastProgress(jobId, { type: 'error', message: message });
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        activeJobs.delete(jobId);

        if (code === 0 && fs.existsSync(outputPath)) {
            broadcastProgress(jobId, {
                type: 'complete',
                success: true,
                downloadUrl: `api/download/${jobId}`,
                filename: outputFilename
            });
        } else {
            broadcastProgress(jobId, {
                type: 'complete',
                success: false,
                error: code === null ? 'Process was terminated' : `Process exited with code ${code}`
            });
        }

        // Cleanup uploaded files after a delay
        setTimeout(() => {
            try {
                if (fs.existsSync(audioPath)) fs.unlinkSync(audioPath);
                if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
                console.log(`Cleaned up upload files for job ${jobId}`);
            } catch (err) {
                console.error('Cleanup error:', err);
            }
        }, 60000); // Clean up after 1 minute
    });
});

// Cancel job endpoint
app.post('/api/cancel/:jobId', (req, res) => {
    const { jobId } = req.params;
    const job = activeJobs.get(jobId);

    if (job) {
        job.process.kill();
        activeJobs.delete(jobId);
        broadcastProgress(jobId, { type: 'cancelled' });
        res.json({ success: true, message: 'Job cancelled' });
    } else {
        res.status(404).json({ error: 'Job not found or already completed' });
    }
});

// Download endpoint
app.get('/api/download/:jobId', (req, res) => {
    const { jobId } = req.params;
    const filename = `output_${jobId}.mp4`;
    const filePath = path.join(outputsDir, filename);

    if (fs.existsSync(filePath)) {
        res.download(filePath, `visualizer_${jobId}.mp4`, (err) => {
            if (err) {
                console.error('Download error:', err);
                if (!res.headersSent) {
                    res.status(500).json({ error: 'Download failed' });
                }
            }
        });
    } else {
        res.status(404).json({ error: 'File not found' });
    }
});

// Status endpoint
app.get('/api/status/:jobId', (req, res) => {
    const { jobId } = req.params;
    const filename = `output_${jobId}.mp4`;
    const filePath = path.join(outputsDir, filename);

    if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        res.json({
            exists: true,
            size: stats.size,
            downloadUrl: `api/download/${jobId}`,
            filename: filename
        });
    } else {
        res.json({ exists: false });
    }
});

// Clean up old output files periodically (every hour)
setInterval(() => {
    const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
    
    fs.readdir(outputsDir, (err, files) => {
        if (err) return;
        
        files.forEach(file => {
            const filePath = path.join(outputsDir, file);
            fs.stat(filePath, (err, stats) => {
                if (err) return;
                
                if (stats.mtime.getTime() < oneDayAgo) {
                    fs.unlink(filePath, (err) => {
                        if (err) {
                            console.error('Failed to delete old file:', err);
                        } else {
                            console.log('Deleted old output file:', file);
                        }
                    });
                }
            });
        });
    });
}, 60 * 60 * 1000);

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Express error:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`🎵 AI Cover Visualizer Server running on http://localhost:${PORT}`);
    console.log('');
    console.log('Open your browser and navigate to the URL above');
});
