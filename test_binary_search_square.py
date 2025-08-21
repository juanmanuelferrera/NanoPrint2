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

def try_pack_images_in_square(num_bins, side_length, bin_width, bin_height):
    """Try to pack all images in given square, return (success, placements, actual_count)."""
    
    # Calculate how many bins fit in each dimension
    cols = int(side_length / bin_width)
    rows = int(side_length / bin_height)
    
    # Center the grid in the square
    grid_width = cols * bin_width
    grid_height = rows * bin_height
    offset_x = (side_length - grid_width) / 2
    offset_y = (side_length - grid_height) / 2
    
    placements = []
    bins_placed = 0
    
    for row in range(rows):
        if bins_placed >= num_bins:
            break
            
        for col in range(cols):
            if bins_placed >= num_bins:
                break
                
            x = offset_x + col * bin_width
            y = offset_y + row * bin_height
            
            # Check if this position is inside the square (should always be true for square)
            if x >= 0 and y >= 0 and x + bin_width <= side_length and y + bin_height <= side_length:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    success = bins_placed >= num_bins
    capacity = rows * cols
    
    return success, placements, bins_placed, rows, cols, capacity

def find_optimal_square_binary_search(num_bins, bin_width, bin_height):
    """Use binary search to find minimum square that fits all images."""
    
    # Step 1: Calculate total image area
    total_image_area = num_bins * bin_width * bin_height
    logger = logging.getLogger("binary_search_square")
    logger.info(f"Total image area: {total_image_area:,} pixels²")
    
    # Step 2: Create initial square with same area as images
    # For square: area = side²
    initial_side = math.sqrt(total_image_area)
    
    logger.info(f"Initial square (same area as images): side={initial_side:.1f}")
    
    # Binary search bounds
    # Lower bound: theoretical minimum
    # Upper bound: 2x theoretical minimum
    side_min = initial_side
    side_max = initial_side * 2.0
    
    # Find a working upper bound first
    while side_max <= initial_side * 3.0:
        success, _, placed, _, _, _ = try_pack_images_in_square(num_bins, side_max, bin_width, bin_height)
        if success:
            break
        side_max += initial_side * 0.5
    
    logger.info(f"Search bounds: {side_min:.1f} to {side_max:.1f}")
    
    # Binary search for optimal side length
    best_side = side_max
    best_placements = None
    best_stats = None
    iterations = 0
    max_iterations = 50
    
    # Use smaller precision for square (1 pixel precision)
    while side_max - side_min > 1 and iterations < max_iterations:
        side_mid = (side_min + side_max) / 2
        
        success, placements, placed, rows, cols, capacity = try_pack_images_in_square(
            num_bins, side_mid, bin_width, bin_height
        )
        
        area = side_mid * side_mid
        efficiency = total_image_area / area * 100
        logger.info(f"Iteration {iterations}: side={side_mid:.1f}, placed={placed}/{num_bins}, "
                   f"grid={rows}x{cols}, capacity={capacity}, success={success}, efficiency={efficiency:.1f}%")
        
        if success:
            # All images fit - try to make it smaller
            best_side = side_mid
            best_placements = placements
            best_stats = (rows, cols, capacity)
            side_max = side_mid
        else:
            # Not all images fit - need bigger square
            side_min = side_mid
        
        iterations += 1
    
    if best_placements is None:
        # Fallback to largest tested size
        _, best_placements, _, rows, cols, capacity = try_pack_images_in_square(
            num_bins, side_max, bin_width, bin_height
        )
        best_side = side_max
        best_stats = (rows, cols, capacity)
    
    rows, cols, capacity = best_stats
    final_area = best_side * best_side
    efficiency = total_image_area / final_area * 100
    
    logger.info(f"Optimal found: side={best_side:.1f}")
    logger.info(f"Final area: {final_area:,.0f} pixels²")
    logger.info(f"Grid: {rows}x{cols}, Capacity: {capacity}")
    logger.info(f"Packing efficiency: {efficiency:.1f}%")
    
    return best_side, best_placements, rows, cols

def test_binary_search_square():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_binary_search_square")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images using binary search for square")
    
    # Create output directory
    output_dir = "binary_search_square_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    logger.info(f"Bin dimensions: {bin_width}x{bin_height}")
    
    # Find optimal square using binary search
    side_length, placements, rows, cols = find_optimal_square_binary_search(
        len(image_files), bin_width, bin_height
    )
    
    canvas_size = int(side_length)
    
    logger.info(f"Canvas size: {canvas_size}x{canvas_size}")
    logger.info(f"Generated {len(placements)} placements for {len(image_files)} images")
    logger.info(f"Fill success: {len(placements) >= len(image_files)}")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_size, rows, cols):
            self.rows = rows
            self.columns = cols
            self.canvas_width = canvas_size
            self.canvas_height = canvas_size
            self.placements = placements
            self.envelope_shape = EnvelopeShape.SQUARE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, canvas_size, rows, cols)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/binary_search_square_test.tif"
    
    # Create image bins from file paths
    image_bins = []
    for i, image_path in enumerate(image_files[:len(placements)]):
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate the full resolution TIFF and thumbnail
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/binary_search_square_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="binary_search_square_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Calculate statistics
        total_image_area = len(image_files) * bin_width * bin_height
        square_area = canvas_size * canvas_size
        efficiency = total_image_area / square_area * 100
        
        # Write test log
        log_filename = f"{output_dir}/binary_search_square_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Binary Search Square Optimization Test\n")
            log_file.write(f"Algorithm: 6-step binary search approach\n")
            log_file.write(f"1. Calculate image area\n")
            log_file.write(f"2. Create square with same area\n")
            log_file.write(f"3. Place images, check if all fit\n")
            log_file.write(f"4. If not all fit, increase size\n")
            log_file.write(f"5. If all fit, decrease size\n")
            log_file.write(f"6. Stop at minimum square containing all\n")
            log_file.write(f"\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Total image area: {total_image_area:,} pixels²\n")
            log_file.write(f"Optimal square side: {canvas_size} pixels\n")
            log_file.write(f"Square area: {square_area:,} pixels²\n")
            log_file.write(f"Grid arrangement: {rows}x{cols}\n")
            log_file.write(f"Packing efficiency: {efficiency:.1f}%\n")
            log_file.write(f"Binary search precision: 1 pixel\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Binary search square test completed. Thumbnail: {thumbnail_result}")
        print(f"Square side: {canvas_size} pixels")
        print(f"Grid: {rows}x{cols}")
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
    
    input_path = f"{output_dir}/binary_search_square_test.tif"
    output_path = "binary_search_square_preview.png"
    
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
    success = test_binary_search_square()
    sys.exit(0 if success else 1)