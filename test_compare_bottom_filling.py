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

def analyze_bottom_row(placements, total_cols):
    """Analyze how well the bottom row is filled."""
    if not placements:
        return 0, 0
    
    # Find the last row Y position
    last_row_y = max(p[1] for p in placements)
    # Count images in the last row
    bottom_row_images = sum(1 for p in placements if p[1] == last_row_y)
    
    return bottom_row_images, last_row_y

def test_compare_bottom_filling():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_compare_bottom_filling")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Comparing bottom row filling for {len(image_files)} images")
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Use the portrait rectangle dimensions from previous test
    rect_width = 45502.8
    rect_height = 58698.6
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    
    logger.info(f"Rectangle: {rect_width:.1f}x{rect_height:.1f}")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    
    # Test different reserve sizes
    test_cases = [
        (2, 2, "Minimal reserve"),
        (4, 4, "Current optimal"),
        (6, 6, "Larger reserve"),
        (8, 8, "Very large reserve")
    ]
    
    print(f"\nBottom Row Filling Comparison:")
    print(f"{'Reserve':<15} {'Images':<8} {'Bottom Row':<12} {'Utilization':<12} {'Last Y':<8}")
    print("-" * 65)
    
    for reserve_rows, reserve_cols, description in test_cases:
        placements, placed = pack_images_simple(
            len(image_files), rect_width, rect_height, bin_width, bin_height, reserve_cols, reserve_rows
        )
        
        if placed >= len(image_files):
            bottom_count, last_y = analyze_bottom_row(placements, total_cols)
            utilization = bottom_count / total_cols * 100
            
            print(f"{reserve_rows}x{reserve_cols:<12} {placed:<8} {bottom_count}/{total_cols:<8} {utilization:>6.1f}%       {last_y}")
            
            logger.info(f"{description}: {reserve_rows}x{reserve_cols} reserve")
            logger.info(f"  Images placed: {placed}")
            logger.info(f"  Bottom row: {bottom_count}/{total_cols} ({utilization:.1f}%)")
            logger.info(f"  Last image Y: {last_y}")
            logger.info(f"  Bottom remaining: {rect_height - (last_y + bin_height):.1f} pixels")
        else:
            print(f"{reserve_rows}x{reserve_cols:<12} {placed:<8} {'N/A':<12} {'N/A':<12} {'N/A'}")
            logger.info(f"{description}: FAILED - only {placed}/{len(image_files)} images fit")
        
        print()

if __name__ == "__main__":
    test_compare_bottom_filling()