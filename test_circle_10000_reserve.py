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

def is_inside_circle_with_square_reserve(x, y, circle_center_x, circle_center_y, circle_radius, 
                                       square_reserve_size, bin_width, bin_height):
    """Check if a tile position is inside the circle OR overlaps with the center square reserve.
    
    Args:
        x, y: Pixel position (top-left of tile)
        circle_center_x, circle_center_y: Circle center coordinates
        circle_radius: Circle radius in pixels
        square_reserve_size: Square reserve side length in pixels
        bin_width, bin_height: Tile dimensions in pixels
    """
    # Calculate tile center position
    tile_center_x = x + bin_width / 2
    tile_center_y = y + bin_height / 2
    
    # Check if tile center is outside the circle
    distance_from_circle_center = math.sqrt((tile_center_x - circle_center_x)**2 + (tile_center_y - circle_center_y)**2)
    if distance_from_circle_center > circle_radius:
        return True  # Outside circle, exclude
    
    # Check if tile overlaps with center square reserve
    square_half_size = square_reserve_size / 2
    square_left = circle_center_x - square_half_size
    square_right = circle_center_x + square_half_size
    square_top = circle_center_y - square_half_size
    square_bottom = circle_center_y + square_half_size
    
    # Tile bounds
    tile_left = x
    tile_right = x + bin_width
    tile_top = y
    tile_bottom = y + bin_height
    
    # Check if tile overlaps with square reserve
    if not (tile_right <= square_left or tile_left >= square_right or 
            tile_bottom <= square_top or tile_top >= square_bottom):
        return True  # Overlaps with square reserve, exclude
    
    return False  # Inside circle and doesn't overlap square reserve

def pack_images_in_circle_with_square_reserve(num_bins, circle_radius, square_reserve_size, bin_width, bin_height):
    """Pack images in circle avoiding center square reserve, top-left to bottom-right order."""
    placements = []
    bins_placed = 0
    
    # Circle dimensions
    circle_diameter = circle_radius * 2
    circle_center_x = circle_radius
    circle_center_y = circle_radius
    
    # Calculate grid dimensions based on circle diameter
    total_cols = int(circle_diameter / bin_width)
    total_rows = int(circle_diameter / bin_height)
    
    # Create list of all valid positions in top-left to bottom-right order
    valid_positions = []
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            
            # Ensure tile fits within circle diameter bounds
            if x + bin_width <= circle_diameter and y + bin_height <= circle_diameter:
                # Skip if outside circle or overlaps with square reserve
                if not is_inside_circle_with_square_reserve(x, y, circle_center_x, circle_center_y, 
                                                          circle_radius, square_reserve_size, bin_width, bin_height):
                    valid_positions.append((int(x), int(y), row, col))
    
    # Sort positions: top-left to bottom-right (row first, then column)
    valid_positions.sort(key=lambda pos: (pos[2], pos[3]))  # Sort by row, then column
    
    # Take the first num_bins positions
    for i in range(min(num_bins, len(valid_positions))):
        x, y, row, col = valid_positions[i]
        placements.append((x, y))
        bins_placed += 1
    
    return placements, bins_placed, circle_diameter

def find_optimal_circle_with_square_reserve(image_files, square_reserve_size=10000):
    """Find optimal circle size for packing with square reserve."""
    bin_width = 1300
    bin_height = 1900
    num_images = len(image_files)
    
    best_result = None
    best_efficiency = 0
    
    # Binary search for optimal circle radius
    min_radius = math.sqrt(num_images * bin_width * bin_height / math.pi) * 1.1  # At least 10% margin
    max_radius = math.sqrt(num_images * bin_width * bin_height / math.pi) * 2.0  # Up to 100% margin
    
    for radius in [min_radius + i * (max_radius - min_radius) / 100 for i in range(101)]:
        # Pack images
        placements, placed, circle_diameter = pack_images_in_circle_with_square_reserve(
            num_images, radius, square_reserve_size, bin_width, bin_height
        )
        
        if placed == num_images:
            # Calculate efficiency
            circle_area = math.pi * radius * radius
            image_area = num_images * bin_width * bin_height
            efficiency = image_area / circle_area
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_result = {
                    'circle_radius': radius,
                    'circle_diameter': circle_diameter,
                    'placements': placements,
                    'efficiency': efficiency,
                    'circle_area': circle_area
                }
    
    return best_result

def test_circle_10000_reserve():
    """Test circle packing with 10000x10000 pixel square reserve at center."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_circle_10000_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    square_reserve_size = 10000
    logger.info(f"Testing circle with {square_reserve_size}x{square_reserve_size} pixel square reserve for {len(image_files)} images")
    
    # Create output directory
    output_dir = "circle_10000_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Find optimal configuration
    result = find_optimal_circle_with_square_reserve(image_files, square_reserve_size)
    
    if not result:
        logger.error("Could not find optimal configuration")
        return False
    
    circle_radius = result['circle_radius']
    circle_diameter = result['circle_diameter']
    placements = result['placements']
    
    # Calculate statistics
    total_cols = int(circle_diameter / bin_width)
    total_rows = int(circle_diameter / bin_height)
    total_capacity = total_cols * total_rows
    
    # Count reserved tiles (square reserve + outside circle)
    circle_center_x = circle_radius
    circle_center_y = circle_radius
    reserved_tiles = 0
    square_reserved_tiles = 0
    outside_circle_tiles = 0
    
    for row in range(total_rows):
        for col in range(total_cols):
            x = col * bin_width
            y = row * bin_height
            if x + bin_width <= circle_diameter and y + bin_height <= circle_diameter:
                if is_inside_circle_with_square_reserve(x, y, circle_center_x, circle_center_y, 
                                                      circle_radius, square_reserve_size, bin_width, bin_height):
                    reserved_tiles += 1
                    
                    # Check if it's specifically the square reserve or outside circle
                    tile_center_x = x + bin_width / 2
                    tile_center_y = y + bin_height / 2
                    distance = math.sqrt((tile_center_x - circle_center_x)**2 + (tile_center_y - circle_center_y)**2)
                    
                    if distance <= circle_radius:  # Inside circle
                        square_reserved_tiles += 1
                    else:  # Outside circle
                        outside_circle_tiles += 1
    
    available_capacity = total_capacity - reserved_tiles
    
    circle_area = math.pi * circle_radius * circle_radius
    image_area = len(image_files) * bin_width * bin_height
    
    # Check placement order (first image should be top-left)
    if placements:
        first_image = placements[0]
        logger.info(f"First image position: ({first_image[0]}, {first_image[1]})")
    
    logger.info(f"\nResults for CIRCLE with {square_reserve_size}x{square_reserve_size} SQUARE reserve:")
    logger.info(f"Circle: diameter {circle_diameter:.1f}px, radius {circle_radius:.1f}px")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    logger.info(f"Total capacity: {total_capacity} tiles")
    logger.info(f"Reserved total: {reserved_tiles} tiles")
    logger.info(f"  - Square reserve: {square_reserved_tiles} tiles ({square_reserve_size}x{square_reserve_size}px)")
    logger.info(f"  - Outside circle: {outside_circle_tiles} tiles")
    logger.info(f"Available: {available_capacity} tiles")
    logger.info(f"Images placed: {len(placements)}")
    logger.info(f"Circle efficiency: {image_area/circle_area*100:.1f}%")
    
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
            self.envelope_shape = EnvelopeShape.CIRCLE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, circle_diameter, circle_diameter)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/circle_10000_square_test.tif"
    
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
    log_path = Path(f"{output_dir}/circle_10000_square_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="circle_10000_square_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_circle_square_preview(output_dir, circle_radius, circle_diameter, total_cols, total_rows,
                                            bin_width, bin_height, square_reserve_size)
        
        print(f"CIRCLE with 10000x10000 SQUARE reserve test completed. Thumbnail: {output_path}")
        print(f"Circle: diameter {circle_diameter:.1f}px, radius {circle_radius:.1f}px")
        print(f"Square reserve: {square_reserved_tiles} tiles ({square_reserve_size}x{square_reserve_size}px)")
        print(f"First image at: ({placements[0][0]}, {placements[0][1]}) - top-left priority")
        print(f"Circle efficiency: {image_area/circle_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_circle_square_preview(output_dir, circle_radius, circle_diameter, total_cols, total_rows,
                                        bin_width, bin_height, square_reserve_size):
    """Create preview with circle and center square highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/circle_10000_square_test.tif"
    output_path = "circle_10000_square_preview.png"
    
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
            
            # Calculate scaling for the square reserve
            square_ratio = square_reserve_size / circle_diameter
            scaled_square_size = new_width * square_ratio
            scaled_square_half = scaled_square_size / 2
            
            print(f"Preview size: {new_width}x{new_height}")
            print(f"Preview center: ({scaled_center_x:.0f},{scaled_center_y:.0f})")
            print(f"Red square size: {scaled_square_size:.0f}x{scaled_square_size:.0f}")
            
            # Draw directly on the resized image
            draw = ImageDraw.Draw(resized)
            
            # Draw the circle boundary (optional, for reference)
            circle_radius_scaled = new_width / 2
            draw.ellipse(
                [scaled_center_x - circle_radius_scaled, scaled_center_y - circle_radius_scaled,
                 scaled_center_x + circle_radius_scaled, scaled_center_y + circle_radius_scaled],
                outline='blue',
                width=2
            )
            
            # Fill the center square with solid red
            draw.rectangle(
                [scaled_center_x - scaled_square_half, scaled_center_y - scaled_square_half,
                 scaled_center_x + scaled_square_half, scaled_center_y + scaled_square_half],
                fill='red',  # Solid red fill for square reserve
                outline='darkred',
                width=3
            )
            
            print(f"Drew red square at center ({scaled_center_x:.0f},{scaled_center_y:.0f}) size {scaled_square_size:.0f}x{scaled_square_size:.0f}")
            print(f"Drew blue circle boundary with radius {circle_radius_scaled:.0f}")
            
            # Add text showing info
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 18)
            except:
                font = ImageFont.load_default()
            
            text = f"CIRCLE with\n{square_reserve_size}x{square_reserve_size}\nSquare Reserve\nRadius: {circle_radius:.0f}px"
            
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
    success = test_circle_10000_reserve()
    sys.exit(0 if success else 1)