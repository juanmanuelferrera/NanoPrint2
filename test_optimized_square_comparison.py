#!/usr/bin/env python3
"""Test optimized square vs original - maximum efficiency comparison."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.logger import setup_logging
from PIL import Image
import glob
import math

def test_optimized_square_comparison():
    """Compare optimized square with reserve vs pure optimized square."""
    setup_logging()
    
    # Use real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]
    print(f"OPTIMIZED SQUARE COMPARISON - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    image_area = len(image_bins) * 1300 * 1900
    
    # Test 1: Current optimized square with reserve
    print(f"\n🟩 Current Square with Optimized Reserve")
    print("-" * 50)
    
    spec_with_reserve = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True
    )
    
    result_with_reserve = packer.pack(len(image_bins), spec_with_reserve)
    area_with_reserve = result_with_reserve.canvas_width * result_with_reserve.canvas_height
    efficiency_with_reserve = (image_area / area_with_reserve) * 100
    
    print(f"Canvas: {result_with_reserve.canvas_width}x{result_with_reserve.canvas_height}")
    print(f"Reserve: {spec_with_reserve.reserve_width}x{spec_with_reserve.reserve_height}")
    print(f"Total area: {area_with_reserve:,} pixels²")
    print(f"Efficiency: {efficiency_with_reserve:.1f}%")
    
    # Test 2: Pure optimized square (no reserve)
    print(f"\n🔥 Maximum Optimized Square (No Reserve)")
    print("-" * 50)
    
    spec_pure = EnvelopeSpec(shape=EnvelopeShape.SQUARE)
    
    result_pure = packer.pack(len(image_bins), spec_pure)
    area_pure = result_pure.canvas_width * result_pure.canvas_height
    efficiency_pure = (image_area / area_pure) * 100
    
    print(f"Canvas: {result_pure.canvas_width}x{result_pure.canvas_height}")
    print(f"Total area: {area_pure:,} pixels²")
    print(f"Efficiency: {efficiency_pure:.1f}%")
    
    # Comparison
    print(f"\n📊 COMPARISON RESULTS")
    print("=" * 60)
    print(f"{'Method':<30} {'Efficiency':<12} {'Canvas':<15} {'Area'}")
    print("-" * 60)
    print(f"{'With Reserve (current)':<30} {efficiency_with_reserve:<11.1f}% {result_with_reserve.canvas_width}x{result_with_reserve.canvas_height:<7} {area_with_reserve:,}")
    print(f"{'Pure Optimized':<30} {efficiency_pure:<11.1f}% {result_pure.canvas_width}x{result_pure.canvas_height:<7} {area_pure:,}")
    
    improvement = efficiency_pure - efficiency_with_reserve
    area_reduction = area_with_reserve - area_pure
    
    print(f"\n🚀 OPTIMIZATION GAINS:")
    print(f"   Efficiency improvement: +{improvement:.1f} percentage points")
    print(f"   Area reduction: {area_reduction:,} pixels² ({((area_reduction/area_with_reserve)*100):.1f}%)")
    print(f"   Canvas reduction: {result_with_reserve.canvas_width - result_pure.canvas_width} pixels")
    
    if efficiency_pure > efficiency_with_reserve:
        print(f"\n🏆 WINNER: Pure Optimized Square")
        print(f"   Best efficiency: {efficiency_pure:.1f}%")
    else:
        print(f"\n🏆 WINNER: Square with Reserve")
        print(f"   Best efficiency: {efficiency_with_reserve:.1f}%")
    
    return result_with_reserve, result_pure

if __name__ == "__main__":
    test_optimized_square_comparison()