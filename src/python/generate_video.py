#!/usr/bin/env python3
"""
Video Generator - CLI version for Node.js backend
Accepts command line arguments for processing
"""

import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import librosa
import subprocess
import os
import sys
import json
from datetime import datetime


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


def create_dot_grid_background(width, height, dot_color=(40, 40, 50), bg_color=(15, 15, 25), spacing=40, dot_size=2):
    """Create a technical dot grid background pattern"""
    # Create base image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw dot grid
    for x in range(0, width, spacing):
        for y in range(0, height, spacing):
            # Draw small dot/cross
            draw.ellipse([x - dot_size, y - dot_size, x + dot_size, y + dot_size], fill=dot_color)
    
    return img


def create_horizontal_mirrored_visualizer(audio_path, image_path, output_path, resolution, fps, num_bars, 
                                          glow_intensity, job_id, gpu_mode='cpu', bar_sensitivity=60):
    """Create a music visualizer with horizontal mirrored bars on left and right sides"""
    
    try:
        log_progress(job_id, "log", None, "Loading audio file...")
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        log_progress(job_id, "log", None, f"Audio duration: {duration:.2f} seconds")
        
        # Load and prepare image
        log_progress(job_id, "log", None, "Processing image...")
        center_img = Image.open(image_path)
        
        min_dim = min(resolution)
        img_size = int(min_dim * 0.45)  # Larger image for this style
        
        center_img = center_img.convert("RGBA")
        
        # Smart crop to square
        orig_width, orig_height = center_img.size
        if orig_width != orig_height:
            if orig_width > orig_height:
                left = (orig_width - orig_height) // 2
                top = 0
                right = left + orig_height
                bottom = orig_height
            else:
                left = 0
                top = (orig_height - orig_width) // 2
                right = orig_width
                bottom = top + orig_width
            center_img = center_img.crop((left, top, right, bottom))
        
        # Resize to final size
        center_img = center_img.resize((img_size, img_size), Image.Resampling.LANCZOS)
        
        # Rounded square mask (not circular)
        mask = Image.new('L', (img_size, img_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        corner_radius = int(img_size * 0.15)  # 15% corner radius
        mask_draw.rounded_rectangle([0, 0, img_size, img_size], radius=corner_radius, fill=255)
        
        # Apply mask
        center_img.putalpha(mask)
        
        # Glow effect
        glow_size = img_size + int(glow_intensity * 1.5)
        glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        
        if glow_intensity > 0:
            for i in range(int(glow_intensity) // 2, 0, -1):
                alpha = int(40 * (1 - i / (glow_intensity / 2)))
                if alpha > 0:
                    size = glow_size - i * 2
                    offset = i
                    glow_draw.rounded_rectangle(
                        [offset, offset, offset + size, offset + size],
                        radius=corner_radius,
                        fill=(64, 224, 208, min(alpha, 255))
                    )
            
            glow = glow.filter(ImageFilter.GaussianBlur(radius=8))
        
        # Calculate frames
        total_frames = int(duration * fps)
        hop_length = max(1, int(len(y) / total_frames))
        
        log_progress(job_id, "log", None, f"Generating {total_frames} frames at {fps} fps...")
        
        # Create temp directory
        temp_dir = os.path.join(os.path.dirname(output_path), f"temp_{job_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Visualizer parameters for horizontal bars
        bar_height = int(resolution[1] * 0.025)  # Height of each bar
        max_bar_length = int((resolution[0] - img_size) / 2 * 0.85)  # Max length on each side
        gap_between_bars = int(resolution[1] * 0.015)  # Gap between bars vertically
        
        # Generate frames
        last_progress = 0
        for frame_idx in range(total_frames):
            # Update progress
            progress = (frame_idx / total_frames) * 80
            if progress - last_progress >= 1:
                log_progress(job_id, "progress", progress, 
                           f"Generating frame {frame_idx}/{total_frames}")
                last_progress = progress
            
            # Get audio segment
            start_sample = frame_idx * hop_length
            end_sample = min((frame_idx + 1) * hop_length, len(y))
            audio_segment = y[start_sample:end_sample]
            
            if len(audio_segment) == 0:
                continue
            
            # FFT analysis
            fft = np.abs(np.fft.rfft(audio_segment))
            
            if len(fft) >= num_bars:
                band_size = len(fft) // num_bars
                frequencies = []
                for i in range(num_bars):
                    start = i * band_size
                    end = (i + 1) * band_size
                    energy = np.mean(fft[start:end])
                    frequencies.append(energy)
            else:
                frequencies = np.zeros(num_bars)
            
            # Normalize
            if max(frequencies) > 0:
                frequencies = np.array(frequencies) / max(frequencies)
            frequencies = frequencies ** 0.7
            
            # Create frame with dot grid background
            frame = create_dot_grid_background(
                resolution[0], 
                resolution[1],
                dot_color=(45, 45, 60),
                bg_color=(15, 15, 25),
                spacing=50,
                dot_size=2
            )
            draw = ImageDraw.Draw(frame)
            
            # Center position
            center_x = resolution[0] // 2
            center_y = resolution[1] // 2
            
            # Calculate total height of visualizer area
            total_visualizer_height = num_bars * (bar_height + gap_between_bars)
            start_y = center_y - total_visualizer_height // 2
            
            # Calculate bass energy for pulsing
            bass_energy = np.mean(frequencies[:len(frequencies)//4]) if len(frequencies) > 0 else 0
            pulse_scale = 1.0 + (bass_energy * 0.10)
            
            # Draw horizontal bars on both sides
            sensitivity_multiplier = bar_sensitivity / 100.0
            
            for i, energy in enumerate(frequencies):
                # Calculate bar length
                bar_length = min(energy * max_bar_length * sensitivity_multiplier, max_bar_length)
                
                if bar_length < 2:  # Skip very small bars
                    continue
                
                # Calculate intensity for color
                intensity = min(1.0, energy)
                
                # Create gradient colors (teal to cyan)
                r = int(32 + intensity * 32)
                g = int(178 + intensity * 77)
                b = int(170 + intensity * 38)
                
                # Calculate Y position for this bar
                bar_y = start_y + i * (bar_height + gap_between_bars)
                
                # Left side bars (extend from left toward center)
                left_bar_x1 = center_x - img_size // 2 - int(10 * pulse_scale) - bar_length
                left_bar_x2 = center_x - img_size // 2 - int(10 * pulse_scale)
                draw.rectangle(
                    [left_bar_x1, bar_y, left_bar_x2, bar_y + bar_height],
                    fill=(r, g, b)
                )
                
                # Right side bars (extend from center toward right)
                right_bar_x1 = center_x + img_size // 2 + int(10 * pulse_scale)
                right_bar_x2 = center_x + img_size // 2 + int(10 * pulse_scale) + bar_length
                draw.rectangle(
                    [right_bar_x1, bar_y, right_bar_x2, bar_y + bar_height],
                    fill=(r, g, b)
                )
            
            # Paste glow effect
            if glow_intensity > 0:
                pulsed_glow_size = int(glow_size * pulse_scale)
                glow_x = center_x - pulsed_glow_size // 2
                glow_y = center_y - pulsed_glow_size // 2
                frame.paste(glow.resize((pulsed_glow_size, pulsed_glow_size), Image.Resampling.LANCZOS), 
                           (glow_x, glow_y), 
                           glow.resize((pulsed_glow_size, pulsed_glow_size), Image.Resampling.LANCZOS))
            
            # Paste center image with pulsing
            pulsed_img_size = int(img_size * pulse_scale)
            img_x = center_x - pulsed_img_size // 2
            img_y = center_y - pulsed_img_size // 2
            frame.paste(center_img.resize((pulsed_img_size, pulsed_img_size), Image.Resampling.LANCZOS), 
                       (img_x, img_y), 
                       center_img.resize((pulsed_img_size, pulsed_img_size), Image.Resampling.LANCZOS))
            
            # Save frame
            frame.save(f"{temp_dir}/frame_{frame_idx:06d}.png")
        
        log_progress(job_id, "progress", 85, "Encoding video with ffmpeg...")
        
        # Configure video codec
        if gpu_mode == 'amd':
            video_codec = 'h264_amf'
            video_preset = 'quality'
            video_params = ['-qp_p', '23', '-qp_i', '23']
        elif gpu_mode == 'nvidia':
            video_codec = 'h264_nvenc'
            video_preset = 'fast'
            video_params = ['-cq', '23']
        else:
            video_codec = 'libx264'
            video_preset = 'medium'
            video_params = ['-crf', '23']
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(fps),
            '-i', f'{temp_dir}/frame_%06d.png',
            '-i', audio_path,
            '-c:v', video_codec,
            '-preset', video_preset,
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest'
        ]
        ffmpeg_cmd.extend(video_params)
        ffmpeg_cmd.append(output_path)
        
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        log_progress(job_id, "progress", 100, "Complete!")
        
    finally:
        if os.path.exists(temp_dir):
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)


def create_visualizer_video(audio_path, image_path, output_path, resolution, fps, num_bars, 
                            glow_intensity, job_id, gpu_mode='cpu', bar_sensitivity=60):
    """Create a music visualizer video with the given parameters"""
    
    try:
        log_progress(job_id, "log", None, "Loading audio file...")
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        log_progress(job_id, "log", None, f"Audio duration: {duration:.2f} seconds")
        
        # Load and prepare image
        log_progress(job_id, "log", None, "Processing image...")
        center_img = Image.open(image_path)
        
        min_dim = min(resolution)
        img_size = int(min_dim * 0.35)  # Smaller image (35% instead of 45%)
        
        center_img = center_img.convert("RGBA")
        
        # Smart crop to square (center crop maintaining aspect ratio)
        orig_width, orig_height = center_img.size
        if orig_width != orig_height:
            # Crop to square from center
            if orig_width > orig_height:
                # Landscape - crop sides
                left = (orig_width - orig_height) // 2
                top = 0
                right = left + orig_height
                bottom = orig_height
            else:
                # Portrait - crop top/bottom
                left = 0
                top = (orig_height - orig_width) // 2
                right = orig_width
                bottom = top + orig_width
            center_img = center_img.crop((left, top, right, bottom))
        
        # Now resize to final size (square to square, no distortion)
        center_img = center_img.resize((img_size, img_size), Image.Resampling.LANCZOS)
        
        # Circular mask with anti-aliased edges
        mask = Image.new('L', (img_size, img_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, img_size, img_size], fill=255)
        
        # Apply mask
        center_img.putalpha(mask)
        
        # Glow effect
        glow_size = img_size + int(glow_intensity)
        glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        
        if glow_intensity > 0:
            for i in range(int(glow_intensity) // 2, 0, -1):
                alpha = int(30 * (1 - i / (glow_intensity / 2)))
                if alpha > 0:
                    size = glow_size - i * 2
                    offset = i
                    glow_draw.ellipse([offset, offset, offset + size, offset + size], 
                                     fill=(100, 150, 255, min(alpha, 255)))
            
            glow = glow.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Calculate frames
        total_frames = int(duration * fps)
        hop_length = max(1, int(len(y) / total_frames))
        
        log_progress(job_id, "log", None, f"Generating {total_frames} frames at {fps} fps...")
        
        # Create temp directory
        temp_dir = os.path.join(os.path.dirname(output_path), f"temp_{job_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Visualizer parameters - centered circular visualizer (closer to smaller image)
        visualizer_radius = min(resolution) * 0.20  # Reduced gap - closer to image
        max_bar_length = min(resolution) * 0.18  # Slightly longer bars
        
        # Generate frames
        last_progress = 0
        for frame_idx in range(total_frames):
            # Update progress (0-80% for frame generation, 20% reserved for encoding)
            progress = (frame_idx / total_frames) * 80
            if progress - last_progress >= 1:
                log_progress(job_id, "progress", progress, 
                           f"Generating frame {frame_idx}/{total_frames}")
                last_progress = progress
            
            # Get audio segment
            start_sample = frame_idx * hop_length
            end_sample = min((frame_idx + 1) * hop_length, len(y))
            audio_segment = y[start_sample:end_sample]
            
            if len(audio_segment) == 0:
                continue
            
            # FFT analysis
            fft = np.abs(np.fft.rfft(audio_segment))
            
            if len(fft) >= num_bars:
                band_size = len(fft) // num_bars
                frequencies = []
                for i in range(num_bars):
                    start = i * band_size
                    end = (i + 1) * band_size
                    energy = np.mean(fft[start:end])
                    frequencies.append(energy)
            else:
                frequencies = np.zeros(num_bars)
            
            # Normalize
            if max(frequencies) > 0:
                frequencies = np.array(frequencies) / max(frequencies)
            frequencies = frequencies ** 0.7
            frequencies = frequencies * max_bar_length
            
            # Create high-resolution frame for anti-aliasing (2x supersampling)
            supersample_scale = 2
            high_res_resolution = (resolution[0] * supersample_scale, resolution[1] * supersample_scale)
            
            # Create dot grid background
            high_res_frame = create_dot_grid_background(
                high_res_resolution[0], 
                high_res_resolution[1],
                dot_color=(45, 45, 60),
                bg_color=(15, 15, 25),
                spacing=50 * supersample_scale,
                dot_size=2
            )
            high_res_draw = ImageDraw.Draw(high_res_frame)
            
            # Center point (high-res)
            high_res_center_x = high_res_resolution[0] // 2
            high_res_center_y = high_res_resolution[1] // 2
            
            # Scale visualizer parameters for high-res rendering
            high_res_visualizer_radius = visualizer_radius * supersample_scale
            high_res_max_bar_length = max_bar_length * supersample_scale
            
            # Draw circular visualizer bars around the center (high-res for anti-aliasing)
            for i, energy in enumerate(frequencies):
                # Calculate angle for this bar (full circle)
                angle = (i / num_bars) * 2 * np.pi - (np.pi / 2)  # Start from top
                
                # Calculate bar length based on energy
                # Apply sensitivity threshold - bars peak at bar_sensitivity% of max
                sensitivity_multiplier = bar_sensitivity / 100.0
                bar_length = min(energy * sensitivity_multiplier, max_bar_length * sensitivity_multiplier)
                
                # Calculate intensity for color
                intensity = min(1.0, energy / max_bar_length)
                
                # Create gradient colors (cyan to purple to pink)
                if intensity < 0.5:
                    # Blue to cyan
                    r = int(0 + intensity * 2 * 100)
                    g = int(150 + intensity * 2 * 105)
                    b = 255
                else:
                    # Cyan to pink
                    r = int(100 + (intensity - 0.5) * 2 * 155)
                    g = int(255 - (intensity - 0.5) * 2 * 100)
                    b = 255
                
                # Calculate bar position (high-res)
                inner_radius = high_res_visualizer_radius
                outer_radius = inner_radius + bar_length * supersample_scale
                
                # Calculate bar width at this radius
                bar_angle_width = (2 * np.pi / num_bars) * 0.7  # 70% of space for bar, 30% gap
                
                # Draw bar as a radial rectangle with anti-aliasing
                num_segments = max(5, int(bar_length * supersample_scale / 3))  # More segments for smoother edges
                for seg in range(num_segments):
                    seg_radius = inner_radius + (outer_radius - inner_radius) * (seg / num_segments)
                    seg_radius_next = inner_radius + (outer_radius - inner_radius) * ((seg + 1) / num_segments)
                    
                    # Calculate segment intensity for gradient effect
                    seg_intensity = seg / num_segments
                    seg_r = int(r * (0.5 + 0.5 * seg_intensity))
                    seg_g = int(g * (0.5 + 0.5 * seg_intensity))
                    seg_b = int(b * (0.5 + 0.5 * seg_intensity))
                    
                    # Calculate corners
                    angles = [
                        angle - bar_angle_width / 2,
                        angle + bar_angle_width / 2,
                        angle + bar_angle_width / 2,
                        angle - bar_angle_width / 2
                    ]
                    radii = [seg_radius, seg_radius, seg_radius_next, seg_radius_next]
                    
                    points = []
                    for a, rad in zip(angles, radii):
                        px = high_res_center_x + rad * np.cos(a)
                        py = high_res_center_y + rad * np.sin(a)
                        points.append((px, py))
                    
                    high_res_draw.polygon(points, fill=(seg_r, seg_g, seg_b))
            
            # Calculate bass energy for image pulsing (use first 1/4 of frequencies = bass)
            bass_energy = np.mean(frequencies[:len(frequencies)//4]) / max_bar_length if max_bar_length > 0 else 0
            pulse_scale = 1.0 + (bass_energy * 0.15)  # Pulse between 1.0 and 1.15 (15% max increase)
            
            # Calculate pulsed image size
            pulsed_img_size = int(img_size * pulse_scale)
            
            # Paste glow effect behind image (high-res)
            if glow_intensity > 0:
                # Scale glow for high-res
                high_res_glow_size = int(glow_size * supersample_scale * (0.8 + 0.4 * bass_energy) * pulse_scale)
                high_res_glow_size = min(high_res_glow_size, int(min(high_res_resolution) * 0.5))
                
                glow_x = high_res_center_x - high_res_glow_size // 2
                glow_y = high_res_center_y - high_res_glow_size // 2
                
                # Resize glow for high-res
                if high_res_glow_size != glow_size * supersample_scale:
                    high_res_glow = glow.resize((high_res_glow_size, high_res_glow_size), Image.Resampling.LANCZOS)
                    high_res_frame.paste(high_res_glow, (glow_x, glow_y), high_res_glow)
                else:
                    high_res_glow = glow.resize((high_res_glow_size, high_res_glow_size), Image.Resampling.LANCZOS)
                    high_res_frame.paste(high_res_glow, (glow_x, glow_y), high_res_glow)
            
            # Paste center image with pulsing effect (high-res)
            high_res_pulsed_img_size = int(pulsed_img_size * supersample_scale)
            if high_res_pulsed_img_size > 0:
                # Resize image for high-res rendering
                high_res_pulsed_img = center_img.resize((high_res_pulsed_img_size, high_res_pulsed_img_size), Image.Resampling.LANCZOS)
                img_x = high_res_center_x - high_res_pulsed_img_size // 2
                img_y = high_res_center_y - high_res_pulsed_img_size // 2
                high_res_frame.paste(high_res_pulsed_img, (img_x, img_y), high_res_pulsed_img)
            
            # Downsample to final resolution with anti-aliasing
            frame = high_res_frame.resize(resolution, Image.Resampling.LANCZOS)
            
            # Save frame
            frame.save(f"{temp_dir}/frame_{frame_idx:06d}.png")
        
        # Encode video
        log_progress(job_id, "progress", 85, "Encoding video with ffmpeg...")
        
        # Configure video codec based on GPU mode
        if gpu_mode == 'amd':
            log_progress(job_id, "log", None, "Using AMD GPU (AMF) hardware encoder")
            video_codec = 'h264_amf'
            video_preset = 'quality'  # AMD AMF preset
            video_params = ['-qp_p', '23', '-qp_i', '23']
        elif gpu_mode == 'nvidia':
            log_progress(job_id, "log", None, "Using NVIDIA GPU (NVENC) hardware encoder")
            video_codec = 'h264_nvenc'
            video_preset = 'fast'  # NVENC preset
            video_params = ['-cq', '23']
        else:
            log_progress(job_id, "log", None, "Using CPU encoder (libx264)")
            video_codec = 'libx264'
            video_preset = 'medium'
            video_params = ['-crf', '23']
        
        log_progress(job_id, "log", None, f"Starting video encoding with {video_codec}...")
        
        # Build ffmpeg command
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(fps),
            '-i', f'{temp_dir}/frame_%06d.png',
            '-i', audio_path,
            '-c:v', video_codec,
            '-preset', video_preset,
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest'
        ]
        
        # Add codec-specific parameters
        ffmpeg_cmd.extend(video_params)
        
        # Add output path
        ffmpeg_cmd.append(output_path)
        
        try:
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            log_progress(job_id, "progress", 100, "Complete!")
            log_progress(job_id, "log", None, "Video encoding complete!")
            
        except subprocess.CalledProcessError as e:
            log_progress(job_id, "error", None, f"FFmpeg error: {e.stderr}")
            raise Exception(f"FFmpeg encoding failed: {e.stderr}")
            
    except Exception as e:
        log_progress(job_id, "error", None, f"Error: {str(e)}")
        raise
        
    finally:
        # Cleanup temp frames
        try:
            if os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
                log_progress(job_id, "log", None, "Cleaned up temporary files")
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description='Generate music visualizer video')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--image', required=True, help='Path to image file')
    parser.add_argument('--output', required=True, help='Path for output video')
    parser.add_argument('--resolution', default='1920x1080', help='Video resolution (e.g., 1920x1080)')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--bars', type=int, default=64, help='Number of visualizer bars')
    parser.add_argument('--glow', type=int, default=50, help='Glow intensity (0-100)')
    parser.add_argument('--bar-sensitivity', type=int, default=60, help='Bar sensitivity/threshold (30-90). Lower = bars peak at lower height.')
    parser.add_argument('--gpu-mode', default='cpu', choices=['cpu', 'amd', 'nvidia'],
                        help='GPU acceleration mode: cpu (default), amd (AMD AMF), nvidia (NVIDIA NVENC)')
    parser.add_argument('--style', default='circular', choices=['circular', 'horizontal'],
                        help='Visualizer style: circular (default) or horizontal')
    parser.add_argument('--job-id', required=True, help='Job ID for tracking')
    
    args = parser.parse_args()
    
    # Parse resolution
    res_parts = args.resolution.split('x')
    resolution = (int(res_parts[0]), int(res_parts[1]))
    
    log_progress(args.job_id, "log", None, f"Starting video generation with {args.style} style...")
    
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
                gpu_mode=args.gpu_mode,
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
                gpu_mode=args.gpu_mode,
                bar_sensitivity=args.bar_sensitivity
            )
        
        # Node.js handles the final completion signal based on exit code and file existence
        # Just log success here
        log_progress(args.job_id, "log", None, "Python processing complete, waiting for Node.js to finalize")
        
    except Exception as e:
        # Report error via progress, Node.js will detect non-zero exit code
        log_progress(args.job_id, "error", None, f"Python error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
