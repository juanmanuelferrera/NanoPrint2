#!/usr/bin/env python3
"""Debug square placement issues from exe 17."""

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

def test_debug_square_placement():
    """Debug square placement issues."""
    setup_logging()
    
    # Use real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]
    print(f"DEBUG SQUARE PLACEMENT - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test current zero-waste square
    print(f"\n🔍 DEBUGGING Zero-Waste Square Algorithm")
    print("-" * 50)
    
    spec = EnvelopeSpec(shape=EnvelopeShape.SQUARE)
    result = packer.pack(len(image_bins), spec)
    
    canvas_size = result.canvas_width
    cols = canvas_size // 1300
    rows = canvas_size // 1900
    total_capacity = cols * rows
    
    print(f"Canvas: {canvas_size}x{canvas_size}")
    print(f"Grid capacity: {cols}x{rows} = {total_capacity} slots")
    print(f"Images needed: {len(image_bins)} slots")
    print(f"Unused slots: {total_capacity - len(image_bins)}")
    
    # Analyze placement pattern
    print(f"\n📍 PLACEMENT ANALYSIS:")
    print(f"Total placements: {len(result.placements)}")
    
    # Check first 10 and last 10 placements
    print(f"\nFirst 10 placements:")
    for i in range(min(10, len(result.placements))):
        x, y = result.placements[i]
        row = y // 1900
        col = x // 1300
        print(f"  Image {i+1}: ({x}, {y}) -> Grid ({col}, {row})")
    
    print(f"\nLast 10 placements:")
    start_idx = max(0, len(result.placements) - 10)
    for i in range(start_idx, len(result.placements)):
        x, y = result.placements[i]
        row = y // 1900
        col = x // 1300
        print(f"  Image {i+1}: ({x}, {y}) -> Grid ({col}, {row})")
    
    # Check for empty rows
    occupied_rows = set()
    for x, y in result.placements:
        row = y // 1900
        occupied_rows.add(row)
    
    print(f"\n🔢 ROW ANALYSIS:")
    print(f"Total grid rows: {rows}")
    print(f"Occupied rows: {len(occupied_rows)}")
    print(f"Empty rows: {rows - len(occupied_rows)}")
    print(f"Row range: {min(occupied_rows) if occupied_rows else 'N/A'} to {max(occupied_rows) if occupied_rows else 'N/A'}")
    
    # Calculate actual grid dimensions needed
    actual_cols = math.ceil(math.sqrt(len(image_bins)))
    actual_rows = math.ceil(len(image_bins) / actual_cols)
    optimal_width = actual_cols * 1300
    optimal_height = actual_rows * 1900
    optimal_canvas = max(optimal_width, optimal_height)
    
    print(f"\n💡 OPTIMAL CALCULATION:")
    print(f"Optimal grid: {actual_cols}x{actual_rows}")
    print(f"Optimal canvas: {optimal_canvas}x{optimal_canvas}")
    print(f"Current canvas: {canvas_size}x{canvas_size}")
    print(f"Size difference: {canvas_size - optimal_canvas} pixels")
    
    # Test with corrected algorithm
    print(f"\n🔧 TESTING CORRECTED ALGORITHM:")
    print("-" * 50)
    
    # Manual calculation
    test_cols = actual_cols
    test_rows = actual_rows
    test_width = test_cols * 1300
    test_height = test_rows * 1900
    test_canvas = max(test_width, test_height)
    
    print(f"Corrected grid: {test_cols}x{test_rows}")
    print(f"Grid dimensions: {test_width}x{test_height}")
    print(f"Square canvas: {test_canvas}x{test_canvas}")
    
    # Calculate efficiency
    image_area = len(image_bins) * 1300 * 1900
    current_efficiency = (image_area / (canvas_size * canvas_size)) * 100
    optimal_efficiency = (image_area / (test_canvas * test_canvas)) * 100
    
    print(f"\nEfficiency comparison:")
    print(f"Current: {current_efficiency:.1f}%")
    print(f"Optimal: {optimal_efficiency:.1f}%")
    print(f"Difference: {optimal_efficiency - current_efficiency:+.1f} percentage points")
    
    return result

if __name__ == "__main__":
    test_debug_square_placement()