#!/usr/bin/env python3
"""
Music Visualizer Video Generator
Creates a video with a centered image and audio-reactive visualizer bars
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import librosa
import subprocess
import os
from tqdm import tqdm


def create_visualizer_video(audio_path, image_path, output_path, fps=30, resolution=(1920, 1080)):
    """
    Create a music visualizer video.
    
    Args:
        audio_path: Path to the MP3 file
        image_path: Path to the center image
        output_path: Output video path
        fps: Frames per second
        resolution: Video resolution (width, height)
    """
    print(f"Loading audio: {audio_path}")
    
    # Load audio
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    print(f"Audio duration: {duration:.2f} seconds")
    print(f"Sample rate: {sr}")
    
    # Load and prepare the center image
    print(f"Loading image: {image_path}")
    center_img = Image.open(image_path)
    
    # Calculate image size (make it take up ~50% of the smaller dimension)
    min_dim = min(resolution)
    img_size = int(min_dim * 0.5)
    
    # Resize and make circular
    center_img = center_img.convert("RGBA")
    center_img = center_img.resize((img_size, img_size), Image.Resampling.LANCZOS)
    
    # Create circular mask
    mask = Image.new('L', (img_size, img_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, img_size, img_size], fill=255)
    
    # Apply circular mask
    center_img.putalpha(mask)
    
    # Add a glow effect
    glow_size = img_size + 40
    glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Create multiple glow layers
    for i in range(20, 0, -1):
        alpha = int(30 * (1 - i/20))
        size = glow_size - i * 2
        offset = i
        glow_draw.ellipse([offset, offset, offset + size, offset + size], 
                         fill=(100, 150, 255, alpha))
    
    # Blur the glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius=5))
    
    # Calculate audio features for each frame
    total_frames = int(duration * fps)
    hop_length = int(len(y) / total_frames)
    
    print(f"Generating {total_frames} frames at {fps} fps...")
    
    # Create temporary directory for frames
    temp_dir = "temp_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Parameters for visualizer
    num_bars = 64
    bar_width = resolution[0] / num_bars
    max_bar_height = resolution[1] * 0.4
    
    # Generate frames
    for frame_idx in tqdm(range(total_frames), desc="Generating frames"):
        # Get audio segment for this frame
        start_sample = frame_idx * hop_length
        end_sample = min((frame_idx + 1) * hop_length, len(y))
        audio_segment = y[start_sample:end_sample]
        
        if len(audio_segment) == 0:
            continue
        
        # Compute FFT for frequency analysis
        fft = np.abs(np.fft.rfft(audio_segment))
        
        # Downsample to number of bars
        if len(fft) >= num_bars:
            # Average energy in frequency bands
            band_size = len(fft) // num_bars
            frequencies = []
            for i in range(num_bars):
                start = i * band_size
                end = (i + 1) * band_size
                energy = np.mean(fft[start:end])
                frequencies.append(energy)
        else:
            frequencies = np.zeros(num_bars)
        
        # Normalize and apply sensitivity
        if max(frequencies) > 0:
            frequencies = np.array(frequencies) / max(frequencies)
        frequencies = frequencies ** 0.7  # Adjust curve
        frequencies = frequencies * max_bar_height
        
        # Create frame
        frame = Image.new('RGB', resolution, (10, 10, 20))
        draw = ImageDraw.Draw(frame)
        
        # Draw visualizer bars (bottom)
        for i, height in enumerate(frequencies):
            x = i * bar_width
            bar_h = height
            
            # Create gradient color based on height
            intensity = min(1.0, height / max_bar_height)
            r = int(50 + intensity * 100)
            g = int(100 + intensity * 155)
            b = int(200 + intensity * 55)
            
            # Draw bar with rounded top
            draw.rectangle(
                [x, resolution[1] - bar_h, x + bar_width - 2, resolution[1]],
                fill=(r, g, b)
            )
        
        # Draw visualizer bars (top - mirrored)
        for i, height in enumerate(frequencies):
            x = i * bar_width
            bar_h = height * 0.6
            
            intensity = min(1.0, height / max_bar_height)
            r = int(50 + intensity * 100)
            g = int(100 + intensity * 155)
            b = int(200 + intensity * 55)
            
            draw.rectangle(
                [x, 0, x + bar_width - 2, bar_h],
                fill=(r, g, b)
            )
        
        # Paste glow behind center image
        glow_x = (resolution[0] - glow_size) // 2
        glow_y = (resolution[1] - glow_size) // 2
        frame.paste(glow, (glow_x, glow_y), glow)
        
        # Paste center image
        img_x = (resolution[0] - img_size) // 2
        img_y = (resolution[1] - img_size) // 2
        frame.paste(center_img, (img_x, img_y), center_img)
        
        # Save frame
        frame.save(f"{temp_dir}/frame_{frame_idx:06d}.png")
    
    print("Encoding video with audio...")
    
    # Use ffmpeg to create video from frames and add audio
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-framerate', str(fps),
        '-i', f'{temp_dir}/frame_%06d.png',
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"✓ Video created successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error encoding video: {e}")
        print(f"FFmpeg stderr: {e.stderr.decode()}")
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg first.")
        print("Visit: https://ffmpeg.org/download.html")
    finally:
        # Cleanup temp frames
        print("Cleaning up temporary files...")
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


if __name__ == "__main__":
    # Configuration
    AUDIO_FILE = "Riley (AI Cover).mp3"
    IMAGE_FILE = "center_image.png"
    OUTPUT_FILE = "Riley_Visualizer.mp4"
    
    # Check if files exist
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: Audio file not found: {AUDIO_FILE}")
        exit(1)
    
    if not os.path.exists(IMAGE_FILE):
        print(f"Error: Image file not found: {IMAGE_FILE}")
        exit(1)
    
    print("=" * 60)
    print("Music Visualizer Video Generator")
    print("=" * 60)
    
    create_visualizer_video(AUDIO_FILE, IMAGE_FILE, OUTPUT_FILE)
    
    print("=" * 60)
    print("Done!")
