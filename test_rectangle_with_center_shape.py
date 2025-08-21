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

def is_inside_center_shape(x, y, bin_width, bin_height, rect_width, rect_height, shape_type="circle", shape_size=3):
    """Check if a tile position overlaps with the center shape."""
    
    # Calculate tile center
    tile_center_x = x + bin_width // 2
    tile_center_y = y + bin_height // 2
    
    # Calculate rectangle center
    rect_center_x = rect_width // 2
    rect_center_y = rect_height // 2
    
    if shape_type == "circle":
        # Circle radius in pixels (shape_size is in "tile units")
        radius = shape_size * min(bin_width, bin_height) // 2
        
        # Distance from tile center to rectangle center
        dx = tile_center_x - rect_center_x
        dy = tile_center_y - rect_center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= radius
        
    elif shape_type == "square":
        # Square half-size in pixels
        half_size = shape_size * min(bin_width, bin_height) // 2
        
        # Check if tile center is within square bounds
        dx = abs(tile_center_x - rect_center_x)
        dy = abs(tile_center_y - rect_center_y)
        
        return dx <= half_size and dy <= half_size
        
    elif shape_type == "diamond":
        # Diamond (rotated square) half-size in pixels
        half_size = shape_size * min(bin_width, bin_height) // 2
        
        # Manhattan distance for diamond shape
        dx = abs(tile_center_x - rect_center_x)
        dy = abs(tile_center_y - rect_center_y)
        
        return (dx + dy) <= half_size
        
    return False

def pack_images_with_dual_exclusions(num_bins, rect_width, rect_height, bin_width, bin_height, 
                                   reserve_cols, reserve_rows, center_shape_type="circle", center_shape_size=3):
    """Pack images avoiding both corner reserve and center shape."""
    
    placements = []
    bins_placed = 0
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    
    # Place images row by row, skipping both exclusion zones
    for row in range(total_rows):
        if bins_placed >= num_bins:
            break
            
        for col in range(total_cols):
            if bins_placed >= num_bins:
                break
                
            # Calculate position
            x = col * bin_width
            y = row * bin_height
            
            # Skip corner reserved area (top-left)
            if row < reserve_rows and col < reserve_cols:
                continue
            
            # Skip center shape area
            if is_inside_center_shape(x, y, bin_width, bin_height, rect_width, rect_height, 
                                    center_shape_type, center_shape_size):
                continue
            
            # Ensure it fits within rectangle
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements, bins_placed

def calculate_exclusion_stats(rect_width, rect_height, bin_width, bin_height, 
                            reserve_cols, reserve_rows, center_shape_type, center_shape_size):
    """Calculate how many tiles are excluded by each zone."""
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    total_capacity = total_cols * total_rows
    
    # Count corner reserve tiles
    corner_tiles = reserve_cols * reserve_rows
    
    # Count center shape tiles
    center_tiles = 0
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            
            # Skip corner area when counting center (avoid double counting)
            if row < reserve_rows and col < reserve_cols:
                continue
                
            if is_inside_center_shape(x, y, bin_width, bin_height, rect_width, rect_height, 
                                    center_shape_type, center_shape_size):
                center_tiles += 1
    
    available_tiles = total_capacity - corner_tiles - center_tiles
    
    return {
        'total_capacity': total_capacity,
        'corner_tiles': corner_tiles, 
        'center_tiles': center_tiles,
        'available_tiles': available_tiles,
        'total_excluded': corner_tiles + center_tiles
    }

def test_rectangle_with_center_shape():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_rectangle_with_center_shape")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Testing rectangle with corner reserve + center shape for {len(image_files)} images")
    
    # Create output directory
    output_dir = "rectangle_center_shape_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Use the optimal rectangle from previous tests
    rect_width = 45502.8
    rect_height = 58698.6
    target_aspect_ratio = rect_width / rect_height
    
    # Use optimal corner reserve
    reserve_rows = 4
    reserve_cols = 4
    
    # Center shape parameters
    center_shape_type = "circle"  # Options: "circle", "square", "diamond"
    center_shape_size = 4  # Size in tile units
    
    logger.info(f"Rectangle: {rect_width:.1f}x{rect_height:.1f}")
    logger.info(f"Corner reserve: {reserve_rows}x{reserve_cols} tiles")
    logger.info(f"Center shape: {center_shape_type} (size {center_shape_size} tile units)")
    
    # Calculate exclusion statistics
    stats = calculate_exclusion_stats(rect_width, rect_height, bin_width, bin_height,
                                    reserve_cols, reserve_rows, center_shape_type, center_shape_size)
    
    logger.info(f"Exclusion zones:")
    logger.info(f"  Total capacity: {stats['total_capacity']} tiles")
    logger.info(f"  Corner reserve: {stats['corner_tiles']} tiles")
    logger.info(f"  Center shape: {stats['center_tiles']} tiles")
    logger.info(f"  Total excluded: {stats['total_excluded']} tiles")
    logger.info(f"  Available: {stats['available_tiles']} tiles")
    
    # Pack images with dual exclusions
    placements, placed = pack_images_with_dual_exclusions(
        len(image_files), rect_width, rect_height, bin_width, bin_height,
        reserve_cols, reserve_rows, center_shape_type, center_shape_size
    )
    
    # Calculate final statistics
    total_area = rect_width * rect_height
    corner_area = reserve_cols * bin_width * reserve_rows * bin_height
    
    # Estimate center shape area (approximate)
    if center_shape_type == "circle":
        shape_radius = center_shape_size * min(bin_width, bin_height) // 2
        center_area = math.pi * shape_radius * shape_radius
    elif center_shape_type == "square":
        shape_size = center_shape_size * min(bin_width, bin_height)
        center_area = shape_size * shape_size
    elif center_shape_type == "diamond":
        shape_size = center_shape_size * min(bin_width, bin_height)
        center_area = shape_size * shape_size // 2  # Diamond is half area of circumscribing square
    
    excluded_area = corner_area + center_area
    available_area = total_area - excluded_area
    image_area = len(image_files) * bin_width * bin_height
    
    # Analyze bottom row filling
    if placements:
        total_cols = int(rect_width / bin_width)
        last_row_y = max(p[1] for p in placements)
        bottom_row_images = sum(1 for p in placements if p[1] == last_row_y)
        bottom_row_utilization = bottom_row_images / total_cols * 100
        bottom_empty = rect_height - (last_row_y + bin_height)
    else:
        bottom_row_images = 0
        bottom_row_utilization = 0
        bottom_empty = rect_height
    
    logger.info(f"\nResults:")
    logger.info(f"Images placed: {placed}/{len(image_files)}")
    logger.info(f"Bottom row: {bottom_row_images}/{int(rect_width / bin_width)} ({bottom_row_utilization:.1f}%)")
    logger.info(f"Bottom empty: {bottom_empty:.1f} pixels")
    logger.info(f"Available space efficiency: {(placed * bin_width * bin_height)/available_area*100:.1f}%")
    logger.info(f"Overall efficiency: {(placed * bin_width * bin_height)/total_area*100:.1f}%")
    
    if placed < len(image_files):
        logger.warning(f"Could not place all images! Missing: {len(image_files) - placed}")
        # Try with larger rectangle
        return test_with_larger_rectangle(image_files, reserve_cols, reserve_rows, 
                                        center_shape_type, center_shape_size, output_dir)
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_width, canvas_height):
            total_cols = int(canvas_width / bin_width)
            total_rows = int(canvas_height / bin_height)
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
    output_filename = f"{output_dir}/rectangle_center_shape_test.tif"
    
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
    log_path = Path(f"{output_dir}/rectangle_center_shape_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="rectangle_center_shape_test",
        approved=False
    )
    
    # Check if file was created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_preview_center_shape(output_dir, rect_width, rect_height, 
                                            reserve_cols * bin_width, reserve_rows * bin_height,
                                            center_shape_type, center_shape_size,
                                            bin_width, bin_height, bottom_row_utilization)
        
        print(f"Rectangle with center shape test completed. Thumbnail: {output_path}")
        print(f"Rectangle: {rect_width:.1f}x{rect_height:.1f}")
        print(f"Corner reserve: {reserve_cols}x{reserve_rows} tiles")
        print(f"Center {center_shape_type}: size {center_shape_size}")
        print(f"Images placed: {placed}/{len(image_files)}")
        print(f"Bottom row utilization: {bottom_row_utilization:.1f}%")
        print(f"Available efficiency: {(placed * bin_width * bin_height)/available_area*100:.1f}%, Overall: {(placed * bin_width * bin_height)/total_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail")
        return False

def test_with_larger_rectangle(image_files, reserve_cols, reserve_rows, center_shape_type, center_shape_size, output_dir):
    """Test with a larger rectangle when images don't fit."""
    
    logger = logging.getLogger("test_larger_rectangle")
    
    bin_width = 1300
    bin_height = 1900
    
    # Try 10% larger rectangle
    rect_width = 45502.8 * 1.1
    rect_height = 58698.6 * 1.1
    
    logger.info(f"Trying larger rectangle: {rect_width:.1f}x{rect_height:.1f}")
    
    placements, placed = pack_images_with_dual_exclusions(
        len(image_files), rect_width, rect_height, bin_width, bin_height,
        reserve_cols, reserve_rows, center_shape_type, center_shape_size
    )
    
    logger.info(f"Larger rectangle result: {placed}/{len(image_files)} images placed")
    
    if placed >= len(image_files):
        logger.info("Success with larger rectangle!")
        # Could implement full rendering here if needed
        return True
    else:
        logger.error(f"Still couldn't fit all images even with larger rectangle")
        return False

def create_and_copy_preview_center_shape(output_dir, rect_width, rect_height, reserve_width, reserve_height,
                                        center_shape_type, center_shape_size, bin_width, bin_height, bottom_util):
    """Create preview with both corner reserve and center shape highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/rectangle_center_shape_test.tif"
    output_path = "rectangle_center_shape_preview.png"
    
    try:
        with Image.open(input_path) as img:
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Calculate scaled dimensions
            scaled_reserve_width = int(reserve_width * ratio)
            scaled_reserve_height = int(reserve_height * ratio)
            
            # Create overlay for both exclusion zones
            overlay = Image.new('RGBA', resized.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Draw corner reserve (green)
            overlay_draw.rectangle(
                [0, 0, scaled_reserve_width, scaled_reserve_height],
                fill=(0, 255, 0, 100)
            )
            
            # Draw center shape (blue)
            center_x = new_width // 2
            center_y = new_height // 2
            shape_radius = int(center_shape_size * min(bin_width, bin_height) * ratio // 2)
            
            if center_shape_type == "circle":
                overlay_draw.ellipse(
                    [center_x - shape_radius, center_y - shape_radius,
                     center_x + shape_radius, center_y + shape_radius],
                    fill=(0, 0, 255, 100)
                )
            elif center_shape_type == "square":
                overlay_draw.rectangle(
                    [center_x - shape_radius, center_y - shape_radius,
                     center_x + shape_radius, center_y + shape_radius],
                    fill=(0, 0, 255, 100)
                )
            elif center_shape_type == "diamond":
                # Draw diamond as polygon
                points = [
                    (center_x, center_y - shape_radius),  # top
                    (center_x + shape_radius, center_y),  # right
                    (center_x, center_y + shape_radius),  # bottom
                    (center_x - shape_radius, center_y)   # left
                ]
                overlay_draw.polygon(points, fill=(0, 0, 255, 100))
            
            # Composite the overlay
            resized = resized.convert('RGBA')
            resized = Image.alpha_composite(resized, overlay)
            
            # Draw borders
            draw = ImageDraw.Draw(resized)
            
            # Green border for corner reserve
            draw.rectangle(
                [0, 0, scaled_reserve_width-1, scaled_reserve_height-1],
                outline='green',
                width=3
            )
            
            # Blue border for center shape
            if center_shape_type == "circle":
                draw.ellipse(
                    [center_x - shape_radius, center_y - shape_radius,
                     center_x + shape_radius, center_y + shape_radius],
                    outline='blue',
                    width=3
                )
            elif center_shape_type == "square":
                draw.rectangle(
                    [center_x - shape_radius, center_y - shape_radius,
                     center_x + shape_radius, center_y + shape_radius],
                    outline='blue',
                    width=3
                )
            elif center_shape_type == "diamond":
                points = [
                    (center_x, center_y - shape_radius),
                    (center_x + shape_radius, center_y),
                    (center_x, center_y + shape_radius),
                    (center_x - shape_radius, center_y),
                    (center_x, center_y - shape_radius)  # Close the shape
                ]
                draw.line(points, fill='blue', width=3)
            
            # Add text
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 18)
            except:
                font = ImageFont.load_default()
            
            text = f"Corner + Center\n{center_shape_type.title()}\nBottom: {bottom_util:.1f}%"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text in bottom-right corner
            text_x = new_width - text_width - 10
            text_y = new_height - text_height - 10
            
            # Draw text background
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
            print(f"Green = corner reserve, Blue = center {center_shape_type}")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_rectangle_with_center_shape()
    sys.exit(0 if success else 1)