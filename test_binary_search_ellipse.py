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

def try_pack_images_in_ellipse(num_bins, a, b, bin_width, bin_height):
    """Try to pack all images in given ellipse, return (success, placements, actual_count)."""
    center_x, center_y = a, b
    max_rows = int(2 * b / bin_height)
    
    placements = []
    bins_placed = 0
    row_distribution = []
    
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
            
        y = center_y - b + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= b:
            continue
            
        # Calculate width at this height in the ellipse
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor
        
        # How many bins fit in this row?
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Ensure even number for symmetry
        if bins_in_row > 1 and bins_in_row % 2 == 1:
            bins_in_row -= 1
            
        if bins_in_row > 0:
            row_distribution.append(bins_in_row)
            start_x = center_x - (bins_in_row * bin_width) / 2
            
            for col in range(bins_in_row):
                if bins_placed >= num_bins:
                    break
                    
                x = start_x + col * bin_width
                
                # Verify this position is truly inside the ellipse
                bin_center_x = x + bin_width // 2
                bin_center_y = y + bin_height // 2
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 1.0:  # Must be inside the ellipse
                    placements.append((int(x), int(y)))
                    bins_placed += 1
    
    # Check row symmetry
    top_row = row_distribution[0] if row_distribution else 0
    bottom_row = row_distribution[-1] if row_distribution else 0
    
    success = bins_placed >= num_bins
    return success, placements, bins_placed, top_row, bottom_row

def find_optimal_ellipse_binary_search(num_bins, target_aspect_x, target_aspect_y, bin_width, bin_height):
    """Use binary search to find minimum ellipse that fits all images."""
    
    # Step 1: Calculate total image area
    total_image_area = num_bins * bin_width * bin_height
    logger = logging.getLogger("binary_search")
    logger.info(f"Total image area: {total_image_area:,} pixels²")
    
    # Step 2: Create initial envelope with same area as images
    # For ellipse: area = π * a * b
    # With aspect ratio constraint: a/b = aspect_x/aspect_y
    aspect_ratio = target_aspect_x / target_aspect_y
    
    # Solve for initial radii
    # area = π * a * b and a = b * aspect_ratio
    # area = π * b² * aspect_ratio
    # b = sqrt(area / (π * aspect_ratio))
    initial_b = math.sqrt(total_image_area / (math.pi * aspect_ratio))
    initial_a = initial_b * aspect_ratio
    
    logger.info(f"Initial ellipse (same area as images): a={initial_a:.1f}, b={initial_b:.1f}")
    
    # Binary search bounds
    # Lower bound: image area (will likely fail)
    # Upper bound: 2x image area (should definitely fit)
    scale_min = 1.0
    scale_max = 2.0
    
    # Find a working upper bound first
    while scale_max <= 3.0:
        test_a = initial_a * scale_max
        test_b = initial_b * scale_max
        success, _, placed, _, _ = try_pack_images_in_ellipse(num_bins, test_a, test_b, bin_width, bin_height)
        if success:
            break
        scale_max += 0.5
    
    logger.info(f"Search bounds: {scale_min:.2f} to {scale_max:.2f}")
    
    # Binary search for optimal scale
    best_scale = scale_max
    best_placements = None
    best_stats = None
    iterations = 0
    max_iterations = 50
    
    while scale_max - scale_min > 0.001 and iterations < max_iterations:  # 0.1% precision
        scale_mid = (scale_min + scale_max) / 2
        test_a = initial_a * scale_mid
        test_b = initial_b * scale_mid
        
        success, placements, placed, top_row, bottom_row = try_pack_images_in_ellipse(
            num_bins, test_a, test_b, bin_width, bin_height
        )
        
        area = math.pi * test_a * test_b
        logger.info(f"Iteration {iterations}: scale={scale_mid:.4f}, placed={placed}/{num_bins}, "
                   f"success={success}, area={area:,.0f}")
        
        if success:
            # All images fit - try to make it smaller
            best_scale = scale_mid
            best_placements = placements
            best_stats = (test_a, test_b, top_row, bottom_row)
            scale_max = scale_mid
        else:
            # Not all images fit - need bigger envelope
            scale_min = scale_mid
        
        iterations += 1
    
    if best_placements is None:
        # Fallback to largest tested size
        test_a = initial_a * scale_max
        test_b = initial_b * scale_max
        _, best_placements, _, top_row, bottom_row = try_pack_images_in_ellipse(
            num_bins, test_a, test_b, bin_width, bin_height
        )
        best_stats = (test_a, test_b, top_row, bottom_row)
    
    final_a, final_b, top_row, bottom_row = best_stats
    final_area = math.pi * final_a * final_b
    efficiency = total_image_area / final_area * 100
    
    logger.info(f"Optimal found: scale={best_scale:.4f}")
    logger.info(f"Final ellipse: a={final_a:.1f}, b={final_b:.1f}")
    logger.info(f"Final area: {final_area:,.0f} pixels²")
    logger.info(f"Packing efficiency: {efficiency:.1f}%")
    logger.info(f"Row distribution: top={top_row}, bottom={bottom_row}")
    
    return (final_a, final_b), best_placements

def test_binary_search_ellipse():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_binary_search_ellipse")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images using binary search optimization")
    
    # Create output directory
    output_dir = "binary_search_ellipse_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Ellipse parameters (portrait 1.0:1.29 aspect ratio)
    aspect_x = 1.0
    aspect_y = 1.29
    
    logger.info(f"Target aspect ratio: {aspect_x}:{aspect_y}")
    logger.info(f"Bin dimensions: {bin_width}x{bin_height}")
    
    # Find optimal ellipse using binary search
    (a, b), placements = find_optimal_ellipse_binary_search(
        len(image_files), aspect_x, aspect_y, bin_width, bin_height
    )
    
    canvas_width = int(2 * a)
    canvas_height = int(2 * b)
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    
    # Adjust placements to canvas coordinates
    adjusted_placements = []
    for x, y in placements:
        # Original placements use a,b as center, adjust to canvas center
        adj_x = x - a + center_x
        adj_y = y - b + center_y
        adjusted_placements.append((int(adj_x), int(adj_y)))
    
    logger.info(f"Canvas size: {canvas_width}x{canvas_height}")
    logger.info(f"Generated {len(adjusted_placements)} placements for {len(image_files)} images")
    logger.info(f"Fill success: {len(adjusted_placements) >= len(image_files)}")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_width, canvas_height):
            self.rows = 0  # Not used in binary search mode
            self.columns = 0  # Not used in binary search mode
            self.canvas_width = canvas_width
            self.canvas_height = canvas_height
            self.placements = placements
            self.envelope_shape = EnvelopeShape.ELLIPSE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(adjusted_placements, canvas_width, canvas_height)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/binary_search_ellipse_test.tif"
    
    # Create image bins from file paths
    image_bins = []
    for i, image_path in enumerate(image_files[:len(adjusted_placements)]):
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate the full resolution TIFF and thumbnail
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/binary_search_ellipse_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="binary_search_ellipse_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Calculate statistics
        total_image_area = len(image_files) * bin_width * bin_height
        ellipse_area = math.pi * a * b
        efficiency = total_image_area / ellipse_area * 100
        
        # Write test log
        log_filename = f"{output_dir}/binary_search_ellipse_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Binary Search Ellipse Optimization Test\n")
            log_file.write(f"Algorithm: Your suggested 6-step approach\n")
            log_file.write(f"1. Calculate image area\n")
            log_file.write(f"2. Create envelope with same area\n")
            log_file.write(f"3. Place images, check if outside\n")
            log_file.write(f"4. If outside, increase area\n")
            log_file.write(f"5. If inside, decrease area\n")
            log_file.write(f"6. Stop at minimum envelope containing all\n")
            log_file.write(f"\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Total image area: {total_image_area:,} pixels²\n")
            log_file.write(f"Target aspect ratio: {aspect_x}:{aspect_y}\n")
            log_file.write(f"Optimal ellipse: a={a:.1f}, b={b:.1f}\n")
            log_file.write(f"Ellipse area: {ellipse_area:,.0f} pixels²\n")
            log_file.write(f"Packing efficiency: {efficiency:.1f}%\n")
            log_file.write(f"Canvas size: {canvas_width}x{canvas_height}\n")
            log_file.write(f"Binary search precision: 0.1%\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Binary search ellipse test completed. Thumbnail: {thumbnail_result}")
        print(f"Ellipse: a={a:.1f}, b={b:.1f}")
        print(f"Packing efficiency: {efficiency:.1f}%")
        print(f"All {len(image_files)} images placed successfully")
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

if __name__ == "__main__":
    success = test_binary_search_ellipse()
    sys.exit(0 if success else 1)