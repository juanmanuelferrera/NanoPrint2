#!/usr/bin/env python3
"""Test integrated circle with reserved space functionality."""

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

def test_integrated_circle_reserve():
    """Test circle with reserve using the integrated system (like GUI would)."""
    setup_logging()
    
    # Use test images or real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if dataset_path.exists():
        image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]  # Use all 1034 images
        print(f"Using {len(image_files)} TIF images from dataset")
    else:
        # Fallback to test images
        test_path = Path("test_images")
        image_files = sorted(test_path.glob("*.png"))[:25]
        print(f"Using {len(image_files)} test images")
    
    if not image_files:
        print("No images found!")
        return
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    # Create packer
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test 1: Circle without reserve
    print("\n=== Test 1: Circle without reserve ===")
    spec1 = EnvelopeSpec(
        shape=EnvelopeShape.CIRCLE,
        reserve_enabled=False
    )
    result1 = packer.pack(len(image_bins), spec1)
    print(f"Canvas: {result1.canvas_width} x {result1.canvas_height}")
    print(f"Images placed: {len(result1.placements)}")
    
    # Test 2: Circle with 10000x10000 center reserve (like your image)
    print("\n=== Test 2: Circle with 10000x10000 center reserve ===")
    spec2 = EnvelopeSpec(
        shape=EnvelopeShape.CIRCLE,
        reserve_enabled=True,
        reserve_width=10000,
        reserve_height=10000,
        reserve_position="center"
    )
    result2 = packer.pack(len(image_bins), spec2)
    print(f"Canvas: {result2.canvas_width} x {result2.canvas_height}")
    print(f"Images placed: {len(result2.placements)}")
    print(f"Reserved: {spec2.reserve_width}x{spec2.reserve_height} at {spec2.reserve_position}")
    
    # Calculate efficiency
    if result2.canvas_width > 0:
        radius = result2.canvas_width / 2
        circle_area = 3.14159 * radius * radius
        image_area = len(image_bins) * 1300 * 1900
        efficiency = (image_area / circle_area) * 100
        print(f"Efficiency: {efficiency:.1f}%")
    
    # Generate preview for the circle with reserve
    print("\n=== Generating preview ===")
    renderer = NanoFicheRenderer()
    preview_path = Path("integrated_circle_reserve_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result2,
        output_path=preview_path,
        max_dimension=2000,
        color=True
    )
    
    print(f"Preview saved to: {preview_path}")
    print("The preview should show:")
    print("  - Blue circle boundary")
    print("  - Red reserved space in center")
    print("  - Images placed avoiding the reserved area")

if __name__ == "__main__":
    test_integrated_circle_reserve()