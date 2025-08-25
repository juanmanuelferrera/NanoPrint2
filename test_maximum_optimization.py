#!/usr/bin/env python3
"""Maximum optimization test - push all algorithms to theoretical limits."""

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

def test_maximum_optimization():
    """Test maximum optimization across all envelope types."""
    setup_logging()
    
    # Use real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]
    print(f"MAXIMUM OPTIMIZATION TEST with {len(image_files)} TIF images")
    print("=" * 70)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    # Create packer
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    image_area = len(image_bins) * 1300 * 1900
    
    # Test 1: Circle with optimized reserve (current best)
    print(f"\n🔴 CIRCLE - Maximum Optimization")
    print("-" * 50)
    
    spec_circle = EnvelopeSpec(
        shape=EnvelopeShape.CIRCLE,
        reserve_enabled=True,
        reserve_width=10000,
        reserve_height=10000,
        reserve_position="center",
        reserve_auto_size=False
    )
    
    result_circle = packer.pack(len(image_bins), spec_circle)
    
    # Calculate theoretical minimum circle area
    theoretical_circle_area = image_area + (10000 * 10000)  # Images + reserve
    theoretical_circle_radius = math.sqrt(theoretical_circle_area / math.pi)
    actual_circle_area = math.pi * (result_circle.canvas_width / 2) ** 2
    circle_efficiency = (image_area / actual_circle_area) * 100
    theoretical_efficiency = (image_area / theoretical_circle_area) * 100
    
    print(f"Theoretical minimum radius: {theoretical_circle_radius:.0f}px")
    print(f"Actual radius: {result_circle.canvas_width // 2}px")
    print(f"Efficiency: {circle_efficiency:.1f}%")
    print(f"Theoretical max efficiency: {theoretical_efficiency:.1f}%")
    print(f"Efficiency ratio: {circle_efficiency/theoretical_efficiency:.3f}")
    
    # Test 2: Square with perfect optimization (current best)
    print(f"\n🟩 SQUARE - Maximum Optimization")
    print("-" * 50)
    
    spec_square = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True
    )
    
    result_square = packer.pack(len(image_bins), spec_square)
    
    square_area = result_square.canvas_width * result_square.canvas_height
    square_efficiency = (image_area / square_area) * 100
    
    print(f"Canvas: {result_square.canvas_width}x{result_square.canvas_height}")
    print(f"Optimized reserve: {spec_square.reserve_width}x{spec_square.reserve_height}")
    print(f"Efficiency: {square_efficiency:.1f}%")
    
    # Test 3: Rectangle with optimal aspect ratio
    print(f"\n🟨 RECTANGLE - Optimal Aspect Ratio")
    print("-" * 50)
    
    # Calculate optimal rectangle aspect ratio for maximum efficiency
    sqrt_images = math.sqrt(len(image_bins))
    optimal_cols = math.ceil(sqrt_images)
    optimal_rows = math.ceil(len(image_bins) / optimal_cols)
    optimal_aspect = (optimal_cols * 1300) / (optimal_rows * 1900)
    
    spec_rect = EnvelopeSpec(
        shape=EnvelopeShape.RECTANGLE,
        aspect_x=optimal_aspect,
        aspect_y=1.0
    )
    
    result_rect = packer.pack(len(image_bins), spec_rect)
    
    rect_area = result_rect.canvas_width * result_rect.canvas_height
    rect_efficiency = (image_area / rect_area) * 100
    
    print(f"Optimal aspect ratio: {optimal_aspect:.3f}:1")
    print(f"Canvas: {result_rect.canvas_width}x{result_rect.canvas_height}")
    print(f"Efficiency: {rect_efficiency:.1f}%")
    
    # Test 4: No envelope (pure grid) - theoretical maximum
    print(f"\n⬜ NO ENVELOPE - Theoretical Maximum")
    print("-" * 50)
    
    pure_cols = math.ceil(math.sqrt(len(image_bins)))
    pure_rows = math.ceil(len(image_bins) / pure_cols)
    pure_width = pure_cols * 1300
    pure_height = pure_rows * 1900
    pure_area = pure_width * pure_height
    pure_efficiency = (image_area / pure_area) * 100
    
    print(f"Grid: {pure_cols}x{pure_rows}")
    print(f"Canvas: {pure_width}x{pure_height}")
    print(f"Efficiency: {pure_efficiency:.1f}% (theoretical maximum)")
    
    # Test 5: Advanced square with minimal waste
    print(f"\n🔥 ADVANCED SQUARE - Zero Waste Optimization")
    print("-" * 50)
    
    # Calculate exact capacity needed
    exact_capacity = len(image_bins)
    
    # Find square size that gives exactly the needed capacity
    side_length = 1
    while True:
        cols = side_length // 1300
        rows = side_length // 1900
        capacity = cols * rows
        
        if capacity >= exact_capacity:
            break
        side_length += 1
    
    # Fine-tune to minimize area while maintaining capacity
    optimal_side = side_length
    while True:
        test_side = optimal_side - 1
        test_cols = test_side // 1300
        test_rows = test_side // 1900
        test_capacity = test_cols * test_rows
        
        if test_capacity < exact_capacity:
            break
        optimal_side = test_side
    
    advanced_area = optimal_side * optimal_side
    advanced_efficiency = (image_area / advanced_area) * 100
    
    print(f"Zero-waste canvas: {optimal_side}x{optimal_side}")
    print(f"Efficiency: {advanced_efficiency:.1f}%")
    
    # Summary
    print(f"\n📊 MAXIMUM OPTIMIZATION SUMMARY")
    print("=" * 70)
    print(f"{'Algorithm':<25} {'Efficiency':<12} {'Canvas Size':<15} {'Area':<15}")
    print("-" * 70)
    print(f"{'Circle (reserve)':<25} {circle_efficiency:<11.1f}% {result_circle.canvas_width}px diam {actual_circle_area:<14.0f}")
    print(f"{'Square (optimized)':<25} {square_efficiency:<11.1f}% {result_square.canvas_width}x{result_square.canvas_height:<7} {square_area:<14.0f}")
    print(f"{'Rectangle (optimal)':<25} {rect_efficiency:<11.1f}% {result_rect.canvas_width}x{result_rect.canvas_height:<7} {rect_area:<14.0f}")
    print(f"{'Pure Grid':<25} {pure_efficiency:<11.1f}% {pure_width}x{pure_height:<7} {pure_area:<14.0f}")
    print(f"{'Advanced Square':<25} {advanced_efficiency:<11.1f}% {optimal_side}x{optimal_side:<7} {advanced_area:<14.0f}")
    
    # Find the winner
    results = [
        ("Circle (reserve)", circle_efficiency, actual_circle_area),
        ("Square (optimized)", square_efficiency, square_area),
        ("Rectangle (optimal)", rect_efficiency, rect_area),
        ("Pure Grid", pure_efficiency, pure_area),
        ("Advanced Square", advanced_efficiency, advanced_area)
    ]
    
    best_result = max(results, key=lambda x: x[1])
    
    print(f"\n🏆 MAXIMUM OPTIMIZATION WINNER: {best_result[0]}")
    print(f"   Efficiency: {best_result[1]:.1f}%")
    print(f"   Area: {best_result[2]:,.0f} pixels²")
    
    return results

if __name__ == "__main__":
    test_maximum_optimization()