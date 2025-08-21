#!/usr/bin/env python3

import sys
import os
import glob
import re
import logging
import math
from pathlib import Path

# Add the nanofiche_core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nanofiche_core'))

from nanofiche_core.logger import setup_logging

def natural_sort_key(filename):
    """Extract numeric part from filename for proper sorting (1, 2, ... 10, 11, ...)"""
    match = re.search(r'-(\d+)\.tif', filename)
    if match:
        return int(match.group(1))
    return 0

def pack_images_simple(num_bins, rect_width, rect_height, bin_width, bin_height, reserve_cols, reserve_rows):
    """Simple packing without bottom optimization."""
    placements = []
    bins_placed = 0
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    
    # Place images row by row, skipping reserved area
    for row in range(total_rows):
        if bins_placed >= num_bins:
            break
            
        for col in range(total_cols):
            if bins_placed >= num_bins:
                break
                
            # Skip reserved area (top-left)
            if row < reserve_rows and col < reserve_cols:
                continue
            
            # Calculate position
            x = col * bin_width
            y = row * bin_height
            
            # Ensure it fits within rectangle
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements, bins_placed

def analyze_placement(placements, total_cols, rect_height, bin_height):
    """Analyze placement results."""
    if not placements:
        return 0, 0, 0
    
    # Find the last row Y position
    last_row_y = max(p[1] for p in placements)
    # Count images in the last row
    bottom_row_images = sum(1 for p in placements if p[1] == last_row_y)
    # Calculate bottom empty space
    bottom_empty = rect_height - (last_row_y + bin_height)
    
    return bottom_row_images, last_row_y, bottom_empty

def test_forced_larger_reserve():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_forced_larger_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Testing forced larger reserve scenarios for {len(image_files)} images")
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Use the current optimal dimensions but make them taller to accommodate another row
    current_width = 45502.8
    current_height = 58698.6
    
    # Force taller rectangle to fit one more row
    taller_height = current_height + bin_height  # Add exactly one row height
    taller_width = taller_height * (1.0 / 1.29)  # Maintain 1:1.29 aspect ratio
    
    total_cols = int(taller_width / bin_width)
    total_rows = int(taller_height / bin_height)
    
    logger.info(f"Original rectangle: {current_width:.1f}x{current_height:.1f}")
    logger.info(f"Taller rectangle: {taller_width:.1f}x{taller_height:.1f}")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles, Total capacity: {total_rows * total_cols}")
    
    # Test different reserve sizes to see how they affect bottom row filling
    test_cases = [
        (4, 4, "Current optimal (4x4)"),
        (6, 6, "Expanded by 2 tiles (6x6)"),
        (8, 8, "Expanded by 4 tiles (8x8)"),
        (10, 10, "Very large reserve (10x10)")
    ]
    
    print(f"\nForced Larger Reserve Test (Taller Rectangle: {taller_width:.0f}x{taller_height:.0f}):")
    print(f"{'Reserve':<15} {'Images':<8} {'Bottom Row':<12} {'Last Y':<8} {'Bottom Empty':<12} {'Can Fit More?'}")
    print("-" * 85)
    
    for reserve_rows, reserve_cols, description in test_cases:
        placements, placed = pack_images_simple(
            len(image_files), taller_width, taller_height, bin_width, bin_height, reserve_cols, reserve_rows
        )
        
        if placed >= len(image_files):
            bottom_count, last_y, bottom_empty = analyze_placement(placements, total_cols, taller_height, bin_height)
            utilization = bottom_count / total_cols * 100
            can_fit_more = "YES" if bottom_empty >= bin_height else "NO"
            
            print(f"{reserve_rows}x{reserve_cols:<12} {placed:<8} {bottom_count}/{total_cols:<8} {last_y:<8} {bottom_empty:<8.0f}px   {can_fit_more}")
            
            logger.info(f"{description}:")
            logger.info(f"  Reserve: {reserve_rows}x{reserve_cols} tiles ({reserve_rows * reserve_cols} tiles)")
            logger.info(f"  Images placed: {placed}")
            logger.info(f"  Bottom row: {bottom_count}/{total_cols} ({utilization:.1f}%)")
            logger.info(f"  Last image Y: {last_y}")
            logger.info(f"  Bottom empty: {bottom_empty:.1f} pixels")
            logger.info(f"  Can fit another row: {can_fit_more}")
            
            # Calculate if expanding reserve more would help
            if reserve_rows < 12:  # Test one level bigger
                bigger_reserve_rows = reserve_rows + 2
                bigger_reserve_cols = reserve_cols + 2
                bigger_placements, bigger_placed = pack_images_simple(
                    len(image_files), taller_width, taller_height, bin_width, bin_height, 
                    bigger_reserve_cols, bigger_reserve_rows
                )
                
                if bigger_placed >= len(image_files):
                    bigger_bottom_count, bigger_last_y, bigger_bottom_empty = analyze_placement(
                        bigger_placements, total_cols, taller_height, bin_height
                    )
                    
                    logger.info(f"  With {bigger_reserve_rows}x{bigger_reserve_cols} reserve:")
                    logger.info(f"    Bottom row: {bigger_bottom_count}/{total_cols}")
                    logger.info(f"    Bottom empty: {bigger_bottom_empty:.1f} pixels")
                    logger.info(f"    Improvement: {bigger_bottom_count - bottom_count} more images in bottom row")
            
            # Calculate overall efficiency
            total_area = taller_width * taller_height
            reserve_area = reserve_cols * bin_width * reserve_rows * bin_height
            image_area = len(image_files) * bin_width * bin_height
            overall_efficiency = image_area / total_area * 100
            
            logger.info(f"  Overall efficiency: {overall_efficiency:.1f}%")
            print()
        else:
            print(f"{reserve_rows}x{reserve_cols:<12} {placed:<8} {'FAIL':<12} {'N/A':<8} {'N/A':<12} {'N/A'}")
            logger.info(f"{description}: FAILED - only {placed}/{len(image_files)} images fit")
            print()

if __name__ == "__main__":
    test_forced_larger_reserve()