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
from nanofiche_core.renderer import NanoFicheRenderer
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.packer import EnvelopeShape

def natural_sort_key(filename):
    """Extract numeric part from filename for proper sorting (1, 2, ... 10, 11, ...)"""
    match = re.search(r'-(\d+)\.tif', filename)
    if match:
        return int(match.group(1))
    return 0

def find_optimal_ellipse_grid_all_files_first(num_bins, target_aspect_x, target_aspect_y, bin_width, bin_height):
    """Find optimal grid arrangement prioritizing placing ALL files first, then optimizing."""
    
    target_aspect_ratio = target_aspect_x / target_aspect_y
    valid_arrangements = []  # Store all arrangements that can fit all files
    
    # Test different grid arrangements like the circle method does
    # Try from square-ish down to more elongated arrangements
    sqrt_bins = math.sqrt(num_bins)
    
    for cols in range(int(sqrt_bins * 0.4), int(sqrt_bins * 2.5) + 1):
        rows = math.ceil(num_bins / cols)
        
        # Calculate grid dimensions
        grid_width = cols * bin_width
        grid_height = rows * bin_height
        
        # For ellipse, calculate required radii to fit this grid
        margin = 1.15  # 15% margin for better fit
        
        # Calculate required ellipse to fit this grid with target aspect ratio
        if target_aspect_ratio >= 1:  # Wider ellipse
            required_a = max(grid_width / 2 * margin, grid_height / 2 * margin * target_aspect_ratio)
            required_b = required_a / target_aspect_ratio
        else:  # Taller ellipse  
            required_b = max(grid_height / 2 * margin, grid_width / 2 * margin / target_aspect_ratio)
            required_a = required_b * target_aspect_ratio
        
        # Test if this arrangement can actually fit all bins using our placement algorithm
        placements = test_elliptical_placement_capacity(
            num_bins, rows, cols, required_a, required_b, bin_width, bin_height
        )
        
        if len(placements) >= num_bins:  # Can fit all files!
            ellipse_area = math.pi * required_a * required_b
            valid_arrangements.append({
                'grid': (rows, cols),
                'ellipse_params': (required_a, required_b),
                'area': ellipse_area,
                'placements_count': len(placements)
            })
    
    if not valid_arrangements:
        # If no arrangement fits all files, create a larger ellipse
        side = math.ceil(sqrt_bins)
        grid_width = side * bin_width
        grid_height = side * bin_height
        
        # Make ellipse larger to ensure all fit
        margin = 1.3  # 30% margin
        if target_aspect_ratio >= 1:
            required_a = max(grid_width, grid_height) / 2 * margin
            required_b = required_a / target_aspect_ratio
        else:
            required_b = max(grid_width, grid_height) / 2 * margin
            required_a = required_b * target_aspect_ratio
        
        return (side, side), (required_a, required_b)
    
    # Among valid arrangements, pick the one with smallest area (most optimized)
    best_arrangement = min(valid_arrangements, key=lambda x: x['area'])
    return best_arrangement['grid'], best_arrangement['ellipse_params']

def test_elliptical_placement_capacity(num_bins, rows, cols, a, b, bin_width, bin_height):
    """Test how many bins can actually be placed with given ellipse parameters using symmetrical placement."""
    center_x, center_y = a, b  # Use radii as center for testing
    
    # Use the same symmetrical placement logic as the main function
    return generate_symmetrical_elliptical_placements_test(
        num_bins, rows, cols, center_x, center_y, a, b, bin_width, bin_height
    )

def generate_symmetrical_elliptical_placements_test(num_bins, rows, cols, center_x, center_y, a, b, bin_width, bin_height):
    """Test version of symmetrical placement for capacity testing."""
    max_rows = int(2 * b / bin_height)
    row_capacities = []
    
    # Calculate capacity for each row
    for row_idx in range(max_rows):
        y = center_y - b + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= b:
            row_capacities.append(0)
            continue
            
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor * 0.95
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Ensure even number for column symmetry
        if bins_in_row > 1 and bins_in_row % 2 == 1:
            bins_in_row -= 1
            
        row_capacities.append(bins_in_row)
    
    # Enforce top/bottom symmetry
    adjusted_capacities = row_capacities.copy()
    total_rows = len([cap for cap in row_capacities if cap > 0])
    
    for i in range(total_rows // 2):
        top_row_idx = i
        bottom_row_idx = total_rows - 1 - i
        
        if top_row_idx < len(adjusted_capacities) and bottom_row_idx < len(adjusted_capacities):
            top_capacity = adjusted_capacities[top_row_idx]
            bottom_capacity = adjusted_capacities[bottom_row_idx]
            
            if abs(top_capacity - bottom_capacity) > 3:
                min_capacity = min(top_capacity, bottom_capacity)
                max_allowed = min_capacity + 2
                adjusted_capacities[top_row_idx] = min(top_capacity, max_allowed)
                adjusted_capacities[bottom_row_idx] = min(bottom_capacity, max_allowed)
    
    # Count total possible placements
    placements = []
    bins_placed = 0
    
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
            
        bins_in_row = adjusted_capacities[row_idx]
        if bins_in_row <= 0:
            continue
            
        y = center_y - b + (row_idx + 0.5) * bin_height
        
        for col in range(bins_in_row):
            if bins_placed >= num_bins:
                break
                
            x = center_x - (bins_in_row * bin_width) / 2 + col * bin_width
            bin_center_x = x + bin_width // 2
            bin_center_y = y + bin_height // 2
            ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
            
            if ellipse_test <= 0.98:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements

def generate_symmetrical_elliptical_placements(num_bins, rows, cols, center_x, center_y, a, b, bin_width, bin_height):
    """Generate elliptical placement with symmetrical columns and top/bottom row symmetry."""
    # First pass: calculate row capacities and ensure top/bottom symmetry
    max_rows = int(2 * b / bin_height)
    row_capacities = []
    
    # Calculate capacity for each row
    for row_idx in range(max_rows):
        y = center_y - b + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= b:
            row_capacities.append(0)
            continue
            
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor * 0.95
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Ensure even number for column symmetry
        if bins_in_row > 1 and bins_in_row % 2 == 1:
            bins_in_row -= 1
            
        row_capacities.append(bins_in_row)
    
    # Enforce top/bottom symmetry: make corresponding rows have similar capacity (within 2-3 difference)
    adjusted_capacities = row_capacities.copy()
    total_rows = len([cap for cap in row_capacities if cap > 0])
    
    for i in range(total_rows // 2):
        top_row_idx = i
        bottom_row_idx = total_rows - 1 - i
        
        if top_row_idx < len(adjusted_capacities) and bottom_row_idx < len(adjusted_capacities):
            top_capacity = adjusted_capacities[top_row_idx]
            bottom_capacity = adjusted_capacities[bottom_row_idx]
            
            # If difference is more than 3, adjust to make them closer
            if abs(top_capacity - bottom_capacity) > 3:
                # Use the smaller capacity for both rows to maintain symmetry
                min_capacity = min(top_capacity, bottom_capacity)
                # But allow up to 2 difference for better packing
                max_allowed = min_capacity + 2
                adjusted_capacities[top_row_idx] = min(top_capacity, max_allowed)
                adjusted_capacities[bottom_row_idx] = min(bottom_capacity, max_allowed)
    
    # Second pass: place bins using adjusted capacities
    placements = []
    bins_placed = 0
    
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
            
        bins_in_row = adjusted_capacities[row_idx]
        if bins_in_row <= 0:
            continue
            
        y = center_y - b + (row_idx + 0.5) * bin_height
        start_x = center_x - (bins_in_row * bin_width) / 2
        
        for col in range(bins_in_row):
            if bins_placed >= num_bins:
                break
                
            x = start_x + col * bin_width
            
            # Double-check ellipse constraint
            bin_center_x = x + bin_width // 2
            bin_center_y = y + bin_height // 2
            ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
            
            if ellipse_test <= 0.98:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements

def test_optimized_ellipse_like_circle():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_optimized_ellipse_like_circle")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images for optimized ellipse test (circle-like method)")
    
    # Create output directory
    output_dir = "optimized_ellipse_like_circle_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Ellipse parameters (portrait 1.0:1.29 aspect ratio)
    aspect_x = 1.0
    aspect_y = 1.29
    
    logger.info(f"Target aspect ratio: {aspect_x}:{aspect_y}")
    
    # Find optimal grid arrangement prioritizing all files first, then optimizing
    (rows, cols), (a, b) = find_optimal_ellipse_grid_all_files_first(
        len(image_files), aspect_x, aspect_y, bin_width, bin_height
    )
    
    canvas_width = int(2 * a)
    canvas_height = int(2 * b)
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    
    logger.info(f"Optimal grid: {rows}x{cols}")
    logger.info(f"Ellipse parameters: a={a:.1f}, b={b:.1f}")
    logger.info(f"Canvas size: {canvas_width}x{canvas_height}")
    logger.info(f"Ellipse area: {math.pi * a * b:.0f} pixels²")
    
    # Generate symmetrical elliptical placements
    placements = generate_symmetrical_elliptical_placements(
        len(image_files), rows, cols, center_x, center_y, a, b, bin_width, bin_height
    )
    
    logger.info(f"Generated {len(placements)} placements for {len(image_files)} images")
    logger.info(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}%")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, rows, cols, placements, canvas_width, canvas_height):
            self.rows = rows
            self.columns = cols
            self.canvas_width = canvas_width
            self.canvas_height = canvas_height
            self.placements = placements
            self.envelope_shape = EnvelopeShape.ELLIPSE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(rows, cols, placements, canvas_width, canvas_height)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/optimized_ellipse_like_circle_test.tif"
    
    # Create image bins from file paths
    image_bins = []
    for i, image_path in enumerate(image_files[:len(placements)]):  # Only use as many as we have placements
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate the full resolution TIFF and thumbnail
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/optimized_ellipse_like_circle_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="optimized_ellipse_like_circle_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Write test log
        log_filename = f"{output_dir}/optimized_ellipse_like_circle_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Optimized Ellipse Test (Circle-like Method)\n")
            log_file.write(f"Timestamp: {thumbnail_result.split('_')[-1].split('.')[0]}\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Images placed: {len(placements)}\n")
            log_file.write(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}%\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Envelope shape: ellipse (optimized like circle)\n")
            log_file.write(f"Target aspect ratio: {aspect_x}:{aspect_y}\n")
            log_file.write(f"Optimal grid: {rows}x{cols}\n")
            log_file.write(f"Ellipse radii: a={a:.1f}, b={b:.1f}\n")
            log_file.write(f"Canvas size: {canvas_width}x{canvas_height}\n")
            log_file.write(f"Ellipse area: {math.pi * a * b:.0f} pixels²\n")
            log_file.write(f"Placement method: Symmetrical columns following ellipse curve\n")
            log_file.write(f"Optimization: Grid testing like circle method\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Optimized ellipse test (circle-like) completed. Thumbnail: {thumbnail_result}")
        print(f"Grid: {rows}x{cols}, Fill efficiency: {len(placements)/len(image_files)*100:.1f}% ({len(placements)}/{len(image_files)} images)")
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

if __name__ == "__main__":
    success = test_optimized_ellipse_like_circle()
    sys.exit(0 if success else 1)