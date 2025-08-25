#!/usr/bin/env python3
"""Test square with center vs top-left reserved space positioning."""

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
import math

def test_square_center_vs_topleft():
    """Test square with center vs top-left reserved space."""
    setup_logging()
    
    # Use real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]
    print(f"Testing square positioning with {len(image_files)} TIF images")
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    # Create packer
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test 1: Top-left reserve (optimized version we just tested)
    print("\n=== Test 1: Top-Left Reserve with Auto-Optimize ===")
    spec1 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True  # Auto optimization
    )
    
    result1 = packer.pack(len(image_bins), spec1)
    area1 = result1.canvas_width * result1.canvas_height
    image_area = len(image_bins) * 1300 * 1900
    efficiency1 = (image_area / area1) * 100
    
    print(f"  Canvas: {result1.canvas_width} x {result1.canvas_height}")
    print(f"  Optimized reserve: {spec1.reserve_width} x {spec1.reserve_height}")
    print(f"  Images placed: {len(result1.placements)}")
    print(f"  Efficiency: {efficiency1:.1f}%")
    
    # Test 2: Center reserve (like circle)
    print("\n=== Test 2: Center Reserve (Fixed Size) ===")
    spec2 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=10000,  # Same as circle test
        reserve_height=10000,
        reserve_position="center",
        reserve_auto_size=False  # Fixed size like circle
    )
    
    result2 = packer.pack(len(image_bins), spec2)
    area2 = result2.canvas_width * result2.canvas_height
    efficiency2 = (image_area / area2) * 100
    
    print(f"  Canvas: {result2.canvas_width} x {result2.canvas_height}")
    print(f"  Fixed reserve: {spec2.reserve_width} x {spec2.reserve_height}")
    print(f"  Images placed: {len(result2.placements)}")
    print(f"  Efficiency: {efficiency2:.1f}%")
    
    # Test 3: Center reserve with smaller size
    print("\n=== Test 3: Center Reserve (Smaller Size) ===")
    spec3 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,  # Smaller reserve
        reserve_height=5000,
        reserve_position="center",
        reserve_auto_size=False
    )
    
    result3 = packer.pack(len(image_bins), spec3)
    area3 = result3.canvas_width * result3.canvas_height
    efficiency3 = (image_area / area3) * 100
    
    print(f"  Canvas: {result3.canvas_width} x {result3.canvas_height}")
    print(f"  Fixed reserve: {spec3.reserve_width} x {spec3.reserve_height}")
    print(f"  Images placed: {len(result3.placements)}")
    print(f"  Efficiency: {efficiency3:.1f}%")
    
    # Comparison
    print(f"\n=== Position Comparison ===")
    print(f"Top-left optimized:  {efficiency1:.1f}% (canvas: {result1.canvas_width})")
    print(f"Center 10000x10000:  {efficiency2:.1f}% (canvas: {result2.canvas_width})")
    print(f"Center 5000x5000:   {efficiency3:.1f}% (canvas: {result3.canvas_width})")
    
    # Generate preview for center reserve
    print(f"\n=== Generating Center Reserve Preview ===")
    renderer = NanoFicheRenderer()
    preview_path = Path("square_center_reserve_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result2,  # Use the 10000x10000 center version
        output_path=preview_path,
        max_dimension=2000,
        color=True
    )
    
    print(f"Preview saved to: {preview_path}")
    print(f"Shows: 1034 images with 10000x10000 red square in center")
    
    return result1, result2, result3

if __name__ == "__main__":
    test_square_center_vs_topleft()