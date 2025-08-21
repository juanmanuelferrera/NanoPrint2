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

def is_inside_center_square_reserve(x, y, outer_square_size, inner_square_size, bin_width, bin_height):
    """Check if a tile position overlaps with the center square reserve.
    
    Args:
        x, y: Pixel position (top-left of tile)
        outer_square_size: Outer square side length in pixels
        inner_square_size: Inner square reserve side length in pixels
        bin_width, bin_height: Tile dimensions in pixels
    """
    # Calculate center of the outer square
    center_x = outer_square_size / 2
    center_y = outer_square_size / 2
    
    # Inner square reserve bounds
    inner_half_size = inner_square_size / 2
    inner_left = center_x - inner_half_size
    inner_right = center_x + inner_half_size
    inner_top = center_y - inner_half_size
    inner_bottom = center_y + inner_half_size
    
    # Tile bounds
    tile_left = x
    tile_right = x + bin_width
    tile_top = y
    tile_bottom = y + bin_height
    
    # Check if tile overlaps with inner square reserve
    return not (tile_right <= inner_left or tile_left >= inner_right or 
                tile_bottom <= inner_top or tile_top >= inner_bottom)

def pack_images_in_square_with_square_reserve(num_bins, outer_square_size, inner_square_size, bin_width, bin_height):
    """Pack images in outer square avoiding inner square reserve, top-left to bottom-right order."""
    placements = []
    bins_placed = 0
    
    # Calculate grid dimensions based on outer square
    total_cols = int(outer_square_size / bin_width)
    total_rows = int(outer_square_size / bin_height)
    
    # Create list of all valid positions in top-left to bottom-right order
    valid_positions = []
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            
            # Ensure tile fits within outer square
            if x + bin_width <= outer_square_size and y + bin_height <= outer_square_size:
                # Skip if overlaps with inner square reserve
                if not is_inside_center_square_reserve(x, y, outer_square_size, inner_square_size, bin_width, bin_height):
                    valid_positions.append((int(x), int(y), row, col))
    
    # Sort positions: top-left to bottom-right (row first, then column)
    valid_positions.sort(key=lambda pos: (pos[2], pos[3]))  # Sort by row, then column
    
    # Take the first num_bins positions
    for i in range(min(num_bins, len(valid_positions))):
        x, y, row, col = valid_positions[i]
        placements.append((x, y))
        bins_placed += 1
    
    return placements, bins_placed

def find_optimal_square_with_square_reserve(image_files, inner_square_size=10000):
    """Find optimal outer square size for packing with inner square reserve."""
    bin_width = 1300
    bin_height = 1900
    num_images = len(image_files)
    
    best_result = None
    best_efficiency = 0
    
    # Binary search for optimal outer square size
    min_side = math.sqrt(num_images * bin_width * bin_height) * 1.1  # At least 10% margin
    max_side = math.sqrt(num_images * bin_width * bin_height) * 2.0  # Up to 100% margin
    
    for side_length in [min_side + i * (max_side - min_side) / 100 for i in range(101)]:
        # Pack images
        placements, placed = pack_images_in_square_with_square_reserve(
            num_images, side_length, inner_square_size, bin_width, bin_height
        )
        
        if placed == num_images:
            # Calculate efficiency
            outer_area = side_length * side_length
            image_area = num_images * bin_width * bin_height
            efficiency = image_area / outer_area
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_result = {
                    'outer_square_size': side_length,
                    'placements': placements,
                    'efficiency': efficiency,
                    'outer_area': outer_area
                }
    
    return best_result

def test_square_in_square():
    """Test square packing with square reserve at center."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_square_in_square")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    inner_square_size = 10000
    logger.info(f"Testing square-in-square with {inner_square_size}x{inner_square_size} pixel inner square for {len(image_files)} images")
    
    # Create output directory
    output_dir = "square_in_square_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Find optimal configuration
    result = find_optimal_square_with_square_reserve(image_files, inner_square_size)
    
    if not result:
        logger.error("Could not find optimal configuration")
        return False
    
    outer_square_size = result['outer_square_size']
    placements = result['placements']
    
    # Calculate statistics
    total_cols = int(outer_square_size / bin_width)
    total_rows = int(outer_square_size / bin_height)
    total_capacity = total_cols * total_rows
    
    # Count reserved tiles (inner square)
    inner_reserved_tiles = 0
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            if x + bin_width <= outer_square_size and y + bin_height <= outer_square_size:
                if is_inside_center_square_reserve(x, y, outer_square_size, inner_square_size, bin_width, bin_height):
                    inner_reserved_tiles += 1
    
    available_capacity = total_capacity - inner_reserved_tiles
    
    outer_area = outer_square_size * outer_square_size
    inner_area = inner_square_size * inner_square_size
    available_area = outer_area - inner_area
    image_area = len(image_files) * bin_width * bin_height
    
    # Analyze bottom row filling
    if placements:
        last_row_y = max(p[1] for p in placements)
        bottom_row_images = sum(1 for p in placements if p[1] == last_row_y)
        bottom_row_utilization = bottom_row_images / total_cols * 100
        bottom_empty = outer_square_size - (last_row_y + bin_height)
    else:
        last_row_y = 0
        bottom_row_images = 0
        bottom_row_utilization = 0
        bottom_empty = outer_square_size
    
    # Check placement order (first image should be top-left)
    if placements:
        first_image = placements[0]
        logger.info(f"First image position: ({first_image[0]}, {first_image[1]})")
    
    logger.info(f"\nResults for SQUARE-IN-SQUARE ({inner_square_size}x{inner_square_size} inner):")
    logger.info(f"Outer square: {outer_square_size:.1f}x{outer_square_size:.1f}px")
    logger.info(f"Inner square: {inner_square_size}x{inner_square_size}px")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    logger.info(f"Total capacity: {total_capacity} tiles")
    logger.info(f"Inner square reserved: {inner_reserved_tiles} tiles")
    logger.info(f"Available: {available_capacity} tiles")
    logger.info(f"Images placed: {len(placements)}")
    logger.info(f"Bottom row: {bottom_row_images}/{total_cols} ({bottom_row_utilization:.1f}%)")
    logger.info(f"Bottom empty: {bottom_empty:.1f} pixels")
    logger.info(f"Available area efficiency: {image_area/available_area*100:.1f}%")
    logger.info(f"Overall efficiency: {image_area/outer_area*100:.1f}%")
    
    if len(placements) < len(image_files):
        logger.error(f"Only placed {len(placements)}/{len(image_files)} images!")
        return False
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_width, canvas_height):
            self.rows = total_rows
            self.columns = total_cols
            self.canvas_width = int(canvas_width)
            self.canvas_height = int(canvas_height)
            self.placements = placements
            self.envelope_shape = EnvelopeShape.SQUARE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, outer_square_size, outer_square_size)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/square_in_square_test.tif"
    
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
    log_path = Path(f"{output_dir}/square_in_square_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="square_in_square_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_square_square_preview(output_dir, outer_square_size, inner_square_size, total_cols, total_rows,
                                            bin_width, bin_height, bottom_row_utilization, inner_reserved_tiles)
        
        print(f"SQUARE-IN-SQUARE test completed. Thumbnail: {output_path}")
        print(f"Outer square: {outer_square_size:.1f}x{outer_square_size:.1f}px")
        print(f"Inner square reserve: {inner_reserved_tiles} tiles ({inner_square_size}x{inner_square_size}px)")
        print(f"First image at: ({placements[0][0]}, {placements[0][1]}) - top-left priority")
        print(f"Bottom row utilization: {bottom_row_utilization:.1f}% ({bottom_row_images}/{total_cols})")
        print(f"Available area efficiency: {image_area/available_area*100:.1f}%")
        print(f"Overall efficiency: {image_area/outer_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_square_square_preview(output_dir, outer_square_size, inner_square_size, total_cols, total_rows,
                                        bin_width, bin_height, bottom_util, inner_reserved_tiles):
    """Create preview with outer square and inner square highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/square_in_square_test.tif"
    output_path = "square_in_square_preview.png"
    
    try:
        with Image.open(input_path) as img:
            print(f"Original TIFF: {img.size}, mode: {img.mode}")
            
            # Convert to RGB if it's not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Resized preview: {new_width}x{new_height}")
            
            # Calculate center and scaled dimensions
            scaled_center_x = new_width / 2
            scaled_center_y = new_height / 2
            
            # Calculate scaling for the inner square
            inner_ratio = inner_square_size / outer_square_size
            scaled_inner_size = new_width * inner_ratio
            scaled_inner_half = scaled_inner_size / 2
            
            print(f"Preview size: {new_width}x{new_height}")
            print(f"Preview center: ({scaled_center_x:.0f},{scaled_center_y:.0f})")
            print(f"Red inner square size: {scaled_inner_size:.0f}x{scaled_inner_size:.0f}")
            
            # Draw directly on the resized image
            draw = ImageDraw.Draw(resized)
            
            # Draw the outer square boundary (optional, for reference)
            draw.rectangle(
                [0, 0, new_width-1, new_height-1],
                outline='blue',
                width=3
            )
            
            # Fill the inner square with solid red
            draw.rectangle(
                [scaled_center_x - scaled_inner_half, scaled_center_y - scaled_inner_half,
                 scaled_center_x + scaled_inner_half, scaled_center_y + scaled_inner_half],
                fill='red',  # Solid red fill for inner square reserve
                outline='darkred',
                width=3
            )
            
            print(f"Drew red inner square at center ({scaled_center_x:.0f},{scaled_center_y:.0f}) size {scaled_inner_size:.0f}x{scaled_inner_size:.0f}")
            print(f"Drew blue outer square boundary {new_width}x{new_height}")
            
            # Add text showing info
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 18)
            except:
                font = ImageFont.load_default()
            
            text = f"SQUARE in SQUARE\nOuter: {outer_square_size:.0f}px\nInner: {inner_square_size}px\nBottom: {bottom_util:.1f}%"
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text in bottom-right corner
            text_x = new_width - text_width - 10
            text_y = new_height - text_height - 10
            
            # Draw text background and text
            draw.rectangle(
                [text_x - 5, text_y - 5, text_x + text_width + 5, text_y + text_height + 5],
                fill='white',
                outline='black'
            )
            draw.text((text_x, text_y), text, fill='black', font=font)
            
            # Convert back to RGB for saving
            resized = resized.convert('RGB')
            resized.save(output_path, 'PNG')
            print(f"Created preview: {output_path} ({new_width}x{new_height})")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_square_in_square()
    sys.exit(0 if success else 1)