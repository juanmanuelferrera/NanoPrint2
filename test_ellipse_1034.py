#!/usr/bin/env python3
"""Test ellipse with 1034 images - row-by-row raster fill."""

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

def test_ellipse_1034():
    """Test ellipse with 1034 images using row-by-row raster fill."""
    setup_logging()
    
    # Use full 1034 images as requested
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    import re
    
    def natural_sort_key(path):
        """Extract numeric part from filename for proper sorting."""
        filename = os.path.basename(path)
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[-1])
        return 0
    
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")), key=natural_sort_key)[:1034]
    print(f"ELLIPSE RASTER FILL TEST - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test ellipse with 3:2 aspect ratio (wide ellipse)
    print(f"\n🟢 Testing Ellipse with 1034 Images (3:2 aspect ratio)")
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
    image_area = len(image_bins) * 1300 * 1900
    ellipse_area = 3.14159 * (canvas_width/2) * (canvas_height/2)
    efficiency = (image_area / ellipse_area) * 100
    
    print(f"Efficiency: {efficiency:.1f}%")
    
    # Check raster fill pattern
    print(f"\n📍 RASTER FILL PATTERN (First 5 and Last 5):")
    for i in range(5):
        x, y = result.placements[i]
        print(f"  Image {i+1}: ({x}, {y})")
    
    print("  ...")
    
    for i in range(len(result.placements)-5, len(result.placements)):
        x, y = result.placements[i]
        print(f"  Image {i+1}: ({x}, {y})")
    
    # Generate preview with ellipse boundary
    print(f"\n🎨 GENERATING 1034 ELLIPSE PREVIEW")
    print("-" * 50)
    
    renderer = NanoFicheRenderer()
    preview_path = Path("ellipse_1034_raster_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result,
        output_path=preview_path,
        max_dimension=2000,  # Higher resolution for 1034 images
        color=True
    )
    
    print(f"Preview saved: {preview_path}")
    print(f"Shows: {len(image_bins)} images in ellipse with blue boundary")
    print(f"Pattern: Row-by-row raster fill (top-to-bottom, left-to-right)")
    print(f"Aspect: {aspect_ratio:.1f}:1 ellipse shape")
    
    return result, preview_path

if __name__ == "__main__":
    result, preview_path = test_ellipse_1034()
    
    # Copy to clipboard
    import subprocess
    abs_path = os.path.abspath(preview_path)
    subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as TIFF picture)'])
    print(f"\n📋 1034-image ellipse with blue boundary copied to clipboard!")
    print(f"You should now see a proper ellipse shape with row-by-row filling.")