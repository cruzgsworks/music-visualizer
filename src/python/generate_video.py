#!/usr/bin/env python3
"""
Video Generator - CLI version for Node.js backend
Optimized: raw ffmpeg pipe, pre-rendered backgrounds, batch STFT, numpy bars
"""

import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import librosa
import subprocess
import os
import sys
import json
import shutil


# ── Progress reporting ─────────────────────────────────────────────────────

def log_progress(job_id, progress_type, value, message=None):
    """Output progress as JSON for the Node.js backend to parse"""
    output = {
        "type": progress_type,
        "jobId": job_id
    }
    if progress_type == "progress":
        output["value"] = value
        output["message"] = message or f"Progress: {value:.1f}%"
    elif message:
        output["message"] = message
    print(json.dumps(output))
    sys.stdout.flush()


# ── Background rendering (numpy array, pre-rendered once) ──────────────────

def create_dot_grid_background_array(width, height, dot_color=(45, 45, 60),
                                     bg_color=(15, 15, 25), spacing=50, dot_size=2):
    """Create dot grid background ONCE and return as (H, W, 3) uint8 numpy array"""
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    for x in range(0, width, spacing):
        for y in range(0, height, spacing):
            draw.ellipse([x - dot_size, y - dot_size, x + dot_size, y + dot_size],
                         fill=dot_color)
    return np.array(img, dtype=np.uint8)


# ── ffmpeg pipe ────────────────────────────────────────────────────────────

def start_ffmpeg_pipe(output_path, audio_path, width, height, fps,
                      video_codec='libx264', video_preset='medium',
                      video_params=None):
    """Launch ffmpeg reading raw RGB24 frames from stdin, muxing audio"""
    if video_params is None:
        video_params = ['-crf', '23']
    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',
        '-pix_fmt', 'rgb24',
        '-r', str(fps),
        '-i', '-',
        '-i', audio_path,
        '-c:v', video_codec,
        '-preset', video_preset,
    ] + video_params + [
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]
    log_progress(None, "log", None, f"ffmpeg: {' '.join(cmd)}")
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── Batch audio pre-compute ────────────────────────────────────────────────

def precompute_spectrum(y, total_frames):
    """Compute STFT magnitude once for all frames.
    Returns (freq_bins, total_frames) numpy array + hop_length used.
    """
    hop_length = max(1, int(len(y) / total_frames))
    # Use blackman window for cleaner frequency separation
    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop_length,
                                window='hann'))
    # stft shape: (1 + n_fft//2, num_frames)
    # Cap to total_frames if STFT produced more
    return stft[:, :total_frames], hop_length


def bar_heights_from_spectrum(frame_fft, num_bars, max_bar_length, sensitivity):
    """Vectorized bar height calculation from a single FFT frame (numpy array)"""
    n_freqs = len(frame_fft)
    if n_freqs >= num_bars:
        band_size = n_freqs // num_bars
        trimmed = frame_fft[:num_bars * band_size]
        frequencies = trimmed.reshape(num_bars, band_size).mean(axis=1)
    else:
        frequencies = np.zeros(num_bars)

    max_val = frequencies.max()
    if max_val > 0:
        frequencies = frequencies / max_val

    # Exponential mapping for better visual response
    frequencies = frequencies ** 0.7
    heights = frequencies * max_bar_length * (sensitivity / 100.0)
    return heights


# ── Image processing helpers ───────────────────────────────────────────────

def load_center_image(image_path, img_size, corner_radius=None):
    """Load, square-crop, resize, and apply rounded-rectangle mask.
    Returns RGBA PIL Image.
    """
    img = Image.open(image_path).convert("RGBA")

    # Smart square crop
    w, h = img.size
    if w != h:
        if w > h:
            left = (w - h) // 2
            img = img.crop((left, 0, left + h, h))
        else:
            top = (h - w) // 2
            img = img.crop((0, top, w, top + w))

    img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)

    # Apply mask (rounded rect or circle)
    mask = Image.new('L', (img_size, img_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    if corner_radius is not None:
        mask_draw.rounded_rectangle([0, 0, img_size, img_size],
                                     radius=corner_radius, fill=255)
    else:
        mask_draw.ellipse([0, 0, img_size, img_size], fill=255)
    img.putalpha(mask)
    return img


def create_glow(glow_size, glow_intensity, corner_radius=None, color=(64, 224, 208), blur_radius=5):
    """Pre-create glow overlay as RGBA PIL Image"""
    glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    if glow_intensity > 0:
        for i in range(int(glow_intensity) // 2, 0, -1):
            alpha = int(40 * (1 - i / (glow_intensity / 2)))
            if alpha <= 0:
                continue
            size = glow_size - i * 2
            off = i
            if corner_radius is not None:
                cr = corner_radius
                glow_draw.rounded_rectangle(
                    [off, off, off + size, off + size],
                    radius=cr, fill=(*color, min(alpha, 255)))
            else:
                glow_draw.ellipse([off, off, off + size, off + size],
                                  fill=(*color, min(alpha, 255)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=8))
    return glow


# ═══════════════════════════════════════════════════════════════════════════
#  STYLE 1: Horizontal Mirrored Bars
# ═══════════════════════════════════════════════════════════════════════════

def create_horizontal_mirrored_visualizer(audio_path, image_path, output_path,
                                          resolution, fps, num_bars,
                                          glow_intensity, job_id,
                                          gpu_mode='cpu', bar_sensitivity=60):
    """Horizontal mirrored bars — pre-rendered bg, numpy bars, raw ffmpeg pipe"""

    try:
        log_progress(job_id, "log", None, "Loading audio file...")
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        total_frames = int(duration * fps)
        log_progress(job_id, "log", None,
                     f"Audio: {duration:.1f}s → {total_frames} frames @ {fps}fps")

        # ── Pre-compute audio spectrum ──
        log_progress(job_id, "log", None, "Pre-computing audio spectrum...")
        spectrum, hop_length = precompute_spectrum(y, total_frames)
        log_progress(job_id, "log", None,
                     f"Spectrum shape: {spectrum.shape}")

        # ── Pre-process centre image (rounded square) ──
        log_progress(job_id, "log", None, "Processing image...")
        min_dim = min(resolution)
        img_size = int(min_dim * 0.45)
        corner_radius = int(img_size * 0.06)  # Smaller radius (6% instead of 15%)
        center_img = load_center_image(image_path, img_size, corner_radius)

        # ── Pre-create smaller glow overlay ──
        glow_size = img_size + int(glow_intensity * 0.3)  # Very tight glow
        glow = create_glow(glow_size, glow_intensity, corner_radius, blur_radius=3)

        # ── Pre-render background (ONCE) ──
        log_progress(job_id, "log", None, "Pre-rendering background...")
        bg_array = create_dot_grid_background_array(
            resolution[0], resolution[1],
            dot_color=(45, 45, 60), bg_color=(15, 15, 25),
            spacing=50, dot_size=2)

        # ── ffmpeg pipe ──
        w, h = resolution
        video_codec, video_preset, video_params = codec_params(gpu_mode)
        proc = start_ffmpeg_pipe(output_path, audio_path, w, h, fps,
                                 video_codec, video_preset, video_params)

        # ── Visualizer geometry (bar area fits center image height) ──
        max_bar_length = int((w - img_size) / 2 * 0.85)
        center_x = w // 2
        center_y = h // 2
        # Gap between image edge and bar start
        bar_gap = int(img_size * 0.08)  # ~8% of image size as breathing room
        # Each bar+gap fits exactly within img_size
        bar_unit = img_size / num_bars
        bar_height = max(3, int(bar_unit * 0.55))
        gap_between_bars = max(1, int(bar_unit * 0.45))
        start_y = center_y - img_size // 2

        # Pre-allocate frame buffer
        frame = np.empty((h, w, 3), dtype=np.uint8)

        last_progress = 0

        for frame_idx in range(total_frames):
            # Progress
            progress = (frame_idx / total_frames) * 95
            if progress - last_progress >= 1:
                log_progress(job_id, "progress", progress,
                             f"Frame {frame_idx}/{total_frames}")
                last_progress = progress

            # ── Copy pre-rendered background ──
            np.copyto(frame, bg_array)

            # ─ Get bar heights from pre-computed spectrum ──
            col = min(frame_idx, spectrum.shape[1] - 1)
            raw_heights = bar_heights_from_spectrum(
                spectrum[:, col], num_bars, max_bar_length, bar_sensitivity)

            # Inverted butterfly: longest bars (bass) in CENTER, shortest at top/bottom
            # Creates a diamond shape ─ bass peaks in middle, treble at edges
            half = num_bars // 2
            heights = np.zeros(num_bars)
            for i in range(half):
                heights[i] = raw_heights[half - 1 - i]         # Top: mid ← bass (increasing)
                heights[num_bars - 1 - i] = raw_heights[half - 1 - i]  # Bottom: bass → mid (decreasing)
            if num_bars % 2 == 1:
                heights[half] = raw_heights[half]              # Center bar

            # ── Bass pulse ──
            bass_energy = float(np.mean(heights[:max(1, num_bars // 4)])) / max_bar_length if max_bar_length > 0 else 0
            pulse_scale = 1.0 + (bass_energy * 0.10)
            pulse_offset = int(10 * pulse_scale)

            # ── Draw horizontal bars (numpy slice assignment) ──
            for i in range(num_bars):
                bar_len = heights[i]
                if bar_len < 2:
                    continue

                intensity = min(1.0, bar_len / max_bar_length) if max_bar_length > 0 else 0
                r = int(32 + intensity * 32)
                g = int(178 + intensity * 77)
                b_col = int(170 + intensity * 38)

                by = start_y + i * (bar_height + gap_between_bars)
                by2 = by + bar_height

                # Left bar (extends from centre-left outward with gap)
                lx1 = int(center_x - img_size // 2 - bar_gap - pulse_offset - bar_len)
                lx2 = int(center_x - img_size // 2 - bar_gap - pulse_offset)
                if lx1 < 0:
                    lx1 = 0
                frame[by:by2, lx1:lx2] = (r, g, b_col)

                # Right bar (extends from centre-right outward with gap)
                rx1 = int(center_x + img_size // 2 + bar_gap + pulse_offset)
                rx2 = int(rx1 + bar_len)
                if rx2 > w:
                    rx2 = w
                frame[by:by2, rx1:rx2] = (r, g, b_col)

            # ── Composite centre image + glow ──
            # Convert frame region to PIL for compositing
            pulsed_is = int(img_size * pulse_scale)
            half_p = pulsed_is // 2
            ix = center_x - half_p
            iy = center_y - half_p

            # Composite glow
            if glow_intensity > 0:
                gs = int(glow_size * pulse_scale)
                gx = center_x - gs // 2
                gy = center_y - gs // 2
                # Convert to PIL, paste glow, paste image, copy back
                # Use PIL only for the compositing region
                frame_pil = Image.fromarray(frame, mode='RGB')
                glow_resized = glow.resize((gs, gs), Image.Resampling.LANCZOS)
                frame_pil.paste(glow_resized, (gx, gy), glow_resized)

                img_resized = center_img.resize(
                    (pulsed_is, pulsed_is), Image.Resampling.LANCZOS)
                frame_pil.paste(img_resized, (ix, iy), img_resized)

                # Write raw bytes to pipe
                proc.stdin.write(frame_pil.tobytes())
            else:
                # No glow — PIL only for centre image
                frame_pil = Image.fromarray(frame, mode='RGB')
                img_resized = center_img.resize(
                    (pulsed_is, pulsed_is), Image.Resampling.LANCZOS)
                frame_pil.paste(img_resized, (ix, iy), img_resized)
                proc.stdin.write(frame_pil.tobytes())

        # ── Done generating frames ──
        log_progress(job_id, "progress", 96, "Finalizing video...")
        proc.stdin.close()
        proc.wait()

        if proc.returncode == 0:
            log_progress(job_id, "progress", 100, "Complete!")
            log_progress(job_id, "log", None, "Video generated successfully")
        else:
            raise Exception(f"ffmpeg exited with code {proc.returncode}")

    except Exception as e:
        log_progress(job_id, "error", None, f"Error: {str(e)}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
#  STYLE 2: Circular Orb
# ═══════════════════════════════════════════════════════════════════════════

def create_visualizer_video(audio_path, image_path, output_path, resolution,
                            fps, num_bars, glow_intensity, job_id,
                            gpu_mode='cpu', bar_sensitivity=60):
    """Circular orb visualizer — pre-rendered bg (2x), batch STFT, raw pipe"""

    try:
        log_progress(job_id, "log", None, "Loading audio file...")
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        total_frames = int(duration * fps)
        log_progress(job_id, "log", None,
                     f"Audio: {duration:.1f}s → {total_frames} frames @ {fps}fps")

        # ── Pre-compute audio spectrum ──
        log_progress(job_id, "log", None, "Pre-computing audio spectrum...")
        spectrum, hop_length = precompute_spectrum(y, total_frames)

        # ── Pre-process centre image (circular) ──
        log_progress(job_id, "log", None, "Processing image...")
        min_dim = min(resolution)
        img_size = int(min_dim * 0.35)
        center_img = load_center_image(image_path, img_size)  # circular mask

        # ── Pre-create glow overlay (circular) ──
        glow_size = img_size + int(glow_intensity)
        glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        if glow_intensity > 0:
            for i in range(int(glow_intensity) // 2, 0, -1):
                alpha = int(30 * (1 - i / (glow_intensity / 2)))
                if alpha <= 0:
                    continue
                size = glow_size - i * 2
                off = i
                glow_draw.ellipse([off, off, off + size, off + size],
                                  fill=(100, 150, 255, min(alpha, 255)))
            glow = glow.filter(ImageFilter.GaussianBlur(radius=5))

        # ── Pre-render background at 2x for supersampling ──
        ss = 2  # supersample scale
        hr_w, hr_h = resolution[0] * ss, resolution[1] * ss
        log_progress(job_id, "log", None,
                     f"Pre-rendering background @ {hr_w}x{hr_h}...")
        hr_bg_array = create_dot_grid_background_array(
            hr_w, hr_h,
            dot_color=(45, 45, 60), bg_color=(15, 15, 25),
            spacing=50 * ss, dot_size=2)

        # ── ffmpeg pipe (at FINAL resolution, not 2x) ──
        w, h = resolution
        video_codec, video_preset, video_params = codec_params(gpu_mode)
        proc = start_ffmpeg_pipe(output_path, audio_path, w, h, fps,
                                 video_codec, video_preset, video_params)

        # ── Visualizer geometry ──
        visualizer_radius = min_dim * 0.20
        max_bar_length = min_dim * 0.18
        hr_center_x = hr_w // 2
        hr_center_y = hr_h // 2
        hr_viz_radius = visualizer_radius * ss
        hr_max_bar_len = max_bar_length * ss

        # Pre-allocate high-res frame buffer
        hr_frame = np.empty((hr_h, hr_w, 3), dtype=np.uint8)
        last_progress = 0

        for frame_idx in range(total_frames):
            progress = (frame_idx / total_frames) * 95
            if progress - last_progress >= 1:
                log_progress(job_id, "progress", progress,
                             f"Frame {frame_idx}/{total_frames}")
                last_progress = progress

            # ── Copy pre-rendered background ──
            np.copyto(hr_frame, hr_bg_array)

            # ── Get bar heights ──
            col = min(frame_idx, spectrum.shape[1] - 1)
            heights = bar_heights_from_spectrum(
                spectrum[:, col], num_bars, max_bar_length, bar_sensitivity)

            # ── Draw bars (PIL polygon — complex geometry, C-optimized) ──
            hr_draw = ImageDraw.Draw(Image.fromarray(hr_frame, mode='RGB'))

            for i in range(num_bars):
                energy = heights[i]
                if energy < 1:
                    continue

                angle = (i / num_bars) * 2 * np.pi - (np.pi / 2)
                intensity = min(1.0, energy / max_bar_length) if max_bar_length > 0 else 0

                # Colour gradient
                if intensity < 0.5:
                    r = int(0 + intensity * 2 * 100)
                    g = int(150 + intensity * 2 * 105)
                    b = 255
                else:
                    r = int(100 + (intensity - 0.5) * 2 * 155)
                    g = int(255 - (intensity - 0.5) * 2 * 100)
                    b = 255

                inner_r = hr_viz_radius
                outer_r = inner_r + energy * ss

                bar_angle = (2 * np.pi / num_bars) * 0.7
                num_seg = max(5, int(energy * ss / 3))

                for seg in range(num_seg):
                    sr0 = inner_r + (outer_r - inner_r) * (seg / num_seg)
                    sr1 = inner_r + (outer_r - inner_r) * ((seg + 1) / num_seg)
                    seg_int = seg / num_seg
                    sr_ = int(r * (0.5 + 0.5 * seg_int))
                    sg_ = int(g * (0.5 + 0.5 * seg_int))
                    sb_ = int(b * (0.5 + 0.5 * seg_int))

                    angles = [
                        angle - bar_angle / 2,
                        angle + bar_angle / 2,
                        angle + bar_angle / 2,
                        angle - bar_angle / 2
                    ]
                    radii = [sr0, sr0, sr1, sr1]
                    pts = []
                    for a, rad in zip(angles, radii):
                        pts.append((hr_center_x + rad * np.cos(a),
                                    hr_center_y + rad * np.sin(a)))
                    hr_draw.polygon(pts, fill=(sr_, sg_, sb_))

            # ── Bass pulse ──
            bass_energy = float(np.mean(heights[:max(1, num_bars // 4)])) / max_bar_length if max_bar_length > 0 else 0
            pulse_scale = 1.0 + (bass_energy * 0.15)

            # ── Composite glow + centre image (on PIL, then downsample) ──
            hr_pil = Image.fromarray(hr_frame, mode='RGB')

            # Glow
            if glow_intensity > 0:
                pulsed_gs = int(glow_size * ss * pulse_scale * (0.8 + 0.4 * bass_energy))
                pulsed_gs = min(pulsed_gs, int(min(hr_w, hr_h) * 0.5))
                if pulsed_gs > 0:
                    r_glow = glow.resize((pulsed_gs, pulsed_gs), Image.Resampling.LANCZOS)
                    gx = hr_center_x - pulsed_gs // 2
                    gy = hr_center_y - pulsed_gs // 2
                    hr_pil.paste(r_glow, (gx, gy), r_glow)

            # Centre image
            pulsed_is = int(img_size * pulse_scale * ss)
            if pulsed_is > 0:
                r_img = center_img.resize((pulsed_is, pulsed_is),
                                          Image.Resampling.LANCZOS)
                ix = hr_center_x - pulsed_is // 2
                iy = hr_center_y - pulsed_is // 2
                hr_pil.paste(r_img, (ix, iy), r_img)

            # Downsample to final resolution
            frame = hr_pil.resize(resolution, Image.Resampling.LANCZOS)

            # Write raw bytes to pipe
            proc.stdin.write(frame.tobytes())

        # ── Done ──
        log_progress(job_id, "progress", 96, "Finalizing video...")
        proc.stdin.close()
        proc.wait()

        if proc.returncode == 0:
            log_progress(job_id, "progress", 100, "Complete!")
            log_progress(job_id, "log", None, "Video generated successfully")
        else:
            raise Exception(f"ffmpeg exited with code {proc.returncode}")

    except Exception as e:
        log_progress(job_id, "error", None, f"Error: {str(e)}")
        raise


# ── Codec detection ────────────────────────────────────────────────────────

def codec_params(gpu_mode):
    """Return (video_codec, preset, params) tuple based on mode or auto-detect"""
    if gpu_mode == 'nvidia':
        return ('h264_nvenc', 'p4', ['-cq', '23', '-tune', 'hq',
                                       '-temporal-aq', '1', '-rc-lookahead', '20'])
    elif gpu_mode == 'amd':
        return ('h264_amf', 'balanced', ['-usage', 'transcoding',
                                          '-rc', 'vbr_peak', '-b:v', '8M'])
    else:
        return ('libx264', 'veryfast', ['-crf', '23'])


def detect_gpu_mode():
    """Auto-detect available GPU encoder. Returns 'nvidia', 'amd', or 'cpu'."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-encoders'],
            capture_output=True, text=True, timeout=5
        )
        encoders = result.stdout
        if 'h264_nvenc' in encoders:
            return 'nvidia'
        elif 'h264_amf' in encoders:
            return 'amd'
    except Exception:
        pass
    return 'cpu'


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Generate music visualizer video')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--image', required=True, help='Path to image file')
    parser.add_argument('--output', required=True, help='Path for output video')
    parser.add_argument('--resolution', default='1920x1080',
                        help='Video resolution (e.g., 1920x1080)')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--bars', type=int, default=64,
                        help='Number of visualizer bars')
    parser.add_argument('--glow', type=int, default=50,
                        help='Glow intensity (0-100)')
    parser.add_argument('--bar-sensitivity', type=int, default=60,
                        help='Bar sensitivity/threshold (30-90)')
    parser.add_argument('--gpu-mode', default='auto',
                        choices=['auto', 'cpu', 'amd', 'nvidia'],
                        help='GPU acceleration: auto, cpu, amd (AMF), nvidia (NVENC)')
    parser.add_argument('--style', default='circular',
                        choices=['circular', 'horizontal'],
                        help='Visualizer style')
    parser.add_argument('--job-id', required=True, help='Job ID for tracking')

    args = parser.parse_args()

    # Resolve GPU mode
    gpu_mode = args.gpu_mode
    if gpu_mode == 'auto':
        gpu_mode = detect_gpu_mode()
        log_progress(args.job_id, "log", None,
                     f"Auto-detected GPU mode: {gpu_mode}")

    # Parse resolution
    parts = args.resolution.split('x')
    resolution = (int(parts[0]), int(parts[1]))

    log_progress(args.job_id, "log", None,
                 f"Starting {args.style} style @ {args.resolution} ({gpu_mode})")

    try:
        if args.style == 'horizontal':
            create_horizontal_mirrored_visualizer(
                audio_path=args.audio,
                image_path=args.image,
                output_path=args.output,
                resolution=resolution,
                fps=args.fps,
                num_bars=args.bars,
                glow_intensity=args.glow,
                job_id=args.job_id,
                gpu_mode=gpu_mode,
                bar_sensitivity=args.bar_sensitivity
            )
        else:
            create_visualizer_video(
                audio_path=args.audio,
                image_path=args.image,
                output_path=args.output,
                resolution=resolution,
                fps=args.fps,
                num_bars=args.bars,
                glow_intensity=args.glow,
                job_id=args.job_id,
                gpu_mode=gpu_mode,
                bar_sensitivity=args.bar_sensitivity
            )

        log_progress(args.job_id, "log", None,
                     "Python processing complete, waiting for Node.js to finalize")

    except Exception as e:
        log_progress(args.job_id, "error", None,
                     f"Python error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
