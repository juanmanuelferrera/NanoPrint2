#!/usr/bin/env python3
"""Test circle with 1034 images and 10000x10000 reserve - compare with last week."""

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

def test_circle_1034_comparison():
    """Test circle with 1034 images - match last week's parameters."""
    setup_logging()
    
    # Use real dataset - same as last week
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]
    print(f"Testing with {len(image_files)} TIF images (same as last week)")
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    # Create packer with same bin dimensions as last week
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test with exact same parameters as your successful image from last week
    print("\n=== Integrated Circle Test (This Week) ===")
    spec = EnvelopeSpec(
        shape=EnvelopeShape.CIRCLE,
        reserve_enabled=True,
        reserve_width=10000,   # Same as last week
        reserve_height=10000,  # Same as last week  
        reserve_position="center"  # Same as last week
    )
    
    result = packer.pack(len(image_bins), spec)
    
    # Calculate results
    diameter = result.canvas_width
    radius = diameter / 2
    circle_area = math.pi * radius * radius
    image_area = len(image_bins) * 1300 * 1900
    efficiency = (image_area / circle_area) * 100
    
    print(f"Results:")
    print(f"  Canvas: {result.canvas_width} x {result.canvas_height}")
    print(f"  Diameter: {diameter} pixels")
    print(f"  Radius: {radius:.0f} pixels")
    print(f"  Reserved: 10000x10000 at center")
    print(f"  Images placed: {len(result.placements)}")
    print(f"  Efficiency: {efficiency:.1f}%")
    
    # Compare with your original from last week
    print(f"\n=== Comparison with Last Week ===")
    print(f"Last week (your image):")
    print(f"  Radius: ~29,427 pixels")
    print(f"  Efficiency: 93.9%")
    print(f"  Reserve: 10000x10000")
    print(f"")
    print(f"This week (integrated):")
    print(f"  Radius: {radius:.0f} pixels")
    print(f"  Efficiency: {efficiency:.1f}%")
    print(f"  Reserve: 10000x10000")
    print(f"")
    print(f"Difference:")
    print(f"  Radius: {radius - 29427:.0f} pixels ({((radius - 29427)/29427*100):+.1f}%)")
    print(f"  Efficiency: {efficiency - 93.9:.1f} percentage points")
    
    # Generate preview
    print(f"\n=== Generating Comparison Preview ===")
    renderer = NanoFicheRenderer()
    preview_path = Path("circle_1034_integrated_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result,
        output_path=preview_path,
        max_dimension=2000,
        color=True
    )
    
    print(f"Preview saved to: {preview_path}")
    print(f"")
    print(f"Visual comparison:")
    print(f"  - Blue circle boundary shows the envelope")
    print(f"  - Red square in center shows 10000x10000 reserve") 
    print(f"  - Images packed avoiding the reserved area")
    
    return result, efficiency, radius

if __name__ == "__main__":
    test_circle_1034_comparison()