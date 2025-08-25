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

def calculate_reserved_space_size(side_length, reserve_aspect_ratio):
    """Calculate the size of reserved space with given aspect ratio."""
    # We want to reserve space with aspect ratio 1300:1900 (width:height)
    # Let's use a reasonable fraction of the total area for the reserve
    # Reserve area should be roughly equivalent to 1-2 image areas
    
    total_area = side_length * side_length
    # Reserve space equivalent to ~1.5 images worth of area
    reserve_area = 1.5 * 1300 * 1900  # 1.5 image areas
    
    # Calculate reserve dimensions with correct aspect ratio
    # reserve_area = reserve_width * reserve_height
    # reserve_aspect_ratio = reserve_width / reserve_height
    # So: reserve_width = reserve_height * reserve_aspect_ratio
    # Therefore: reserve_area = reserve_height² * reserve_aspect_ratio
    
    reserve_height = math.sqrt(reserve_area / reserve_aspect_ratio)
    reserve_width = reserve_height * reserve_aspect_ratio
    
    # Make sure it's not too big (max 20% of side length)
    max_dimension = side_length * 0.2
    if reserve_width > max_dimension:
        reserve_width = max_dimension
        reserve_height = reserve_width / reserve_aspect_ratio
    if reserve_height > max_dimension:
        reserve_height = max_dimension
        reserve_width = reserve_height * reserve_aspect_ratio
    
    return int(reserve_width), int(reserve_height)

def try_pack_images_in_square_with_reserve(num_bins, side_length, bin_width, bin_height, reserve_width, reserve_height):
    """Try to pack all images in square with reserved top-left space."""
    
    # Calculate available space after reserving top-left corner
    # We have two areas to work with:
    # 1. Top-right: from (reserve_width, 0) to (side_length, reserve_height)
    # 2. Bottom: from (0, reserve_height) to (side_length, side_length)
    
    placements = []
    bins_placed = 0
    
    # Area 1: Top-right rectangle
    top_right_width = side_length - reserve_width
    top_right_height = reserve_height
    top_right_cols = int(top_right_width / bin_width)
    top_right_rows = int(top_right_height / bin_height)
    
    # Place images in top-right area
    for row in range(top_right_rows):
        if bins_placed >= num_bins:
            break
        for col in range(top_right_cols):
            if bins_placed >= num_bins:
                break
            x = reserve_width + col * bin_width
            y = row * bin_height
            if x + bin_width <= side_length and y + bin_height <= reserve_height:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    # Area 2: Bottom rectangle (full width)
    bottom_width = side_length
    bottom_height = side_length - reserve_height
    bottom_cols = int(bottom_width / bin_width)
    bottom_rows = int(bottom_height / bin_height)
    
    # Place remaining images in bottom area
    for row in range(bottom_rows):
        if bins_placed >= num_bins:
            break
        for col in range(bottom_cols):
            if bins_placed >= num_bins:
                break
            x = col * bin_width
            y = reserve_height + row * bin_height
            if x + bin_width <= side_length and y + bin_height <= side_length:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    success = bins_placed >= num_bins
    total_capacity = (top_right_rows * top_right_cols) + (bottom_rows * bottom_cols)
    
    return success, placements, bins_placed, total_capacity, (top_right_rows, top_right_cols), (bottom_rows, bottom_cols)

def find_optimal_square_with_reserve_binary_search(num_bins, bin_width, bin_height):
    """Use binary search to find minimum square with reserved space that fits all images."""
    
    # Step 1: Calculate total image area
    total_image_area = num_bins * bin_width * bin_height
    logger = logging.getLogger("binary_search_square_reserve")
    logger.info(f"Total image area: {total_image_area:,} pixels²")
    
    # Reserve space aspect ratio (same as images)
    reserve_aspect_ratio = bin_width / bin_height  # 1300/1900 ≈ 0.684
    logger.info(f"Reserved space aspect ratio: {reserve_aspect_ratio:.3f} (same as images)")
    
    # Step 2: Create initial square - need bigger than without reserve
    # Start with 1.3x the theoretical minimum to account for reserved space
    initial_side = math.sqrt(total_image_area) * 1.3
    
    logger.info(f"Initial square (with reserve space): side={initial_side:.1f}")
    
    # Binary search bounds
    side_min = initial_side * 0.8  # Start lower since we're accounting for reserve
    side_max = initial_side * 2.0
    
    # Find a working upper bound first
    while side_max <= initial_side * 3.0:
        reserve_width, reserve_height = calculate_reserved_space_size(side_max, reserve_aspect_ratio)
        success, _, placed, _, _, _ = try_pack_images_in_square_with_reserve(
            num_bins, side_max, bin_width, bin_height, reserve_width, reserve_height
        )
        if success:
            break
        side_max += initial_side * 0.5
    
    logger.info(f"Search bounds: {side_min:.1f} to {side_max:.1f}")
    
    # Binary search for optimal side length
    best_side = side_max
    best_placements = None
    best_stats = None
    best_reserve_dims = None
    iterations = 0
    max_iterations = 50
    
    while side_max - side_min > 1 and iterations < max_iterations:
        side_mid = (side_min + side_max) / 2
        reserve_width, reserve_height = calculate_reserved_space_size(side_mid, reserve_aspect_ratio)
        
        success, placements, placed, capacity, top_right_grid, bottom_grid = try_pack_images_in_square_with_reserve(
            num_bins, side_mid, bin_width, bin_height, reserve_width, reserve_height
        )
        
        area = side_mid * side_mid
        reserve_area = reserve_width * reserve_height
        usable_area = area - reserve_area
        efficiency = total_image_area / usable_area * 100
        overall_efficiency = total_image_area / area * 100
        
        logger.info(f"Iteration {iterations}: side={side_mid:.1f}, reserve={reserve_width}x{reserve_height}, "
                   f"placed={placed}/{num_bins}, capacity={capacity}, success={success}, "
                   f"usable_efficiency={efficiency:.1f}%, overall={overall_efficiency:.1f}%")
        
        if success:
            # All images fit - try to make it smaller
            best_side = side_mid
            best_placements = placements
            best_stats = (capacity, top_right_grid, bottom_grid)
            best_reserve_dims = (reserve_width, reserve_height)
            side_max = side_mid
        else:
            # Not all images fit - need bigger square
            side_min = side_mid
        
        iterations += 1
    
    if best_placements is None:
        # Fallback to largest tested size
        reserve_width, reserve_height = calculate_reserved_space_size(side_max, reserve_aspect_ratio)
        _, best_placements, _, capacity, top_right_grid, bottom_grid = try_pack_images_in_square_with_reserve(
            num_bins, side_max, bin_width, bin_height, reserve_width, reserve_height
        )
        best_side = side_max
        best_stats = (capacity, top_right_grid, bottom_grid)
        best_reserve_dims = (reserve_width, reserve_height)
    
    capacity, top_right_grid, bottom_grid = best_stats
    reserve_width, reserve_height = best_reserve_dims
    
    final_area = best_side * best_side
    reserve_area = reserve_width * reserve_height
    usable_area = final_area - reserve_area
    usable_efficiency = total_image_area / usable_area * 100
    overall_efficiency = total_image_area / final_area * 100
    
    logger.info(f"Optimal found: side={best_side:.1f}")
    logger.info(f"Reserved space: {reserve_width}x{reserve_height} ({reserve_area:,} pixels²)")
    logger.info(f"Total area: {final_area:,.0f} pixels²")
    logger.info(f"Usable area: {usable_area:,.0f} pixels²")
    logger.info(f"Grid arrangement: top-right {top_right_grid}, bottom {bottom_grid}")
    logger.info(f"Usable space efficiency: {usable_efficiency:.1f}%")
    logger.info(f"Overall efficiency: {overall_efficiency:.1f}%")
    
    return best_side, best_placements, best_reserve_dims, best_stats

def test_binary_search_square_with_reserve():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_binary_search_square_with_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images using binary search for square with reserved space")
    
    # Create output directory
    output_dir = "binary_search_square_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    logger.info(f"Bin dimensions: {bin_width}x{bin_height}")
    logger.info(f"Reserved space will have same aspect ratio: {bin_width}:{bin_height}")
    
    # Find optimal square with reserved space using binary search
    side_length, placements, (reserve_width, reserve_height), (capacity, top_right_grid, bottom_grid) = find_optimal_square_with_reserve_binary_search(
        len(image_files), bin_width, bin_height
    )
    
    canvas_size = int(side_length)
    
    logger.info(f"Canvas size: {canvas_size}x{canvas_size}")
    logger.info(f"Reserved space: {reserve_width}x{reserve_height} (top-left corner)")
    logger.info(f"Generated {len(placements)} placements for {len(image_files)} images")
    logger.info(f"Fill success: {len(placements) >= len(image_files)}")
    
    # Create mock packing result with reserved space info
    class MockPackingResultWithReserve:
        def __init__(self, placements, canvas_size, reserve_dims, grid_info):
            self.rows = 0  # Complex layout, not simple grid
            self.columns = 0
            self.canvas_width = canvas_size
            self.canvas_height = canvas_size
            self.placements = placements
            self.envelope_shape = EnvelopeShape.SQUARE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
            # Additional info for reserved space
            self.reserve_width = reserve_dims[0]
            self.reserve_height = reserve_dims[1]
            self.top_right_grid = grid_info[1]
            self.bottom_grid = grid_info[2]
            # Add envelope_spec for compatibility with current renderer
            from nanofiche_core.packer import EnvelopeSpec
            self.envelope_spec = EnvelopeSpec(
                shape=EnvelopeShape.SQUARE,
                reserve_enabled=True,
                reserve_width=reserve_dims[0],
                reserve_height=reserve_dims[1],
                reserve_position="top-left",
                reserve_auto_size=False
            )
    
    packing_result = MockPackingResultWithReserve(placements, canvas_size, (reserve_width, reserve_height), (capacity, top_right_grid, bottom_grid))
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/binary_search_square_reserve_test.tif"
    
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
    log_path = Path(f"{output_dir}/binary_search_square_reserve_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="binary_search_square_reserve_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Calculate statistics
        total_image_area = len(image_files) * bin_width * bin_height
        total_area = canvas_size * canvas_size
        reserve_area = reserve_width * reserve_height
        usable_area = total_area - reserve_area
        usable_efficiency = total_image_area / usable_area * 100
        overall_efficiency = total_image_area / total_area * 100
        
        # Write test log
        log_filename = f"{output_dir}/binary_search_square_reserve_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Binary Search Square with Reserved Space Test\n")
            log_file.write(f"Algorithm: 6-step binary search with top-left reserved area\n")
            log_file.write(f"1. Calculate image area\n")
            log_file.write(f"2. Create square with reserved space\n")
            log_file.write(f"3. Place images in available areas (top-right + bottom)\n")
            log_file.write(f"4. If not all fit, increase square size\n")
            log_file.write(f"5. If all fit, decrease square size\n")
            log_file.write(f"6. Stop at minimum square containing all\n")
            log_file.write(f"\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Total image area: {total_image_area:,} pixels²\n")
            log_file.write(f"Optimal square side: {canvas_size} pixels\n")
            log_file.write(f"Total square area: {total_area:,} pixels²\n")
            log_file.write(f"Reserved space: {reserve_width}x{reserve_height} pixels\n")
            log_file.write(f"Reserved area: {reserve_area:,} pixels²\n")
            log_file.write(f"Usable area: {usable_area:,} pixels²\n")
            log_file.write(f"Layout: Top-right {top_right_grid}, Bottom {bottom_grid}\n")
            log_file.write(f"Usable space efficiency: {usable_efficiency:.1f}%\n")
            log_file.write(f"Overall efficiency: {overall_efficiency:.1f}%\n")
            log_file.write(f"Binary search precision: 1 pixel\n")
            log_file.write(f"Reserved space purpose: Logo, metadata, QR codes, etc.\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Binary search square with reserve test completed. Thumbnail: {thumbnail_result}")
        print(f"Square side: {canvas_size} pixels")
        print(f"Reserved space: {reserve_width}x{reserve_height} pixels (top-left)")
        print(f"Layout: Top-right {top_right_grid}, Bottom {bottom_grid}")
        print(f"Usable efficiency: {usable_efficiency:.1f}%, Overall: {overall_efficiency:.1f}%")
        print(f"All {len(image_files)} images placed successfully")
        
        # Create and copy preview to clipboard
        logger.info("Creating preview and copying to clipboard...")
        create_and_copy_preview(output_dir, reserve_width, reserve_height)
        
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

def create_and_copy_preview(output_dir, reserve_width, reserve_height):
    """Create preview image with reserved space highlighted and copy to clipboard."""
    from PIL import Image, ImageDraw
    import subprocess
    
    input_path = f"{output_dir}/binary_search_square_reserve_test.tif"
    output_path = "binary_search_square_reserve_preview.png"
    
    try:
        with Image.open(input_path) as img:
            # Create a smaller version
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Highlight the reserved space with a border
            draw = ImageDraw.Draw(resized)
            scaled_reserve_width = int(reserve_width * ratio)
            scaled_reserve_height = int(reserve_height * ratio)
            
            # Draw a red rectangle around the reserved space
            draw.rectangle(
                [0, 0, scaled_reserve_width, scaled_reserve_height],
                outline="red",
                width=3
            )
            
            resized.save(output_path, 'PNG')
            print(f"Created preview: {output_path} ({new_width}x{new_height})")
            print(f"Reserved space highlighted in red: {scaled_reserve_width}x{scaled_reserve_height}")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_binary_search_square_with_reserve()
    sys.exit(0 if success else 1)