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

def is_inside_shaped_reserve_pixels(x, y, rect_width, rect_height, shape_type, size_percentage, bin_width, bin_height):
    """Check if a pixel position is inside the shaped reserved area at center.
    
    Args:
        x, y: Pixel position (top-left of tile)
        rect_width, rect_height: Rectangle dimensions in pixels
        shape_type: 'circle', 'square', 'rectangle'
        size_percentage: Size as percentage of envelope width (e.g., 10 for 10%)
        bin_width, bin_height: Tile dimensions in pixels
    """
    # Calculate center of the rectangle in pixels
    center_x = rect_width / 2
    center_y = rect_height / 2
    
    # Calculate tile center position
    tile_center_x = x + bin_width / 2
    tile_center_y = y + bin_height / 2
    
    # Calculate shape dimensions in pixels based on percentage of envelope width
    shape_width_pixels = rect_width * (size_percentage / 100)
    
    if shape_type == 'circle':
        # Circle with radius = shape_width_pixels / 2
        radius = shape_width_pixels / 2
        distance = math.sqrt((tile_center_x - center_x)**2 + (tile_center_y - center_y)**2)
        return distance <= radius
    
    elif shape_type == 'square':
        # Square with side length = shape_width_pixels
        half_size = shape_width_pixels / 2
        return (abs(tile_center_x - center_x) <= half_size and 
                abs(tile_center_y - center_y) <= half_size)
    
    elif shape_type == 'rectangle':
        # Rectangle with width = shape_width_pixels, height = 0.6 * width
        half_width = shape_width_pixels / 2
        half_height = shape_width_pixels * 0.6 / 2
        return (abs(tile_center_x - center_x) <= half_width and 
                abs(tile_center_y - center_y) <= half_height)
    
    return False

def pack_images_with_shaped_reserve(num_bins, rect_width, rect_height, bin_width, bin_height, 
                                  shape_type, size_percentage):
    """Pack images avoiding the shaped reserved area at center, optimizing bottom fill."""
    placements = []
    bins_placed = 0
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    
    # Create list of all possible positions
    all_positions = []
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            
            # Ensure it fits within rectangle
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                # Skip shaped reserved area using pixel-based calculation
                if not is_inside_shaped_reserve_pixels(x, y, rect_width, rect_height, shape_type, size_percentage, bin_width, bin_height):
                    all_positions.append((int(x), int(y), row))
    
    # Sort positions to prioritize bottom rows (higher row numbers first for bottom optimization)
    all_positions.sort(key=lambda pos: (-pos[2], pos[0]))  # Sort by row descending, then x ascending
    
    # Take the first num_bins positions
    for i in range(min(num_bins, len(all_positions))):
        x, y, row = all_positions[i]
        placements.append((x, y))
        bins_placed += 1
    
    return placements, bins_placed

def find_optimal_shaped_reserve(image_files, shape_type, size_percentage, target_aspect_ratio=1.0/1.29):
    """Find optimal rectangle size for shaped reserve with given percentage."""
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
        placements, placed = pack_images_with_shaped_reserve(
            num_images, rect_width, rect_height, bin_width, bin_height, 
            shape_type, size_percentage
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
                    'size_percentage': size_percentage,
                    'placements': placements,
                    'efficiency': efficiency,
                    'area': total_area
                }
    
    return best_result

def test_shaped_reserve(shape_type, size_percentage=10):
    """Test packing with shaped reserved space."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(f"test_shaped_reserve_{shape_type}")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Testing {shape_type} shaped reserve ({size_percentage}% width) for {len(image_files)} images")
    
    # Create output directory
    output_dir = f"{shape_type}_{size_percentage}pct_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Find optimal configuration
    result = find_optimal_shaped_reserve(image_files, shape_type, size_percentage)
    
    if not result:
        logger.error("Could not find optimal configuration")
        return False
    
    rect_width = result['rect_width']
    rect_height = result['rect_height']
    size_percentage = result['size_percentage']
    placements = result['placements']
    
    # Calculate statistics
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    total_capacity = total_cols * total_rows
    
    # Count reserved tiles using pixel-based calculation
    reserved_tiles = 0
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                if is_inside_shaped_reserve_pixels(x, y, rect_width, rect_height, shape_type, size_percentage, bin_width, bin_height):
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
    
    logger.info(f"\nResults for {shape_type.upper()} shaped reserve:")
    logger.info(f"Rectangle: {rect_width:.1f}x{rect_height:.1f}")
    logger.info(f"Aspect ratio (W:H): {rect_width/rect_height:.3f}")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    logger.info(f"Total capacity: {total_capacity} tiles")
    # Calculate exact pixel dimensions of the shape
    shape_width_pixels = rect_width * (size_percentage / 100)
    if shape_type == 'circle':
        shape_desc = f"circle diameter {shape_width_pixels:.0f}px"
    elif shape_type == 'square':
        shape_desc = f"square {shape_width_pixels:.0f}x{shape_width_pixels:.0f}px"
    elif shape_type == 'rectangle':
        shape_height_pixels = shape_width_pixels * 0.6
        shape_desc = f"rectangle {shape_width_pixels:.0f}x{shape_height_pixels:.0f}px"
    
    logger.info(f"Reserved ({shape_type}): {reserved_tiles} tiles ({size_percentage}% width = {shape_desc})")
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
    output_filename = f"{output_dir}/{shape_type}_{size_percentage}pct_reserve_test.tif"
    
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
    log_path = Path(f"{output_dir}/{shape_type}_{size_percentage}pct_reserve_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name=f"{shape_type}_{size_percentage}pct_reserve_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_shaped_preview(output_dir, shape_type, size_percentage, total_cols, total_rows,
                                     bin_width, bin_height, bottom_row_utilization, rect_width/rect_height, rect_width)
        
        print(f"{shape_type.upper()} shaped reserve test completed. Thumbnail: {output_path}")
        print(f"Rectangle: {rect_width:.1f}x{rect_height:.1f} (aspect W:H: {rect_width/rect_height:.3f})")
        print(f"{shape_type.upper()} reserve: {reserved_tiles} tiles ({shape_desc})")
        print(f"Bottom row utilization: {bottom_row_utilization:.1f}% ({bottom_row_images}/{total_cols})")
        print(f"Overall efficiency: {image_area/total_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_shaped_preview(output_dir, shape_type, size_percentage, total_cols, total_rows,
                                 bin_width, bin_height, bottom_util, aspect_ratio, rect_width):
    """Create preview with shaped reserved space highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/{shape_type}_{size_percentage}pct_reserve_test.tif"
    output_path = f"{shape_type}_{size_percentage}pct_reserve_preview.png"
    
    try:
        with Image.open(input_path) as img:
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Calculate scaled tile dimensions
            scaled_bin_width = int(bin_width * ratio)
            scaled_bin_height = int(bin_height * ratio)
            
            # Create semi-transparent overlay for reserved area
            overlay = Image.new('RGBA', resized.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Calculate shaped reserve area based on percentage
            center_col = total_cols / 2
            center_row = total_rows / 2
            
            # Calculate shape size in pixels based on percentage of envelope width
            shape_width_pixels = rect_width * (size_percentage / 100)
            shape_size_scaled = shape_width_pixels * ratio  # Convert to scaled pixels
            
            center_x = int(center_col * scaled_bin_width)
            center_y = int(center_row * scaled_bin_height)
            
            if shape_type == 'circle':
                # Draw circle - radius is half the diameter
                radius = int(shape_size_scaled / 2)
                print(f"Drawing circle: center=({center_x},{center_y}), radius={radius}, scaled_size={shape_size_scaled}")
                overlay_draw.ellipse(
                    [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                    fill=(255, 0, 0, 100)  # Semi-transparent red
                )
                # Also draw a border to make it more visible
                overlay_draw.ellipse(
                    [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                    outline=(255, 0, 0, 200),
                    width=3
                )
                
            elif shape_type == 'square':
                # Draw square
                half_size = int(shape_size_scaled / 2)
                overlay_draw.rectangle(
                    [center_x - half_size, center_y - half_size, center_x + half_size, center_y + half_size], 
                    fill=(0, 255, 0, 100)  # Green
                )
                
            elif shape_type == 'rectangle':
                # Draw rectangle (width = percentage, height = 0.6 * width)
                half_width = int(shape_size_scaled / 2)
                half_height = int(shape_size_scaled * 0.6 / 2)
                overlay_draw.rectangle(
                    [center_x - half_width, center_y - half_height, center_x + half_width, center_y + half_height], 
                    fill=(0, 0, 255, 100)  # Blue
                )
            
            # Composite the overlay
            resized = resized.convert('RGBA')
            resized = Image.alpha_composite(resized, overlay)
            
            # Add text showing info
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 20)
            except:
                font = ImageFont.load_default()
            
            text = f"{shape_type.upper()} Reserve\n{size_percentage}% width\nBottom: {bottom_util:.1f}%\nAspect: {aspect_ratio:.3f}"
            # Create draw object first
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
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        shape_type = sys.argv[1].lower()
    else:
        shape_type = 'circle'  # Default to circle
    
    if len(sys.argv) > 2:
        size_percentage = int(sys.argv[2])
    else:
        size_percentage = 10  # Default to 10%
    
    if shape_type not in ['circle', 'square', 'rectangle']:
        print("Usage: python test_shaped_reserve.py [circle|square|rectangle] [percentage]")
        sys.exit(1)
    
    success = test_shaped_reserve(shape_type, size_percentage)
    sys.exit(0 if success else 1)