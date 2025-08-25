#!/usr/bin/env python3
"""Test optimized square with reserved space functionality."""

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

def test_optimized_square_reserve():
    """Test optimized square with reserve (like the original binary search test)."""
    setup_logging()
    
    # Use real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if dataset_path.exists():
        image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:100]  # Use 100 for test
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
    
    # Test 1: Fixed size reserve (current method)
    print("\n=== Test 1: Fixed 5000x5000 center reserve ===")
    spec1 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="center",
        reserve_auto_size=False
    )
    result1 = packer.pack(len(image_bins), spec1)
    print(f"Canvas: {result1.canvas_width} x {result1.canvas_height}")
    print(f"Reserve: {spec1.reserve_width} x {spec1.reserve_height} at {spec1.reserve_position}")
    print(f"Images placed: {len(result1.placements)}")
    
    # Test 2: Optimized auto-size reserve (new method)
    print("\n=== Test 2: Auto-optimized top-left reserve ===")
    spec2 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,  # Will be overridden
        reserve_height=5000,  # Will be overridden  
        reserve_position="top-left",
        reserve_auto_size=True
    )
    result2 = packer.pack(len(image_bins), spec2)
    print(f"Canvas: {result2.canvas_width} x {result2.canvas_height}")
    print(f"Optimized reserve: {spec2.reserve_width} x {spec2.reserve_height} at {spec2.reserve_position}")
    print(f"Images placed: {len(result2.placements)}")
    
    # Calculate efficiency comparison
    if result1.canvas_width > 0 and result2.canvas_width > 0:
        area1 = result1.canvas_width * result1.canvas_height
        area2 = result2.canvas_width * result2.canvas_height
        image_area = len(image_bins) * 1300 * 1900
        
        eff1 = (image_area / area1) * 100
        eff2 = (image_area / area2) * 100
        
        print(f"\nEfficiency comparison:")
        print(f"  Fixed reserve: {eff1:.1f}%")
        print(f"  Optimized reserve: {eff2:.1f}%")
        print(f"  Improvement: {eff2-eff1:.1f} percentage points")
    
    # Generate preview for optimized version
    print("\n=== Generating optimized preview ===")
    renderer = NanoFicheRenderer()
    preview_path = Path("optimized_square_reserve_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result2,
        output_path=preview_path,
        max_dimension=2000,
        color=True
    )
    
    print(f"Preview saved to: {preview_path}")
    print(f"The optimized reserve should be much smaller: {spec2.reserve_width}x{spec2.reserve_height}")
    print("Red overlay shows the optimized reserved area (top-left)")

if __name__ == "__main__":
    test_optimized_square_reserve()