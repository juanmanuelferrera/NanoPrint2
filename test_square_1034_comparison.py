#!/usr/bin/env python3
"""Test square with 1034 images - compare integrated vs original."""

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

def test_square_1034_comparison():
    """Test square with 1034 images - compare auto-optimize vs original."""
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
    
    # Test with auto-optimized reserved space (new integrated method)
    print("\n=== Integrated Square with Auto-Optimized Reserve ===")
    spec = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,   # Will be overridden by auto-optimize
        reserve_height=5000,  # Will be overridden by auto-optimize
        reserve_position="top-left",
        reserve_auto_size=True  # Key difference - auto optimization
    )
    
    result = packer.pack(len(image_bins), spec)
    
    # Calculate results
    canvas_size = result.canvas_width
    total_area = canvas_size * canvas_size
    reserve_area = spec.reserve_width * spec.reserve_height
    image_area = len(image_bins) * 1300 * 1900
    usable_area = total_area - reserve_area
    
    efficiency = (image_area / total_area) * 100
    usable_efficiency = (image_area / usable_area) * 100
    
    print(f"Results:")
    print(f"  Canvas: {result.canvas_width} x {result.canvas_height}")
    print(f"  Auto-optimized reserve: {spec.reserve_width} x {spec.reserve_height} (top-left)")
    print(f"  Images placed: {len(result.placements)}")
    print(f"  Overall efficiency: {efficiency:.1f}%")
    print(f"  Usable efficiency: {usable_efficiency:.1f}%")
    
    # Compare with original from last week's log
    print(f"\n=== Comparison with Last Week's Binary Search Square ===")
    print(f"Last week (binary search with reserve):")
    print(f"  Canvas: 52,558 x 52,558 (from log)")
    print(f"  Reserve: 1592 x 2327 (optimized)")
    print(f"  Overall efficiency: 92.5%")
    print(f"  Usable efficiency: 92.6%")
    print(f"")
    print(f"This week (integrated auto-optimize):")
    print(f"  Canvas: {canvas_size} x {canvas_size}")
    print(f"  Reserve: {spec.reserve_width} x {spec.reserve_height}")
    print(f"  Overall efficiency: {efficiency:.1f}%")
    print(f"  Usable efficiency: {usable_efficiency:.1f}%")
    print(f"")
    print(f"Difference:")
    original_canvas = 52558
    original_efficiency = 92.5
    print(f"  Canvas: {canvas_size - original_canvas:+,} pixels ({((canvas_size - original_canvas)/original_canvas*100):+.1f}%)")
    print(f"  Efficiency: {efficiency - original_efficiency:+.1f} percentage points")
    
    # Generate preview
    print(f"\n=== Generating Comparison Preview ===")
    renderer = NanoFicheRenderer()
    preview_path = Path("square_1034_integrated_preview.tif")
    
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
    print(f"  - Small red rectangle in top-left shows optimized reserve")
    print(f"  - Images fill two areas: top-right + bottom")
    print(f"  - Reserve size auto-calculated for optimal bottom row fill")
    
    return result, efficiency, spec.reserve_width, spec.reserve_height

if __name__ == "__main__":
    test_square_1034_comparison()