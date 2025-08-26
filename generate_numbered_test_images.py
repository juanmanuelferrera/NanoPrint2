#!/usr/bin/env python3
"""Generate 1034 test images with large visible numbers for testing layout order."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

def generate_numbered_images(output_dir: Path, count: int = 1034):
    """Generate numbered test images with large visible numbers."""
    
    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Image dimensions with 1:1.29 aspect ratio as requested
    width = 1000
    height = int(width * 1.29)  # 1:1.29 aspect ratio
    
    print(f"Generating {count} numbered test images...")
    print(f"Output directory: {output_dir}")
    print(f"Image size: {width}x{height}")
    print("=" * 60)
    
    # Try to use a large font
    font_size = 150
    try:
        # Try system fonts
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
            font_size = 50
    
    for i in range(1, count + 1):
        # Create image with white background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw number in large text
        number_text = str(i)
        
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), number_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw black text with white outline for visibility
        outline_width = 3
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), number_text, font=font, fill='white')
        
        # Draw main text in black
        draw.text((x, y), number_text, font=font, fill='black')
        
        # Add colored border based on number for easy identification
        border_color = f"hsl({(i * 137) % 360}, 70%, 50%)"  # Different color for each
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=5)
        
        # Save as TIF
        filename = f"{i:04d}.tif"  # Zero-padded for proper sorting
        filepath = output_dir / filename
        img.save(filepath, format='TIFF')
        
        if i % 100 == 0:
            print(f"Generated {i} images...")
    
    print(f"\n✅ Generated {count} numbered test images")
    print(f"Files: 0001.tif to {count:04d}.tif")
    print(f"Each image shows its number in large text with colored border")
    
    return output_dir

def main():
    """Main function to generate test images."""
    output_dir = Path("numbered_test_images")
    
    # Clean up existing images
    if output_dir.exists():
        print("Cleaning up existing test images...")
        for f in output_dir.glob("*.tif"):
            f.unlink()
    
    # Generate new numbered images - full 1034 set
    generate_numbered_images(output_dir, 1034)
    
    print(f"\n📁 Test images ready in: {output_dir.absolute()}")
    print("Now you can use these images to test the ellipse layout order!")

if __name__ == "__main__":
    main()