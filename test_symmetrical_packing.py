#!/usr/bin/env python3
"""Test symmetrical packing with better space utilization."""

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

def test_symmetrical_packing():
    """Test improved symmetrical packing algorithm."""
    setup_logging()
    
    # Use subset for testing
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:200]  
    print(f"SYMMETRICAL PACKING TEST - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    num_images = len(image_bins)
    
    # Test current algorithm vs improved algorithm
    print(f"\n📊 COMPARING PACKING ALGORITHMS")
    print("=" * 60)
    
    # Algorithm 1: Current zero-waste (can be asymmetrical)
    print(f"\n🔹 Current Algorithm: Zero-Waste Square")
    print("-" * 50)
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    spec1 = EnvelopeSpec(shape=EnvelopeShape.SQUARE)
    result1 = packer.pack(num_images, spec1)
    
    canvas1 = result1.canvas_width
    cols1 = canvas1 // 1300
    rows1 = canvas1 // 1900
    capacity1 = cols1 * rows1
    efficiency1 = (num_images / capacity1) * 100
    
    print(f"Canvas: {canvas1}x{canvas1}")
    print(f"Grid: {cols1}x{rows1} = {capacity1} slots")
    print(f"Used: {num_images} slots ({efficiency1:.1f}% capacity)")
    print(f"Empty: {capacity1 - num_images} slots")
    
    # Algorithm 2: Symmetrical grid (balanced rows/cols)
    print(f"\n🔹 Improved Algorithm: Symmetrical Grid")
    print("-" * 50)
    
    # Calculate optimal rectangular grid
    sqrt_images = math.sqrt(num_images)
    
    # Try different grid configurations for best balance
    best_cols = None
    best_rows = None
    best_waste = float('inf')
    best_canvas = None
    
    # Test grid configurations around the square root
    for test_cols in range(int(sqrt_images), int(sqrt_images * 1.5) + 1):
        test_rows = math.ceil(num_images / test_cols)
        test_capacity = test_cols * test_rows
        test_waste = test_capacity - num_images
        
        # Calculate canvas size for square envelope
        test_width = test_cols * 1300
        test_height = test_rows * 1900
        test_canvas = max(test_width, test_height)
        
        # Prefer configurations with less waste and more balanced aspect
        grid_aspect = test_cols / test_rows
        balance_score = 1.0 / (1.0 + abs(1.0 - grid_aspect))  # Closer to 1:1 is better
        
        # Combined score: minimize waste, maximize balance
        score = test_waste - (balance_score * 5)  # Weight balance factor
        
        if score < best_waste or (score == best_waste and test_canvas < best_canvas):
            best_cols = test_cols
            best_rows = test_rows
            best_waste = test_waste
            best_canvas = test_canvas
    
    capacity2 = best_cols * best_rows
    efficiency2 = (num_images / capacity2) * 100
    
    print(f"Canvas: {best_canvas}x{best_canvas}")
    print(f"Grid: {best_cols}x{best_rows} = {capacity2} slots")
    print(f"Used: {num_images} slots ({efficiency2:.1f}% capacity)")
    print(f"Empty: {capacity2 - num_images} slots")
    print(f"Grid aspect ratio: {best_cols/best_rows:.2f}:1")
    
    # Algorithm 3: Perfectly balanced (minimize empty space)
    print(f"\n🔹 Optimized Algorithm: Minimum Waste")
    print("-" * 50)
    
    # Find configuration with absolute minimum waste
    perfect_cols = int(sqrt_images)
    perfect_rows = math.ceil(num_images / perfect_cols)
    
    # Adjust to minimize waste while keeping reasonable aspect ratio
    while (perfect_cols * perfect_rows - num_images) > (perfect_cols - 1) * math.ceil(num_images / (perfect_cols - 1)) - num_images and perfect_cols > 1:
        perfect_cols -= 1
        perfect_rows = math.ceil(num_images / perfect_cols)
    
    perfect_width = perfect_cols * 1300
    perfect_height = perfect_rows * 1900
    perfect_canvas = max(perfect_width, perfect_height)
    capacity3 = perfect_cols * perfect_rows
    efficiency3 = (num_images / capacity3) * 100
    
    print(f"Canvas: {perfect_canvas}x{perfect_canvas}")
    print(f"Grid: {perfect_cols}x{perfect_rows} = {capacity3} slots")
    print(f"Used: {num_images} slots ({efficiency3:.1f}% capacity)")
    print(f"Empty: {capacity3 - num_images} slots")
    print(f"Grid aspect ratio: {perfect_cols/perfect_rows:.2f}:1")
    
    # Generate visual comparison
    print(f"\n🎨 GENERATING VISUAL COMPARISON")
    print("=" * 60)
    
    # Create mock result for symmetrical algorithm
    class MockSymmetricalResult:
        def __init__(self, cols, rows, canvas_size, num_images):
            self.columns = cols
            self.rows = rows
            self.canvas_width = canvas_size
            self.canvas_height = canvas_size
            self.envelope_shape = EnvelopeShape.SQUARE
            self.total_bins = num_images
            self.bin_width = 1300
            self.bin_height = 1900
            self.envelope_spec = None
            
            # Generate centered placements
            grid_width = cols * 1300
            grid_height = rows * 1900
            offset_x = (canvas_size - grid_width) // 2
            offset_y = (canvas_size - grid_height) // 2
            
            self.placements = []
            for i in range(num_images):
                row = i // cols
                col = i % cols
                x = offset_x + col * 1300
                y = offset_y + row * 1900
                self.placements.append((x, y))
    
    symmetrical_result = MockSymmetricalResult(best_cols, best_rows, best_canvas, num_images)
    
    # Generate preview of symmetrical version
    renderer = NanoFicheRenderer()
    preview_path = Path("symmetrical_packing_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=symmetrical_result,
        output_path=preview_path,
        max_dimension=1500,
        color=True
    )
    
    print(f"Symmetrical preview saved: {preview_path}")
    
    # Summary comparison
    print(f"\n📈 ALGORITHM COMPARISON")
    print("=" * 60)
    print(f"{'Algorithm':<20} {'Canvas':<12} {'Grid':<10} {'Empty':<6} {'Efficiency'}")
    print("-" * 60)
    print(f"{'Current':<20} {canvas1:<11} {cols1}x{rows1:<6} {capacity1-num_images:<5} {efficiency1:.1f}%")
    print(f"{'Symmetrical':<20} {best_canvas:<11} {best_cols}x{best_rows:<6} {capacity2-num_images:<5} {efficiency2:.1f}%")
    print(f"{'Optimized':<20} {perfect_canvas:<11} {perfect_cols}x{perfect_rows:<6} {capacity3-num_images:<5} {efficiency3:.1f}%")
    
    # Choose best algorithm
    algorithms = [
        ("Current", canvas1, efficiency1),
        ("Symmetrical", best_canvas, efficiency2),
        ("Optimized", perfect_canvas, efficiency3)
    ]
    
    best_algorithm = min(algorithms, key=lambda x: x[1])  # Smallest canvas wins
    
    print(f"\n🏆 BEST ALGORITHM: {best_algorithm[0]}")
    print(f"   Canvas size: {best_algorithm[1]}x{best_algorithm[1]}")
    print(f"   Efficiency: {best_algorithm[2]:.1f}%")
    
    return symmetrical_result, preview_path

if __name__ == "__main__":
    result, preview_path = test_symmetrical_packing()
    
    # Copy to clipboard
    import subprocess
    abs_path = os.path.abspath(preview_path)
    subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as TIFF picture)'])
    print(f"\n📋 Symmetrical preview copied to clipboard!")
    print(f"Compare with the previous image to see improved symmetry and space utilization.")