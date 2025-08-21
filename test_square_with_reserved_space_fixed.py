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

def calculate_reserved_space_dimensions(square_side, reserve_aspect_ratio):
    """Calculate reserved space dimensions with given aspect ratio."""
    # Reserve space equivalent to ~2 image areas for visibility
    reserve_area = 2.0 * 1300 * 1900  
    
    # Calculate dimensions with correct aspect ratio
    reserve_height = math.sqrt(reserve_area / reserve_aspect_ratio)
    reserve_width = reserve_height * reserve_aspect_ratio
    
    # Ensure it doesn't exceed 25% of square dimension
    max_dimension = square_side * 0.25
    if reserve_width > max_dimension:
        reserve_width = max_dimension
        reserve_height = reserve_width / reserve_aspect_ratio
    if reserve_height > max_dimension:
        reserve_height = max_dimension
        reserve_width = reserve_height * reserve_aspect_ratio
    
    return int(reserve_width), int(reserve_height)

def pack_images_in_available_space(num_bins, square_side, bin_width, bin_height, reserve_width, reserve_height):
    """Pack images in available space (excluding reserved top-left area)."""
    
    placements = []
    bins_placed = 0
    
    # Available area is L-shaped:
    # 1. Top strip: from (reserve_width, 0) to (square_side, reserve_height)  
    # 2. Bottom area: from (0, reserve_height) to (square_side, square_side)
    
    # Calculate available columns and rows
    cols_total = int(square_side / bin_width)
    rows_total = int(square_side / bin_height)
    
    # Calculate reserved area in grid terms
    reserve_cols = int(math.ceil(reserve_width / bin_width))
    reserve_rows = int(math.ceil(reserve_height / bin_height))
    
    # Place images row by row, column by column, but skip reserved area
    for row in range(rows_total):
        if bins_placed >= num_bins:
            break
            
        for col in range(cols_total):
            if bins_placed >= num_bins:
                break
                
            # Skip reserved area (top-left)
            if row < reserve_rows and col < reserve_cols:
                continue  # This cell is in reserved space
            
            # Calculate position
            x = col * bin_width
            y = row * bin_height
            
            # Ensure it fits within square
            if x + bin_width <= square_side and y + bin_height <= square_side:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements, bins_placed

def find_minimal_square_with_reserve(num_bins, bin_width, bin_height, reserve_aspect_ratio):
    """Find the minimal square that fits all images with reserved space."""
    
    logger = logging.getLogger("minimal_square_with_reserve")
    
    # Start with a reasonable estimate
    # Total image area + some reserve area
    total_image_area = num_bins * bin_width * bin_height
    estimated_side = math.sqrt(total_image_area * 1.2)  # 20% overhead for reserve
    
    logger.info(f"Starting search from estimated side: {estimated_side:.1f}")
    
    # Binary search for minimal square
    side_min = estimated_side * 0.8
    side_max = estimated_side * 2.0
    
    # Find working upper bound
    while side_max <= estimated_side * 3.0:
        reserve_w, reserve_h = calculate_reserved_space_dimensions(side_max, reserve_aspect_ratio)
        placements, placed = pack_images_in_available_space(
            num_bins, side_max, bin_width, bin_height, reserve_w, reserve_h
        )
        if placed >= num_bins:
            break
        side_max += estimated_side * 0.5
    
    logger.info(f"Search bounds: {side_min:.1f} to {side_max:.1f}")
    
    best_side = side_max
    best_placements = None
    best_reserve_dims = None
    iterations = 0
    
    # Binary search
    while side_max - side_min > 1 and iterations < 50:
        side_mid = (side_min + side_max) / 2
        reserve_w, reserve_h = calculate_reserved_space_dimensions(side_mid, reserve_aspect_ratio)
        
        placements, placed = pack_images_in_available_space(
            num_bins, side_mid, bin_width, bin_height, reserve_w, reserve_h
        )
        
        total_area = side_mid * side_mid
        reserve_area = reserve_w * reserve_h
        available_area = total_area - reserve_area
        efficiency = (num_bins * bin_width * bin_height) / available_area * 100
        overall_efficiency = (num_bins * bin_width * bin_height) / total_area * 100
        
        logger.info(f"Iteration {iterations}: side={side_mid:.1f}, reserve={reserve_w}x{reserve_h}, "
                   f"placed={placed}/{num_bins}, efficiency={efficiency:.1f}%, overall={overall_efficiency:.1f}%")
        
        if placed >= num_bins:
            # All fit - try smaller
            best_side = side_mid
            best_placements = placements
            best_reserve_dims = (reserve_w, reserve_h)
            side_max = side_mid
        else:
            # Need bigger
            side_min = side_mid
        
        iterations += 1
    
    return best_side, best_placements, best_reserve_dims

def test_square_with_reserved_space_fixed():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_square_with_reserved_space_fixed")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images with reserved space (FIXED approach)")
    
    # Create output directory
    output_dir = "square_reserve_fixed_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Reserve space aspect ratio (same as images)
    reserve_aspect_ratio = bin_width / bin_height  # 1300/1900
    
    logger.info(f"Bin dimensions: {bin_width}x{bin_height}")
    logger.info(f"Reserved space aspect ratio: {reserve_aspect_ratio:.3f} (same as images)")
    
    # Find minimal square with reserved space
    side_length, placements, (reserve_width, reserve_height) = find_minimal_square_with_reserve(
        len(image_files), bin_width, bin_height, reserve_aspect_ratio
    )
    
    canvas_size = int(side_length)
    total_area = canvas_size * canvas_size
    reserve_area = reserve_width * reserve_height
    available_area = total_area - reserve_area
    image_area = len(image_files) * bin_width * bin_height
    
    logger.info(f"Final results:")
    logger.info(f"Square side: {canvas_size} pixels")
    logger.info(f"Reserved space: {reserve_width}x{reserve_height} pixels")
    logger.info(f"Total area: {total_area:,} pixels²")
    logger.info(f"Reserved area: {reserve_area:,} pixels²")
    logger.info(f"Available area: {available_area:,} pixels²")
    logger.info(f"Image area: {image_area:,} pixels²")
    logger.info(f"Available space efficiency: {image_area/available_area*100:.1f}%")
    logger.info(f"Overall efficiency: {image_area/total_area*100:.1f}%")
    logger.info(f"Placed {len(placements)} out of {len(image_files)} images")
    
    # Verify last image is at bottom corner
    if placements:
        last_placement = max(placements, key=lambda p: p[1] * 100000 + p[0])  # Sort by y then x
        logger.info(f"Last image position: ({last_placement[0]}, {last_placement[1]})")
        logger.info(f"Last image bottom-right: ({last_placement[0] + bin_width}, {last_placement[1] + bin_height})")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_size):
            self.rows = 0
            self.columns = 0
            self.canvas_width = canvas_size
            self.canvas_height = canvas_size
            self.placements = placements
            self.envelope_shape = EnvelopeShape.SQUARE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, canvas_size)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/square_reserve_fixed_test.tif"
    
    # Create image bins
    image_bins = []
    for i, image_path in enumerate(image_files[:len(placements)]):
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate TIFF
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/square_reserve_fixed_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="square_reserve_fixed_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Write detailed log
        log_filename = f"{output_dir}/square_reserve_fixed_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Square with Reserved Space (FIXED) Test\n")
            log_file.write(f"Approach: Reserved area completely off-limits to images\n")
            log_file.write(f"Packing: Images fill available space row by row\n")
            log_file.write(f"Last image: Positioned at bottom-right corner\n")
            log_file.write(f"\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Images placed: {len(placements)}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Square side: {canvas_size} pixels\n")
            log_file.write(f"Reserved space: {reserve_width}x{reserve_height} pixels (top-left)\n")
            log_file.write(f"Reserved aspect ratio: {reserve_aspect_ratio:.3f}\n")
            log_file.write(f"Total area: {total_area:,} pixels²\n")
            log_file.write(f"Reserved area: {reserve_area:,} pixels²\n")
            log_file.write(f"Available area: {available_area:,} pixels²\n")
            log_file.write(f"Image area: {image_area:,} pixels²\n")
            log_file.write(f"Available space efficiency: {image_area/available_area*100:.1f}%\n")
            log_file.write(f"Overall efficiency: {image_area/total_area*100:.1f}%\n")
            if placements:
                last_pos = max(placements, key=lambda p: p[1] * 100000 + p[0])
                log_file.write(f"Last image position: ({last_pos[0]}, {last_pos[1]})\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        # Create preview and copy to clipboard
        create_and_copy_preview_fixed(output_dir, reserve_width, reserve_height)
        
        print(f"Fixed square with reserve test completed. Thumbnail: {thumbnail_result}")
        print(f"Square: {canvas_size}x{canvas_size}, Reserve: {reserve_width}x{reserve_height}")
        print(f"Available efficiency: {image_area/available_area*100:.1f}%, Overall: {image_area/total_area*100:.1f}%")
        print(f"All {len(image_files)} images placed in available space")
        
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

def create_and_copy_preview_fixed(output_dir, reserve_width, reserve_height):
    """Create preview with reserved space clearly marked."""
    from PIL import Image, ImageDraw
    import subprocess
    
    input_path = f"{output_dir}/square_reserve_fixed_test.tif"
    output_path = "square_reserve_fixed_preview.png"
    
    try:
        with Image.open(input_path) as img:
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Draw reserved space outline
            draw = ImageDraw.Draw(resized)
            scaled_reserve_width = int(reserve_width * ratio)
            scaled_reserve_height = int(reserve_height * ratio)
            
            # Fill reserved area with semi-transparent overlay
            overlay = Image.new('RGBA', (scaled_reserve_width, scaled_reserve_height), (255, 0, 0, 64))
            resized.paste(overlay, (0, 0), overlay)
            
            # Draw red border around reserved space
            draw.rectangle(
                [0, 0, scaled_reserve_width-1, scaled_reserve_height-1],
                outline="red",
                width=4
            )
            
            resized.save(output_path, 'PNG')
            print(f"Created preview: {output_path} ({new_width}x{new_height})")
            print(f"Reserved space (red area): {scaled_reserve_width}x{scaled_reserve_height}")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_square_with_reserved_space_fixed()
    sys.exit(0 if success else 1)