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

def is_inside_fixed_square_reserve(x, y, rect_width, rect_height, bin_width, bin_height):
    """Check if a tile position overlaps with the fixed 5000x5000 pixel square at center.
    
    Args:
        x, y: Pixel position (top-left of tile)
        rect_width, rect_height: Rectangle dimensions in pixels
        bin_width, bin_height: Tile dimensions in pixels
    """
    # Calculate center of the rectangle in pixels
    center_x = rect_width / 2
    center_y = rect_height / 2
    
    # Fixed 5000x5000 pixel square
    reserve_size = 5000
    half_size = reserve_size / 2
    
    # Reserve square bounds
    reserve_left = center_x - half_size
    reserve_right = center_x + half_size
    reserve_top = center_y - half_size
    reserve_bottom = center_y + half_size
    
    # Tile bounds
    tile_left = x
    tile_right = x + bin_width
    tile_top = y
    tile_bottom = y + bin_height
    
    # Check if tile overlaps with reserve square
    return not (tile_right <= reserve_left or tile_left >= reserve_right or 
                tile_bottom <= reserve_top or tile_top >= reserve_bottom)

def pack_images_with_fixed_square_reserve(num_bins, rect_width, rect_height, bin_width, bin_height):
    """Pack images avoiding the fixed 5000x5000 square at center, top-left to bottom-right order."""
    placements = []
    bins_placed = 0
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    
    # Create list of all valid positions in top-left to bottom-right order
    valid_positions = []
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            
            # Ensure it fits within rectangle
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                # Skip if overlaps with fixed square reserve
                if not is_inside_fixed_square_reserve(x, y, rect_width, rect_height, bin_width, bin_height):
                    valid_positions.append((int(x), int(y), row, col))
    
    # Sort positions: top-left to bottom-right (row first, then column)
    valid_positions.sort(key=lambda pos: (pos[2], pos[3]))  # Sort by row, then column
    
    # Take the first num_bins positions
    for i in range(min(num_bins, len(valid_positions))):
        x, y, row, col = valid_positions[i]
        placements.append((x, y))
        bins_placed += 1
    
    return placements, bins_placed

def find_optimal_rect_for_fixed_reserve(image_files, target_aspect_ratio=1.0/1.29):
    """Find optimal rectangle size for fixed 5000x5000 square reserve."""
    bin_width = 1300
    bin_height = 1900
    num_images = len(image_files)
    
    best_result = None
    best_efficiency = 0
    
    # Binary search for optimal rectangle dimensions
    min_area = num_images * bin_width * bin_height * 1.1  # At least 10% margin
    max_area = num_images * bin_width * bin_height * 2.0  # Up to 100% margin
    
    for area in [min_area + i * (max_area - min_area) / 100 for i in range(101)]:
        # Calculate dimensions based on target aspect ratio
        rect_height = math.sqrt(area / target_aspect_ratio)
        rect_width = area / rect_height
        
        # Pack images
        placements, placed = pack_images_with_fixed_square_reserve(
            num_images, rect_width, rect_height, bin_width, bin_height
        )
        
        if placed == num_images:
            # Calculate efficiency
            total_area = rect_width * rect_height
            image_area = num_images * bin_width * bin_height
            efficiency = image_area / total_area
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_result = {
                    'rect_width': rect_width,
                    'rect_height': rect_height,
                    'placements': placements,
                    'efficiency': efficiency,
                    'area': total_area
                }
    
    return best_result

def test_fixed_5000_reserve():
    """Test packing with fixed 5000x5000 pixel square reserve at center."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_fixed_5000_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Testing fixed 5000x5000 pixel square reserve for {len(image_files)} images")
    
    # Create output directory
    output_dir = "fixed_5000_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Find optimal configuration
    result = find_optimal_rect_for_fixed_reserve(image_files)
    
    if not result:
        logger.error("Could not find optimal configuration")
        return False
    
    rect_width = result['rect_width']
    rect_height = result['rect_height']
    placements = result['placements']
    
    # Calculate statistics
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    total_capacity = total_cols * total_rows
    
    # Count reserved tiles
    reserved_tiles = 0
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                if is_inside_fixed_square_reserve(x, y, rect_width, rect_height, bin_width, bin_height):
                    reserved_tiles += 1
    
    available_capacity = total_capacity - reserved_tiles
    
    total_area = rect_width * rect_height
    image_area = len(image_files) * bin_width * bin_height
    
    # Analyze bottom row filling
    if placements:
        last_row_y = max(p[1] for p in placements)
        bottom_row_images = sum(1 for p in placements if p[1] == last_row_y)
        bottom_row_utilization = bottom_row_images / total_cols * 100
        bottom_empty = rect_height - (last_row_y + bin_height)
    else:
        last_row_y = 0
        bottom_row_images = 0
        bottom_row_utilization = 0
        bottom_empty = rect_height
    
    # Check placement order (first image should be top-left)
    if placements:
        first_image = placements[0]
        logger.info(f"First image position: ({first_image[0]}, {first_image[1]})")
    
    logger.info(f"\nResults for FIXED 5000x5000 SQUARE reserve:")
    logger.info(f"Rectangle: {rect_width:.1f}x{rect_height:.1f}")
    logger.info(f"Aspect ratio (W:H): {rect_width/rect_height:.3f}")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    logger.info(f"Total capacity: {total_capacity} tiles")
    logger.info(f"Reserved (5000x5000 square): {reserved_tiles} tiles")
    logger.info(f"Available: {available_capacity} tiles")
    logger.info(f"Images placed: {len(placements)}")
    logger.info(f"Bottom row: {bottom_row_images}/{total_cols} ({bottom_row_utilization:.1f}%)")
    logger.info(f"Bottom empty: {bottom_empty:.1f} pixels")
    logger.info(f"Overall efficiency: {image_area/total_area*100:.1f}%")
    
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
            self.envelope_shape = EnvelopeShape.RECTANGLE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, rect_width, rect_height)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/fixed_5000_square_test.tif"
    
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
    log_path = Path(f"{output_dir}/fixed_5000_square_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="fixed_5000_square_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_fixed_preview(output_dir, rect_width, rect_height, total_cols, total_rows,
                                    bin_width, bin_height, bottom_row_utilization, rect_width/rect_height)
        
        print(f"FIXED 5000x5000 SQUARE reserve test completed. Thumbnail: {output_path}")
        print(f"Rectangle: {rect_width:.1f}x{rect_height:.1f} (aspect W:H: {rect_width/rect_height:.3f})")
        print(f"Fixed square reserve: {reserved_tiles} tiles (5000x5000 pixels)")
        print(f"First image at: ({placements[0][0]}, {placements[0][1]}) - top-left priority")
        print(f"Bottom row utilization: {bottom_row_utilization:.1f}% ({bottom_row_images}/{total_cols})")
        print(f"Overall efficiency: {image_area/total_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_fixed_preview(output_dir, rect_width, rect_height, total_cols, total_rows,
                                bin_width, bin_height, bottom_util, aspect_ratio):
    """Create preview with fixed 5000x5000 square highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/fixed_5000_square_test.tif"
    output_path = "fixed_5000_square_preview.png"
    
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
            
            # Save a copy without overlay first to check
            resized.save("debug_no_overlay.png", 'PNG')
            print("Saved debug_no_overlay.png to check original image")
            
            # Calculate center and scaled reserve dimensions
            center_x = new_width / 2
            center_y = new_height / 2
            
            # Fixed 5000 pixel square scaled to preview
            reserve_size_scaled = 5000 * ratio
            half_size = reserve_size_scaled / 2
            
            # Calculate center of the preview image
            scaled_center_x = new_width / 2
            scaled_center_y = new_height / 2
            
            # Calculate the correct scaling for the red square
            # Original image is 46667x60201, red square is 5000x5000
            # Preview is 620x800, so red square should be proportionally smaller
            original_width = 46667
            red_square_ratio = 5000 / original_width  # What portion of original width
            scaled_red_size = new_width * red_square_ratio  # Apply same ratio to preview width
            scaled_half_size = scaled_red_size / 2
            
            print(f"Preview size: {new_width}x{new_height}")
            print(f"Preview center: ({scaled_center_x:.0f},{scaled_center_y:.0f})")
            print(f"Red square size: {scaled_red_size:.0f}x{scaled_red_size:.0f}")
            print(f"Red square half-size: {scaled_half_size:.0f}")
            
            # Draw directly on the resized image - solid red for ONLY the reserved area
            draw = ImageDraw.Draw(resized)
            
            # Fill the exact center square that should be empty
            draw.rectangle(
                [scaled_center_x - scaled_half_size, scaled_center_y - scaled_half_size, 
                 scaled_center_x + scaled_half_size, scaled_center_y + scaled_half_size],
                fill='red',  # Solid red fill for reserved area only
                outline='darkred',
                width=2
            )
            
            print(f"Drew red square at center ({scaled_center_x:.0f},{scaled_center_y:.0f}) size {scaled_half_size*2:.0f}x{scaled_half_size*2:.0f}")
            
            # Add text showing info
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 20)
            except:
                font = ImageFont.load_default()
            
            text = f"FIXED 5000x5000\nSquare Reserve\nBottom: {bottom_util:.1f}%\nAspect: {aspect_ratio:.3f}"
            
            # Get the draw object for text
            draw = ImageDraw.Draw(resized)
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
            print(f"5000x5000 square (red area) scaled to: {reserve_size_scaled:.0f}x{reserve_size_scaled:.0f}")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_fixed_5000_reserve()
    sys.exit(0 if success else 1)