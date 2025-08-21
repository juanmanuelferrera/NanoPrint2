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

def calculate_grid_capacity_and_leftover(square_side, bin_width, bin_height, reserve_cols, reserve_rows):
    """Calculate total grid capacity and leftover tiles after placing images."""
    
    total_cols = int(square_side / bin_width)
    total_rows = int(square_side / bin_height)
    total_capacity = total_cols * total_rows
    
    # Reserved tiles
    reserved_tiles = reserve_cols * reserve_rows
    
    # Available capacity
    available_capacity = total_capacity - reserved_tiles
    
    return total_capacity, available_capacity, reserved_tiles, total_cols, total_rows

def find_optimal_expanded_reserve(num_bins, square_side, bin_width, bin_height, target_aspect_ratio):
    """Find optimal expanded reserved space that uses leftover tiles."""
    
    logger = logging.getLogger("expanded_reserve")
    
    total_cols = int(square_side / bin_width)
    total_rows = int(square_side / bin_height)
    total_capacity = total_cols * total_rows
    
    logger.info(f"Grid: {total_rows}x{total_cols}, Total capacity: {total_capacity}")
    logger.info(f"Images to place: {num_bins}")
    logger.info(f"Leftover tiles if no reserve: {total_capacity - num_bins}")
    
    # Start with minimum reserve size (2 image areas equivalent)
    min_reserve_area = 2.0 * bin_width * bin_height
    min_reserve_height = math.sqrt(min_reserve_area / target_aspect_ratio)
    min_reserve_width = min_reserve_height * target_aspect_ratio
    
    min_reserve_cols = max(1, int(math.ceil(min_reserve_width / bin_width)))
    min_reserve_rows = max(1, int(math.ceil(min_reserve_height / bin_height)))
    
    logger.info(f"Minimum reserve: {min_reserve_rows}x{min_reserve_cols} tiles")
    
    # Try expanding the reserve to use leftover space
    best_reserve_cols = min_reserve_cols
    best_reserve_rows = min_reserve_rows
    best_leftover = float('inf')
    
    # Try different reserve sizes, maintaining aspect ratio as much as possible
    for reserve_rows in range(min_reserve_rows, total_rows // 2):
        for reserve_cols in range(min_reserve_cols, total_cols // 2):
            
            # Check if aspect ratio is reasonable (within 20% of target)
            actual_aspect = (reserve_cols * bin_width) / (reserve_rows * bin_height)
            aspect_diff = abs(actual_aspect - target_aspect_ratio) / target_aspect_ratio
            
            if aspect_diff > 0.3:  # Skip if aspect ratio is too far off
                continue
            
            # Calculate available capacity with this reserve
            reserved_tiles = reserve_rows * reserve_cols
            available_capacity = total_capacity - reserved_tiles
            
            # Can we fit all images?
            if available_capacity >= num_bins:
                leftover = available_capacity - num_bins
                
                # Prefer configurations that minimize leftover tiles
                if leftover < best_leftover:
                    best_leftover = leftover
                    best_reserve_cols = reserve_cols
                    best_reserve_rows = reserve_rows
                    
                    logger.info(f"Better reserve found: {reserve_rows}x{reserve_cols} tiles, "
                               f"aspect={actual_aspect:.3f}, leftover={leftover}")
    
    final_reserve_width = best_reserve_cols * bin_width
    final_reserve_height = best_reserve_rows * bin_height
    final_aspect = final_reserve_width / final_reserve_height
    
    logger.info(f"Final expanded reserve: {best_reserve_rows}x{best_reserve_cols} tiles")
    logger.info(f"Reserve dimensions: {final_reserve_width}x{final_reserve_height} pixels")
    logger.info(f"Reserve aspect ratio: {final_aspect:.3f} (target: {target_aspect_ratio:.3f})")
    logger.info(f"Leftover tiles: {best_leftover}")
    
    return final_reserve_width, final_reserve_height, best_reserve_cols, best_reserve_rows, best_leftover

def pack_images_with_expanded_reserve(num_bins, square_side, bin_width, bin_height, reserve_cols, reserve_rows):
    """Pack images avoiding the expanded reserved area."""
    
    placements = []
    bins_placed = 0
    
    total_cols = int(square_side / bin_width)
    total_rows = int(square_side / bin_height)
    
    # Place images row by row, skipping reserved area
    for row in range(total_rows):
        if bins_placed >= num_bins:
            break
            
        for col in range(total_cols):
            if bins_placed >= num_bins:
                break
                
            # Skip reserved area (top-left)
            if row < reserve_rows and col < reserve_cols:
                continue
            
            # Calculate position
            x = col * bin_width
            y = row * bin_height
            
            # Ensure it fits within square
            if x + bin_width <= square_side and y + bin_height <= square_side:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements, bins_placed

def test_square_with_expanded_reserve():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_square_with_expanded_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images with expanded reserved space")
    
    # Create output directory
    output_dir = "square_expanded_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Target aspect ratio for reserve (same as images)
    target_aspect_ratio = bin_width / bin_height
    
    logger.info(f"Bin dimensions: {bin_width}x{bin_height}")
    logger.info(f"Target reserve aspect ratio: {target_aspect_ratio:.3f}")
    
    # Use the optimal square size from previous test (we know it fits)
    square_side = 51300  # From the fixed test result
    
    # Find optimal expanded reserve
    reserve_width, reserve_height, reserve_cols, reserve_rows, leftover_tiles = find_optimal_expanded_reserve(
        len(image_files), square_side, bin_width, bin_height, target_aspect_ratio
    )
    
    # Pack images with expanded reserve
    placements, placed = pack_images_with_expanded_reserve(
        len(image_files), square_side, bin_width, bin_height, reserve_cols, reserve_rows
    )
    
    # Calculate statistics
    total_cols = int(square_side / bin_width)
    total_rows = int(square_side / bin_height)
    total_capacity = total_cols * total_rows
    reserved_tiles = reserve_cols * reserve_rows
    available_capacity = total_capacity - reserved_tiles
    
    total_area = square_side * square_side
    reserve_area = reserve_width * reserve_height
    available_area = total_area - reserve_area
    image_area = len(image_files) * bin_width * bin_height
    
    logger.info(f"\nFinal Results:")
    logger.info(f"Square: {square_side}x{square_side} pixels")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    logger.info(f"Total capacity: {total_capacity} tiles")
    logger.info(f"Reserved: {reserve_rows}x{reserve_cols} tiles ({reserved_tiles} tiles)")
    logger.info(f"Available: {available_capacity} tiles")
    logger.info(f"Images placed: {placed}")
    logger.info(f"Leftover tiles: {leftover_tiles}")
    logger.info(f"Reserve dimensions: {reserve_width}x{reserve_height} pixels")
    logger.info(f"Available space efficiency: {image_area/available_area*100:.1f}%")
    logger.info(f"Overall efficiency: {image_area/total_area*100:.1f}%")
    
    # Verify last image position
    if placements:
        last_placement = max(placements, key=lambda p: p[1] * 100000 + p[0])
        logger.info(f"Last image position: {last_placement}")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_size):
            self.rows = total_rows
            self.columns = total_cols
            self.canvas_width = canvas_size
            self.canvas_height = canvas_size
            self.placements = placements
            self.envelope_shape = EnvelopeShape.SQUARE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, square_side)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/square_expanded_reserve_test.tif"
    
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
    log_path = Path(f"{output_dir}/square_expanded_reserve_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="square_expanded_reserve_test",
        approved=False
    )
    
    # Check if file was actually created (more reliable than return value)
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Write detailed log
        log_filename = f"{output_dir}/square_expanded_reserve_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Square with Expanded Reserved Space Test\n")
            log_file.write(f"Approach: Expand reserved space to use leftover tiles\n")
            log_file.write(f"Optimization: Minimize wasted space by expanding reserve\n")
            log_file.write(f"\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Images placed: {placed}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Square side: {square_side} pixels\n")
            log_file.write(f"Grid: {total_rows}x{total_cols} tiles\n")
            log_file.write(f"Total capacity: {total_capacity} tiles\n")
            log_file.write(f"Reserved space: {reserve_width}x{reserve_height} pixels\n")
            log_file.write(f"Reserved tiles: {reserve_rows}x{reserve_cols} ({reserved_tiles} tiles)\n")
            log_file.write(f"Available tiles: {available_capacity}\n")
            log_file.write(f"Leftover tiles: {leftover_tiles}\n")
            log_file.write(f"Reserve aspect ratio: {reserve_width/reserve_height:.3f}\n")
            log_file.write(f"Target aspect ratio: {target_aspect_ratio:.3f}\n")
            log_file.write(f"Total area: {total_area:,} pixels²\n")
            log_file.write(f"Reserved area: {reserve_area:,} pixels²\n")
            log_file.write(f"Available area: {available_area:,} pixels²\n")
            log_file.write(f"Image area: {image_area:,} pixels²\n")
            log_file.write(f"Available space efficiency: {image_area/available_area*100:.1f}%\n")
            log_file.write(f"Overall efficiency: {image_area/total_area*100:.1f}%\n")
            if placements:
                last_pos = max(placements, key=lambda p: p[1] * 100000 + p[0])
                log_file.write(f"Last image position: {last_pos}\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {output_path}\n")
            log_file.write(f"  - {log_filename}\n")
        
        # Create preview and copy to clipboard
        create_and_copy_preview_expanded(output_dir, reserve_width, reserve_height, leftover_tiles)
        
        print(f"Square with expanded reserve test completed. Thumbnail: {output_path}")
        print(f"Square: {square_side}x{square_side}")
        print(f"Expanded reserve: {reserve_width}x{reserve_height} ({reserve_rows}x{reserve_cols} tiles)")
        print(f"Leftover tiles: {leftover_tiles}")
        print(f"Available efficiency: {image_area/available_area*100:.1f}%, Overall: {image_area/total_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_preview_expanded(output_dir, reserve_width, reserve_height, leftover_tiles):
    """Create preview with expanded reserved space highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/square_expanded_reserve_test.tif"
    output_path = "square_expanded_reserve_preview.png"
    
    try:
        with Image.open(input_path) as img:
            max_size = 800
            ratio = min(max_size / img.width, max_size / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Calculate scaled reserve dimensions
            scaled_reserve_width = int(reserve_width * ratio)
            scaled_reserve_height = int(reserve_height * ratio)
            
            # Create semi-transparent overlay for reserved area
            overlay = Image.new('RGBA', resized.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(
                [0, 0, scaled_reserve_width, scaled_reserve_height],
                fill=(0, 255, 0, 100)  # Semi-transparent green for expanded reserve
            )
            
            # Composite the overlay
            resized = resized.convert('RGBA')
            resized = Image.alpha_composite(resized, overlay)
            
            # Draw green border around expanded reserved space
            draw = ImageDraw.Draw(resized)
            draw.rectangle(
                [0, 0, scaled_reserve_width-1, scaled_reserve_height-1],
                outline='green',
                width=4
            )
            
            # Add text showing leftover tiles
            try:
                # Try to use a system font, fall back to default if not available
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 24)
            except:
                font = ImageFont.load_default()
            
            text = f"Leftover: {leftover_tiles} tiles"
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
            print(f"Expanded reserve space (green area): {scaled_reserve_width}x{scaled_reserve_height}")
            print(f"Leftover tiles reduced to: {leftover_tiles}")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_square_with_expanded_reserve()
    sys.exit(0 if success else 1)