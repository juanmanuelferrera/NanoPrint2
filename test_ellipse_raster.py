#!/usr/bin/env python3
"""Test ellipse raster fill algorithm."""

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

def test_ellipse_raster():
    """Test ellipse with row-by-row raster fill."""
    setup_logging()
    
    # Use subset for testing
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:150]  
    print(f"ELLIPSE RASTER FILL TEST - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test ellipse with 2:1 aspect ratio (wide)
    print(f"\n🟢 Testing Ellipse Raster Fill (2:1 aspect ratio)")
    print("-" * 50)
    
    spec = EnvelopeSpec(
        shape=EnvelopeShape.ELLIPSE,
        aspect_x=2.0,
        aspect_y=1.0
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
    image_area = len(image_bins) * 1300 * 1900
    ellipse_area = 3.14159 * (canvas_width/2) * (canvas_height/2)
    efficiency = (image_area / ellipse_area) * 100
    
    print(f"Efficiency: {efficiency:.1f}%")
    
    # Check raster fill pattern
    print(f"\n📍 RASTER FILL PATTERN CHECK:")
    print(f"First 10 placements (should start from top-left):")
    for i in range(min(10, len(result.placements))):
        x, y = result.placements[i]
        print(f"  Image {i+1}: ({x}, {y})")
    
    print(f"\nLast 10 placements:")
    for i in range(max(0, len(result.placements)-10), len(result.placements)):
        x, y = result.placements[i]
        print(f"  Image {i+1}: ({x}, {y})")
    
    # Generate preview
    print(f"\n🎨 GENERATING ELLIPSE RASTER PREVIEW")
    print("-" * 50)
    
    renderer = NanoFicheRenderer()
    preview_path = Path("ellipse_raster_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result,
        output_path=preview_path,
        max_dimension=1500,
        color=True
    )
    
    print(f"Preview saved: {preview_path}")
    print(f"Shows: {len(image_bins)} images in ellipse with row-by-row raster fill")
    print(f"Pattern: Top-to-bottom, left-to-right filling")
    
    return result, preview_path

if __name__ == "__main__":
    result, preview_path = test_ellipse_raster()
    
    # Copy to clipboard
    import subprocess
    abs_path = os.path.abspath(preview_path)
    subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as TIFF picture)'])
    print(f"\n📋 Ellipse raster fill preview copied to clipboard!")
    print(f"You can now see the proper row-by-row filling pattern starting from top available space.")