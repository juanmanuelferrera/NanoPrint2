#!/usr/bin/env python3
"""
Test script for square layout with bin size 1300x1900 and images 1251x1836.
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from nanofiche_core import NanoFichePacker, EnvelopeShape, EnvelopeSpec, ImageBin, NanoFicheRenderer
from nanofiche_core.logger import setup_logging
import logging
import os

def create_test_images_with_size(count=25, width=1251, height=1836):
    """Create test images with specific dimensions."""
    test_dir = Path("test_square_images")
    test_dir.mkdir(exist_ok=True)
    
    image_files = []
    colors = [
        (255, 200, 200), (200, 255, 200), (200, 200, 255),
        (255, 255, 200), (255, 200, 255), (200, 255, 255),
        (255, 150, 150), (150, 255, 150), (150, 150, 255),
        (255, 220, 180), (180, 255, 220), (220, 180, 255)
    ]
    
    for i in range(count):
        # Create test image with exact dimensions
        color = colors[i % len(colors)]
        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)
        
        # Draw border
        draw.rectangle([0, 0, width-1, height-1], outline='black', width=5)
        
        # Draw image number in center
        text = f"{i+1}"
        # Try to use a larger font if available
        try:
            font = ImageFont.truetype("arial.ttf", 200)
        except:
            font = ImageFont.load_default()
        
        # Draw text multiple times for visibility
        for y_offset in range(200, height-200, 300):
            draw.text((width//2 - 100, y_offset), text, fill='black', font=font)
            draw.text((width//2 - 98, y_offset + 2), text, fill='white', font=font)
        
        # Save image
        img_path = test_dir / f"image_{i+1:03d}.png"
        img.save(img_path)
        image_files.append(img_path)
        print(f"Created {img_path} ({width}x{height})")
    
    return image_files

def test_square_layout():
    """Test square layout with specified parameters."""
    setup_logging(logging.INFO)
    
    print("Testing Square Layout")
    print("=" * 50)
    print("Parameters:")
    print("  - Image size: 1251 x 1836 pixels")
    print("  - Bin size: 1300 x 1900 pixels")
    print("  - Envelope shape: Square")
    print()
    
    # Create test images with exact dimensions
    image_files = create_test_images_with_size(25, 1251, 1836)
    
    # Create image bins with bin size 1300x1900
    bin_width = 1300
    bin_height = 1900
    image_bins = [ImageBin(f, bin_width, bin_height, i) for i, f in enumerate(image_files)]
    
    # Create packer with specified bin size
    packer = NanoFichePacker(bin_width, bin_height)
    
    # Test SQUARE packing
    envelope_spec = EnvelopeSpec(EnvelopeShape.SQUARE)
    result = packer.pack(len(image_bins), envelope_spec)
    
    print(f"\nPacking Result:")
    print(f"  Grid: {result.rows} rows x {result.columns} columns")
    print(f"  Canvas size: {result.canvas_width} x {result.canvas_height} pixels")
    print(f"  Each bin: {bin_width} x {bin_height} pixels")
    print(f"  Total bins: {result.total_bins}")
    
    # Calculate actual image placement within bins
    print(f"\nImage placement:")
    print(f"  Image size: 1251 x 1836")
    print(f"  Bin size: 1300 x 1900")
    print(f"  Horizontal padding: {(bin_width - 1251) / 2:.1f} pixels on each side")
    print(f"  Vertical padding: {(bin_height - 1836) / 2:.1f} pixels on each side")
    
    # Generate preview/thumbnail
    print(f"\nGenerating preview TIFF...")
    renderer = NanoFicheRenderer()
    
    # Create output directory
    output_dir = Path("test_square_output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate preview (thumbnail)
    preview_path = output_dir / "square_layout_preview.tif"
    renderer.generate_preview(image_bins, result, preview_path, max_dimension=2000)
    print(f"  Preview saved to: {preview_path}")
    
    # Also generate a smaller thumbnail for easy viewing
    thumbnail_path = output_dir / "square_layout_thumbnail.tif"
    renderer.generate_preview(image_bins, result, thumbnail_path, max_dimension=800)
    print(f"  Thumbnail saved to: {thumbnail_path}")
    
    # Generate log file
    from nanofiche_core.logger import log_project
    from datetime import datetime
    
    log_path = output_dir / "square_layout_test.log"
    log_project(
        log_path=log_path,
        project_name="square_layout_test",
        timestamp=datetime.now(),
        bin_width=bin_width,
        bin_height=bin_height,
        envelope_shape="square",
        num_files=len(image_bins),
        output_path=preview_path,
        final_size=(result.canvas_width, result.canvas_height),
        process_time=1.0,
        approved=False,
        images_placed=len(image_bins)
    )
    print(f"  Log saved to: {log_path}")
    
    print(f"\n✅ Test complete!")
    print(f"\nYou can now view the thumbnail layout at:")
    print(f"  {thumbnail_path.absolute()}")

if __name__ == "__main__":
    test_square_layout()