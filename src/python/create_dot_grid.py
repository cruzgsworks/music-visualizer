#!/usr/bin/env python3
"""
Dot Grid Background Generator
Creates a technical dot grid pattern background similar to graph paper
"""

from PIL import Image, ImageDraw
import argparse


def create_dot_grid(width, height, dot_color=(45, 45, 60), bg_color=(15, 15, 25), 
                   spacing=50, dot_size=2, output_path="dot_grid_background.png"):
    """
    Create a dot grid background pattern
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        dot_color: RGB tuple for dot color (default: subtle gray-blue)
        bg_color: RGB tuple for background color (default: dark blue-black)
        spacing: Distance between dots in pixels
        dot_size: Radius of each dot in pixels
        output_path: Path to save the image
    """
    # Create base image with background color
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw dot grid
    for x in range(0, width, spacing):
        for y in range(0, height, spacing):
            # Draw small dot
            draw.ellipse(
                [x - dot_size, y - dot_size, x + dot_size, y + dot_size], 
                fill=dot_color
            )
    
    # Save the image
    img.save(output_path)
    print(f"✅ Dot grid background saved to: {output_path}")
    print(f"   Resolution: {width}x{height}")
    print(f"   Grid spacing: {spacing}px")
    print(f"   Dot size: {dot_size}px")
    
    return img


def main():
    parser = argparse.ArgumentParser(description='Generate dot grid background pattern')
    parser.add_argument('--width', type=int, default=1920, help='Image width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Image height (default: 1080)')
    parser.add_argument('--spacing', type=int, default=50, help='Grid spacing in pixels (default: 50)')
    parser.add_argument('--dot-size', type=int, default=2, help='Dot radius in pixels (default: 2)')
    parser.add_argument('--output', default='dot_grid_background.png', help='Output file path')
    
    args = parser.parse_args()
    
    print("🎨 Generating dot grid background...")
    print()
    
    create_dot_grid(
        width=args.width,
        height=args.height,
        spacing=args.spacing,
        dot_size=args.dot_size,
        output_path=args.output
    )


if __name__ == "__main__":
    main()
