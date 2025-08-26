#!/usr/bin/env python3
"""Test ellipse with 1034 numbered images to verify layout order."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.renderer import NanoFicheRenderer
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.logger import setup_logging
from PIL import Image
import glob
import re

def test_ellipse_numbered():
    """Test ellipse with numbered images to verify layout order."""
    setup_logging()
    
    # Use numbered test images
    dataset_path = Path("numbered_test_images")
    if not dataset_path.exists():
        print("Numbered test images not found! Run generate_numbered_test_images.py first")
        return
        
    def natural_sort_key(path):
        """Extract numeric part from filename for proper sorting."""
        filename = os.path.basename(path)
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[-1])
        return 0
    
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")), key=natural_sort_key)[:1034]
    print(f"ELLIPSE NUMBERED IMAGE TEST - {len(image_files)} numbered images")
    print("=" * 60)
    
    # Verify first and last files
    print(f"First image: {os.path.basename(image_files[0])}")
    print(f"Last image: {os.path.basename(image_files[-1])}")
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1000, bin_height=1290)  # Match 1:1.29 aspect ratio
    
    # Test ellipse with 3:2 aspect ratio
    print(f"\n🟢 Testing Ellipse with {len(image_bins)} Numbered Images (3:2 aspect ratio)")
    print("-" * 50)
    
    spec = EnvelopeSpec(
        shape=EnvelopeShape.ELLIPSE,
        aspect_x=3.0,
        aspect_y=2.0
    )
    
    result = packer.pack(len(image_bins), spec)
    
    canvas_width = result.canvas_width
    canvas_height = result.canvas_height
    aspect_ratio = canvas_width / canvas_height
    
    print(f"Canvas: {canvas_width}x{canvas_height}")
    print(f"Aspect ratio: {aspect_ratio:.2f}:1")
    print(f"Images placed: {len(result.placements)}")
    print(f"Target images: {len(image_bins)}")
    
    # Calculate efficiency
    image_area = len(image_bins) * 1000 * 1290
    ellipse_area = 3.14159 * (canvas_width/2) * (canvas_height/2)
    efficiency = (image_area / ellipse_area) * 100
    
    print(f"Efficiency: {efficiency:.1f}%")
    
    # Check layout pattern - show which numbers are where
    print(f"\n📍 LAYOUT ORDER VERIFICATION:")
    print("First 10 images (should be 1-10 in raster order):")
    for i in range(min(10, len(result.placements))):
        x, y = result.placements[i]
        image_number = i + 1  # Since we're using sorted files
        print(f"  Position {i+1}: Image #{image_number} at ({x}, {y})")
    
    print("\nLast 10 images (should be 1025-1034):")
    for i in range(max(0, len(result.placements)-10), len(result.placements)):
        x, y = result.placements[i]
        image_number = i + 1
        print(f"  Position {i+1}: Image #{image_number} at ({x}, {y})")
    
    # Generate preview with numbered images
    print(f"\n🎨 GENERATING NUMBERED ELLIPSE PREVIEW")
    print("-" * 50)
    
    renderer = NanoFicheRenderer()
    preview_path = Path("ellipse_numbered_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result,
        output_path=preview_path,
        max_dimension=2500,  # Higher resolution to see numbers clearly
        color=True
    )
    
    print(f"Preview saved: {preview_path}")
    print(f"Shows: {len(image_bins)} numbered images in ellipse")
    print(f"You can now see the exact order: 1,2,3... filling row-by-row")
    print(f"Efficiency: {efficiency:.1f}% packing")
    
    return result, preview_path

if __name__ == "__main__":
    result, preview_path = test_ellipse_numbered()
    
    # Copy to clipboard
    import subprocess
    abs_path = os.path.abspath(preview_path)
    subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as TIFF picture)'])
    print(f"\n📋 Numbered ellipse layout copied to clipboard!")
    print(f"You can now see exactly how images 1-1034 are laid out in the ellipse!")