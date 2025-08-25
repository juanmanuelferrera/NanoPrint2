#!/usr/bin/env python3
"""Analyze square reserve optimization and bottom row fill."""

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

def analyze_square_reserve_optimization():
    """Analyze square reserve sizing and bottom row fill."""
    setup_logging()
    
    # Use real dataset
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:1034]
    print(f"Analyzing square reserve with {len(image_files)} TIF images")
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    # Create packer
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Current auto-optimized result
    print("\n=== Current Auto-Optimized Result ===")
    spec = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True
    )
    
    result = packer.pack(len(image_bins), spec)
    
    canvas_size = result.canvas_width
    reserve_w = spec.reserve_width
    reserve_h = spec.reserve_height
    
    print(f"Canvas: {canvas_size}x{canvas_size}")
    print(f"Reserve: {reserve_w}x{reserve_h}")
    
    # Calculate areas and utilization
    top_right_width = canvas_size - reserve_w
    top_right_height = reserve_h
    top_right_cols = int(top_right_width / 1300)
    top_right_rows = int(top_right_height / 1900)
    top_right_capacity = top_right_cols * top_right_rows
    
    bottom_width = canvas_size
    bottom_height = canvas_size - reserve_h
    bottom_cols = int(bottom_width / 1300)
    bottom_rows = int(bottom_height / 1900)
    bottom_capacity = bottom_cols * bottom_rows
    
    total_capacity = top_right_capacity + bottom_capacity
    
    print(f"\nArea Analysis:")
    print(f"Top-right: {top_right_cols}x{top_right_rows} = {top_right_capacity} slots")
    print(f"Bottom: {bottom_cols}x{bottom_rows} = {bottom_capacity} slots")
    print(f"Total capacity: {total_capacity} slots")
    print(f"Images needed: {len(image_bins)} slots")
    print(f"Unused slots: {total_capacity - len(image_bins)}")
    
    # Check bottom row utilization
    images_in_top = min(len(image_bins), top_right_capacity)
    images_in_bottom = len(image_bins) - images_in_top
    
    if images_in_bottom > 0:
        bottom_rows_used = math.ceil(images_in_bottom / bottom_cols)
        bottom_last_row_images = images_in_bottom % bottom_cols
        if bottom_last_row_images == 0:
            bottom_last_row_images = bottom_cols
        
        print(f"\nBottom Area Utilization:")
        print(f"Images in bottom: {images_in_bottom}")
        print(f"Bottom rows used: {bottom_rows_used} of {bottom_rows}")
        print(f"Last row images: {bottom_last_row_images} of {bottom_cols} ({(bottom_last_row_images/bottom_cols)*100:.1f}%)")
        print(f"Empty slots in last row: {bottom_cols - bottom_last_row_images}")
        
        # Calculate what reserve size would give perfect bottom row fill
        if bottom_last_row_images < bottom_cols:
            empty_slots = bottom_cols - bottom_last_row_images
            print(f"\n=== Reserve Enlargement Analysis ===")
            print(f"To fill bottom row perfectly, need to remove {empty_slots} slots from bottom")
            print(f"This could be achieved by enlarging reserve or reducing canvas slightly")
            
            # Try enlarging reserve width to remove those slots
            extra_width_needed = empty_slots * 1300
            new_reserve_width = reserve_w + extra_width_needed
            
            print(f"Option 1: Enlarge reserve width to {new_reserve_width} (+{extra_width_needed})")
            
            # Calculate new top-right capacity
            new_top_right_width = canvas_size - new_reserve_width
            new_top_right_cols = int(new_top_right_width / 1300)
            new_top_right_capacity = new_top_right_cols * top_right_rows
            new_total_capacity = new_top_right_capacity + bottom_capacity
            
            print(f"New top-right: {new_top_right_cols}x{top_right_rows} = {new_top_right_capacity}")
            print(f"New total capacity: {new_total_capacity}")
            
            if new_total_capacity >= len(image_bins):
                print(f"✓ Would still fit all {len(image_bins)} images")
                efficiency_change = ((len(image_bins) * 1300 * 1900) / (canvas_size * canvas_size)) * 100
                print(f"Efficiency would remain: {efficiency_change:.1f}%")
            else:
                print(f"✗ Would not fit all images (capacity: {new_total_capacity})")
    
    return result

if __name__ == "__main__":
    analyze_square_reserve_optimization()