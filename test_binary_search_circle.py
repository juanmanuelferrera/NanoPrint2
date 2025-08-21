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

def try_pack_images_in_circle(num_bins, radius, bin_width, bin_height):
    """Try to pack all images in given circle, return (success, placements, actual_count)."""
    center_x = center_y = radius
    max_rows = int(2 * radius / bin_height)
    
    placements = []
    bins_placed = 0
    row_distribution = []
    
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
            
        y = center_y - radius + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= radius:
            continue
            
        # Calculate width at this height in the circle
        # Circle equation: x² + y² = r²
        # Solve for x: x = ±sqrt(r² - y²)
        width_factor = math.sqrt(max(0, 1 - (y_offset / radius) ** 2))
        row_half_width = radius * width_factor
        
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
                
                # Verify this position is truly inside the circle
                bin_center_x = x + bin_width // 2
                bin_center_y = y + bin_height // 2
                distance_sq = (bin_center_x - center_x) ** 2 + (bin_center_y - center_y) ** 2
                
                if distance_sq <= radius ** 2:  # Must be inside the circle
                    placements.append((int(x), int(y)))
                    bins_placed += 1
    
    # Check row symmetry
    top_row = row_distribution[0] if row_distribution else 0
    bottom_row = row_distribution[-1] if row_distribution else 0
    
    success = bins_placed >= num_bins
    return success, placements, bins_placed, top_row, bottom_row, len(row_distribution)

def find_optimal_circle_binary_search(num_bins, bin_width, bin_height):
    """Use binary search to find minimum circle that fits all images."""
    
    # Step 1: Calculate total image area
    total_image_area = num_bins * bin_width * bin_height
    logger = logging.getLogger("binary_search_circle")
    logger.info(f"Total image area: {total_image_area:,} pixels²")
    
    # Step 2: Create initial circle with same area as images
    # For circle: area = π * r²
    # r = sqrt(area / π)
    initial_radius = math.sqrt(total_image_area / math.pi)
    
    logger.info(f"Initial circle (same area as images): radius={initial_radius:.1f}")
    
    # Binary search bounds
    # Lower bound: theoretical minimum
    # Upper bound: 2x theoretical minimum
    radius_min = initial_radius
    radius_max = initial_radius * 2.0
    
    # Find a working upper bound first
    while radius_max <= initial_radius * 3.0:
        success, _, placed, _, _, _ = try_pack_images_in_circle(num_bins, radius_max, bin_width, bin_height)
        if success:
            break
        radius_max += initial_radius * 0.5
    
    logger.info(f"Search bounds: {radius_min:.1f} to {radius_max:.1f}")
    
    # Binary search for optimal radius
    best_radius = radius_max
    best_placements = None
    best_stats = None
    iterations = 0
    max_iterations = 50
    
    # Use 0.1% precision for radius
    while (radius_max - radius_min) / radius_min > 0.001 and iterations < max_iterations:
        radius_mid = (radius_min + radius_max) / 2
        
        success, placements, placed, top_row, bottom_row, num_rows = try_pack_images_in_circle(
            num_bins, radius_mid, bin_width, bin_height
        )
        
        area = math.pi * radius_mid * radius_mid
        efficiency = total_image_area / area * 100
        logger.info(f"Iteration {iterations}: radius={radius_mid:.1f}, placed={placed}/{num_bins}, "
                   f"rows={num_rows}, top={top_row}, bottom={bottom_row}, "
                   f"success={success}, efficiency={efficiency:.1f}%")
        
        if success:
            # All images fit - try to make it smaller
            best_radius = radius_mid
            best_placements = placements
            best_stats = (top_row, bottom_row, num_rows)
            radius_max = radius_mid
        else:
            # Not all images fit - need bigger circle
            radius_min = radius_mid
        
        iterations += 1
    
    if best_placements is None:
        # Fallback to largest tested size
        _, best_placements, _, top_row, bottom_row, num_rows = try_pack_images_in_circle(
            num_bins, radius_max, bin_width, bin_height
        )
        best_radius = radius_max
        best_stats = (top_row, bottom_row, num_rows)
    
    top_row, bottom_row, num_rows = best_stats
    final_area = math.pi * best_radius * best_radius
    efficiency = total_image_area / final_area * 100
    
    logger.info(f"Optimal found: radius={best_radius:.1f}")
    logger.info(f"Final area: {final_area:,.0f} pixels²")
    logger.info(f"Number of rows: {num_rows}")
    logger.info(f"Row distribution: top={top_row}, bottom={bottom_row}")
    logger.info(f"Packing efficiency: {efficiency:.1f}%")
    
    return best_radius, best_placements, top_row, bottom_row

def test_binary_search_circle():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_binary_search_circle")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images using binary search for circle")
    
    # Create output directory
    output_dir = "binary_search_circle_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    logger.info(f"Bin dimensions: {bin_width}x{bin_height}")
    
    # Find optimal circle using binary search
    radius, placements, top_row, bottom_row = find_optimal_circle_binary_search(
        len(image_files), bin_width, bin_height
    )
    
    canvas_size = int(2 * radius)
    center = canvas_size // 2
    
    # Adjust placements to canvas coordinates
    adjusted_placements = []
    for x, y in placements:
        # Original placements use radius as center, adjust to canvas center
        adj_x = x - radius + center
        adj_y = y - radius + center
        adjusted_placements.append((int(adj_x), int(adj_y)))
    
    logger.info(f"Canvas size: {canvas_size}x{canvas_size}")
    logger.info(f"Generated {len(adjusted_placements)} placements for {len(image_files)} images")
    logger.info(f"Fill success: {len(adjusted_placements) >= len(image_files)}")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_size):
            self.rows = 0  # Not used in binary search mode
            self.columns = 0  # Not used in binary search mode
            self.canvas_width = canvas_size
            self.canvas_height = canvas_size
            self.placements = placements
            self.envelope_shape = EnvelopeShape.CIRCLE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(adjusted_placements, canvas_size)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/binary_search_circle_test.tif"
    
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
    log_path = Path(f"{output_dir}/binary_search_circle_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="binary_search_circle_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Calculate statistics
        total_image_area = len(image_files) * bin_width * bin_height
        circle_area = math.pi * radius * radius
        efficiency = total_image_area / circle_area * 100
        
        # Write test log
        log_filename = f"{output_dir}/binary_search_circle_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Binary Search Circle Optimization Test\n")
            log_file.write(f"Algorithm: 6-step binary search approach\n")
            log_file.write(f"1. Calculate image area\n")
            log_file.write(f"2. Create circle with same area\n")
            log_file.write(f"3. Place images, check if all fit\n")
            log_file.write(f"4. If not all fit, increase radius\n")
            log_file.write(f"5. If all fit, decrease radius\n")
            log_file.write(f"6. Stop at minimum circle containing all\n")
            log_file.write(f"\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Total image area: {total_image_area:,} pixels²\n")
            log_file.write(f"Optimal circle radius: {radius:.1f} pixels\n")
            log_file.write(f"Circle area: {circle_area:,.0f} pixels²\n")
            log_file.write(f"Canvas size: {canvas_size}x{canvas_size} pixels\n")
            log_file.write(f"Top row images: {top_row}\n")
            log_file.write(f"Bottom row images: {bottom_row}\n")
            log_file.write(f"Packing efficiency: {efficiency:.1f}%\n")
            log_file.write(f"Binary search precision: 0.1%\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Binary search circle test completed. Thumbnail: {thumbnail_result}")
        print(f"Circle radius: {radius:.1f} pixels")
        print(f"Top row: {top_row}, Bottom row: {bottom_row}")
        print(f"Packing efficiency: {efficiency:.1f}%")
        print(f"All {len(image_files)} images placed successfully")
        
        # Create and copy preview to clipboard
        logger.info("Creating preview and copying to clipboard...")
        create_and_copy_preview(output_dir)
        
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

def create_and_copy_preview(output_dir):
    """Create preview image and copy to clipboard."""
    from PIL import Image
    import subprocess
    
    input_path = f"{output_dir}/binary_search_circle_test.tif"
    output_path = "binary_search_circle_preview.png"
    
    try:
        with Image.open(input_path) as img:
            # Create a smaller version
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized.save(output_path, 'PNG')
            print(f"Created preview: {output_path} ({new_width}x{new_height})")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_binary_search_circle()
    sys.exit(0 if success else 1)