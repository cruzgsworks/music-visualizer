#!/usr/bin/env python3
"""
Music Visualizer Video Generator - GUI Version
A user-friendly interface for creating music visualizer videos
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import librosa
import subprocess
import os
from datetime import datetime


class VisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 AI Cover Visualizer")
        self.root.geometry("700x600")
        self.root.configure(bg='#1e1e1e')
        
        # Variables
        self.audio_path = tk.StringVar()
        self.image_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.resolution_var = tk.StringVar(value="1920x1080")
        self.fps_var = tk.IntVar(value=30)
        self.bar_count_var = tk.IntVar(value=64)
        self.glow_intensity_var = tk.IntVar(value=50)
        
        self.is_processing = False
        self.stop_requested = False
        
        self.setup_ui()
        
        # Ensure UI is in ready state
        self.reset_ui_state()
        
        # Initial log message
        self.log("Visualizer GUI initialized and ready")
        
    def setup_ui(self):
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='white', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#00d4ff')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="🎵 AI Cover Visualizer", style='Header.TLabel')
        header.pack(pady=(0, 20))
        
        # File Selection Section
        files_frame = ttk.LabelFrame(main_frame, text="📁 File Selection", padding="10")
        files_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Audio file
        ttk.Label(files_frame, text="Audio File (MP3):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(files_frame, textvariable=self.audio_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(files_frame, text="Browse", command=self.browse_audio).grid(row=0, column=2, padx=5, pady=5)
        
        # Image file
        ttk.Label(files_frame, text="Center Image:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(files_frame, textvariable=self.image_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(files_frame, text="Browse", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)
        
        # Output file
        ttk.Label(files_frame, text="Output Video:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(files_frame, textvariable=self.output_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(files_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)
        
        # Settings Section
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Visualizer Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Resolution
        ttk.Label(settings_frame, text="Resolution:").grid(row=0, column=0, sticky=tk.W, pady=5)
        resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var, 
                                       values=["1920x1080", "1280x720", "3840x2160", "1080x1920"], 
                                       state="readonly", width=15)
        resolution_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # FPS
        ttk.Label(settings_frame, text="Frame Rate (FPS):").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        fps_spin = ttk.Spinbox(settings_frame, from_=15, to=60, textvariable=self.fps_var, width=10)
        fps_spin.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Bar count
        ttk.Label(settings_frame, text="Visualizer Bars:").grid(row=1, column=0, sticky=tk.W, pady=5)
        bar_spin = ttk.Spinbox(settings_frame, from_=32, to=128, textvariable=self.bar_count_var, width=15)
        bar_spin.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Glow intensity
        ttk.Label(settings_frame, text="Glow Intensity:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        glow_scale = ttk.Scale(settings_frame, from_=0, to=100, variable=self.glow_intensity_var, orient=tk.HORIZONTAL, length=100)
        glow_scale.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Presets
        preset_frame = ttk.Frame(settings_frame)
        preset_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Label(preset_frame, text="Quick Presets:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preset_frame, text="YouTube (1080p)", command=lambda: self.set_preset("youtube")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="TikTok (9:16)", command=lambda: self.set_preset("tiktok")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Instagram", command=lambda: self.set_preset("instagram")).pack(side=tk.LEFT, padx=2)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=600, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready to start", foreground='#888888')
        self.status_label.pack()
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg='#0d0d0d', fg='#00ff00', 
                                                 font=('Consolas', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Rendering", command=self.start_rendering, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_rendering, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="❓ Help", command=self.show_help, width=10).pack(side=tk.RIGHT, padx=5)
        
        # Set default output path
        self.output_path.set(os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_visualizer.mp4"))
        
    def set_preset(self, preset):
        if preset == "youtube":
            self.resolution_var.set("1920x1080")
            self.fps_var.set(30)
            self.bar_count_var.set(64)
        elif preset == "tiktok":
            self.resolution_var.set("1080x1920")
            self.fps_var.set(30)
            self.bar_count_var.set(48)
        elif preset == "instagram":
            self.resolution_var.set("1080x1080")
            self.fps_var.set(30)
            self.bar_count_var.set(48)
        self.log(f"Applied preset: {preset}")
        
    def browse_audio(self):
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.mp3 *.wav *.flac *.m4a"), ("All files", "*.*")]
        )
        if filename:
            self.audio_path.set(filename)
            # Auto-set output path based on audio filename
            base_name = os.path.splitext(os.path.basename(filename))[0]
            output_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_path.set(os.path.join(output_dir, f"{base_name}_Visualizer.mp4"))
            self.log(f"Selected audio: {os.path.basename(filename)}")
            
    def browse_image(self):
        filename = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if filename:
            self.image_path.set(filename)
            self.log(f"Selected image: {os.path.basename(filename)}")
            
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
            
    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def update_status(self, message, is_error=False):
        self.status_label.config(text=message, foreground='#ff4444' if is_error else '#00d4ff')
        self.root.update_idletasks()
        
    def reset_ui_state(self):
        """Reset UI to ready state - ensures buttons are properly enabled/disabled"""
        self.is_processing = False
        self.stop_requested = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("Ready to start")
        self.progress_var.set(0)
        self.root.update_idletasks()
        
    def start_rendering(self):
        # Validate inputs
        if not self.audio_path.get() or not os.path.exists(self.audio_path.get()):
            messagebox.showerror("Error", "Please select a valid audio file.")
            return
            
        if not self.image_path.get() or not os.path.exists(self.image_path.get()):
            messagebox.showerror("Error", "Please select a valid image file.")
            return
            
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output file path.")
            return
            
        # Start processing in a separate thread
        self.is_processing = True
        self.stop_requested = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self.render_video, daemon=True)
        thread.start()
        
    def stop_rendering(self):
        self.stop_requested = True
        self.update_status("Stopping... (will finish current frame)")
        self.log("Stop requested by user")
        
    def render_video(self):
        try:
            audio_path = self.audio_path.get()
            image_path = self.image_path.get()
            output_path = self.output_path.get()
            
            # Parse resolution
            res_parts = self.resolution_var.get().split('x')
            resolution = (int(res_parts[0]), int(res_parts[1]))
            fps = self.fps_var.get()
            num_bars = self.bar_count_var.get()
            
            self.log("=" * 50)
            self.log("Starting visualizer generation")
            self.log(f"Resolution: {resolution[0]}x{resolution[1]}")
            self.log(f"Frame Rate: {fps} fps")
            self.log(f"Visualizer Bars: {num_bars}")
            self.update_status("Loading audio...")
            
            # Load audio
            self.log("Analyzing audio file...")
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            self.log(f"Audio duration: {duration:.2f} seconds")
            
            # Load and prepare image
            self.log("Processing image...")
            center_img = Image.open(image_path)
            min_dim = min(resolution)
            img_size = int(min_dim * 0.45)
            
            center_img = center_img.convert("RGBA")
            center_img = center_img.resize((img_size, img_size), Image.Resampling.LANCZOS)
            
            # Circular mask
            mask = Image.new('L', (img_size, img_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, img_size, img_size], fill=255)
            center_img.putalpha(mask)
            
            # Glow effect
            glow_size = img_size + int(self.glow_intensity_var.get())
            glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            
            for i in range(int(self.glow_intensity_var.get()) // 2, 0, -1):
                alpha = int(30 * (1 - i/(self.glow_intensity_var.get() / 2)))
                size = glow_size - i * 2
                offset = i
                glow_draw.ellipse([offset, offset, offset + size, offset + size], 
                                 fill=(100, 150, 255, alpha))
            
            glow = glow.filter(ImageFilter.GaussianBlur(radius=5))
            
            # Calculate frames
            total_frames = int(duration * fps)
            hop_length = max(1, int(len(y) / total_frames))
            
            self.log(f"Generating {total_frames} frames...")
            
            # Create temp directory
            temp_dir = os.path.join(os.path.dirname(output_path), "temp_frames")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Visualizer parameters
            bar_width = resolution[0] / num_bars
            max_bar_height = resolution[1] * 0.35
            
            # Generate frames
            for frame_idx in range(total_frames):
                if self.stop_requested:
                    self.log("Rendering stopped by user")
                    break
                
                # Update progress
                progress = (frame_idx / total_frames) * 80  # Reserve 20% for encoding
                self.progress_var.set(progress)
                
                if frame_idx % 30 == 0:  # Update status every second
                    eta = (total_frames - frame_idx) / fps / 60
                    self.update_status(f"Generating frame {frame_idx}/{total_frames} (ETA: {eta:.1f} min)")
                
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
                frequencies = frequencies * max_bar_height
                
                # Create frame
                frame = Image.new('RGB', resolution, (15, 15, 25))
                draw = ImageDraw.Draw(frame)
                
                # Draw visualizer bars (bottom)
                for i, height in enumerate(frequencies):
                    x = i * bar_width
                    bar_h = height
                    
                    intensity = min(1.0, height / max_bar_height)
                    r = int(50 + intensity * 100)
                    g = int(100 + intensity * 155)
                    b = int(200 + intensity * 55)
                    
                    draw.rectangle(
                        [x, resolution[1] - bar_h, x + bar_width - 2, resolution[1]],
                        fill=(r, g, b)
                    )
                
                # Draw visualizer bars (top)
                for i, height in enumerate(frequencies):
                    x = i * bar_width
                    bar_h = height * 0.5
                    
                    intensity = min(1.0, height / max_bar_height)
                    r = int(50 + intensity * 100)
                    g = int(100 + intensity * 155)
                    b = int(200 + intensity * 55)
                    
                    draw.rectangle(
                        [x, 0, x + bar_width - 2, bar_h],
                        fill=(r, g, b)
                    )
                
                # Paste glow and center image
                glow_x = (resolution[0] - glow_size) // 2
                glow_y = (resolution[1] - glow_size) // 2
                frame.paste(glow, (glow_x, glow_y), glow)
                
                img_x = (resolution[0] - img_size) // 2
                img_y = (resolution[1] - img_size) // 2
                frame.paste(center_img, (img_x, img_y), center_img)
                
                # Save frame
                frame.save(f"{temp_dir}/frame_{frame_idx:06d}.png")
            
            if not self.stop_requested:
                # Encode video
                self.update_status("Encoding video with ffmpeg...")
                self.progress_var.set(85)
                self.log("Encoding final video...")
                
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',
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
                    result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                    self.progress_var.set(100)
                    self.log(f"✓ Video created successfully!")
                    self.log(f"Output: {output_path}")
                    self.update_status("Complete!")
                    
                    if messagebox.askyesno("Success!", f"Video created successfully!\n\nOpen containing folder?"):
                        subprocess.run(['explorer', '/select,', output_path])
                        
                except subprocess.CalledProcessError as e:
                    self.log(f"FFmpeg error: {e.stderr}", is_error=True)
                    raise Exception(f"FFmpeg encoding failed: {e.stderr}")
                    
        except Exception as e:
            self.log(f"Error: {str(e)}", is_error=True)
            self.update_status(f"Error: {str(e)}", is_error=True)
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
            
        finally:
            # Cleanup
            self.log("Cleaning up temporary files...")
            try:
                if os.path.exists(temp_dir):
                    for f in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, f))
                    os.rmdir(temp_dir)
            except:
                pass
                
            # Reset UI to ready state
            self.reset_ui_state()
            
    def show_help(self):
        help_text = """
🎵 AI Cover Visualizer - Help

1. Select your audio file (MP3, WAV, etc.)
2. Select your center image (PNG, JPG, etc.)
3. Choose output location
4. Adjust settings or use a preset
5. Click "Start Rendering"

📐 Presets:
• YouTube: 1920x1080, landscape
• TikTok: 1080x1920, portrait (9:16)
• Instagram: 1080x1080, square

⚙️ Settings:
• Resolution: Video dimensions
• Frame Rate: Higher = smoother
• Visualizer Bars: More bars = finer frequency detail
• Glow Intensity: Brightness of the glow effect

⏱️ Rendering time depends on:
• Song length
• Resolution
• Frame rate
• Your CPU speed

⚠️ Don't close the window while rendering!
        """
        messagebox.showinfo("Help", help_text)


def main():
    root = tk.Tk()
    app = VisualizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
