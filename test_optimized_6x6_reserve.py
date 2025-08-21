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

def pack_images_with_reserve(num_bins, rect_width, rect_height, bin_width, bin_height, reserve_cols, reserve_rows):
    """Pack images avoiding the reserved area."""
    placements = []
    bins_placed = 0
    
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    
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
            
            # Ensure it fits within rectangle
            if x + bin_width <= rect_width and y + bin_height <= rect_height:
                placements.append((int(x), int(y)))
                bins_placed += 1
    
    return placements, bins_placed

def test_optimized_6x6_reserve():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_optimized_6x6_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Testing optimized 6x6 reserve for {len(image_files)} images")
    
    # Create output directory
    output_dir = "rectangle_6x6_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Use the taller rectangle from our test that proved 6x6 works better
    target_aspect_ratio = 1.0 / 1.29  # Portrait
    rect_width = 46975.7
    rect_height = 60598.6
    
    # Test 6x6 reserve (proven to be better)
    reserve_rows = 6
    reserve_cols = 6
    
    logger.info(f"Rectangle: {rect_width:.1f}x{rect_height:.1f}")
    logger.info(f"Target aspect ratio (W:H): {target_aspect_ratio:.3f}")
    logger.info(f"Actual aspect ratio (W:H): {rect_width/rect_height:.3f}")
    logger.info(f"Reserve: {reserve_rows}x{reserve_cols} tiles")
    
    # Pack images with 6x6 reserve
    placements, placed = pack_images_with_reserve(
        len(image_files), rect_width, rect_height, bin_width, bin_height, reserve_cols, reserve_rows
    )
    
    # Calculate statistics
    total_cols = int(rect_width / bin_width)
    total_rows = int(rect_height / bin_height)
    total_capacity = total_cols * total_rows
    reserved_tiles = reserve_cols * reserve_rows
    available_capacity = total_capacity - reserved_tiles
    
    total_area = rect_width * rect_height
    reserve_area = reserve_cols * bin_width * reserve_rows * bin_height
    available_area = total_area - reserve_area
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
    
    logger.info(f"\nResults:")
    logger.info(f"Grid: {total_rows}x{total_cols} tiles")
    logger.info(f"Total capacity: {total_capacity} tiles")
    logger.info(f"Reserved: {reserve_rows}x{reserve_cols} tiles ({reserved_tiles} tiles)")
    logger.info(f"Available: {available_capacity} tiles")
    logger.info(f"Images placed: {placed}")
    logger.info(f"Bottom row: {bottom_row_images}/{total_cols} ({bottom_row_utilization:.1f}%)")
    logger.info(f"Last image Y: {last_row_y}")
    logger.info(f"Bottom empty: {bottom_empty:.1f} pixels")
    logger.info(f"Reserve dimensions: {reserve_cols * bin_width}x{reserve_rows * bin_height} pixels")
    logger.info(f"Available space efficiency: {image_area/available_area*100:.1f}%")
    logger.info(f"Overall efficiency: {image_area/total_area*100:.1f}%")
    
    if placed < len(image_files):
        logger.error(f"Only placed {placed}/{len(image_files)} images!")
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
    output_filename = f"{output_dir}/rectangle_6x6_reserve_test.tif"
    
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
    log_path = Path(f"{output_dir}/rectangle_6x6_reserve_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="rectangle_6x6_reserve_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_preview_6x6(output_dir, reserve_cols * bin_width, reserve_rows * bin_height, 
                                   bottom_row_utilization, rect_width/rect_height)
        
        print(f"Optimized 6x6 reserve test completed. Thumbnail: {output_path}")
        print(f"Rectangle: {rect_width:.1f}x{rect_height:.1f} (aspect W:H: {rect_width/rect_height:.3f})")
        print(f"6x6 reserve: {reserve_cols * bin_width}x{reserve_rows * bin_height} pixels")
        print(f"Bottom row utilization: {bottom_row_utilization:.1f}% ({bottom_row_images}/{total_cols})")
        print(f"Bottom empty space: {bottom_empty:.1f} pixels")
        print(f"Available efficiency: {image_area/available_area*100:.1f}%, Overall: {image_area/total_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_preview_6x6(output_dir, reserve_width, reserve_height, bottom_util, aspect_ratio):
    """Create preview with 6x6 reserved space highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/rectangle_6x6_reserve_test.tif"
    output_path = "rectangle_6x6_reserve_preview.png"
    
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
                fill=(0, 255, 0, 100)  # Semi-transparent green for 6x6 reserve
            )
            
            # Composite the overlay
            resized = resized.convert('RGBA')
            resized = Image.alpha_composite(resized, overlay)
            
            # Draw green border around 6x6 reserved space
            draw = ImageDraw.Draw(resized)
            draw.rectangle(
                [0, 0, scaled_reserve_width-1, scaled_reserve_height-1],
                outline='green',
                width=4
            )
            
            # Add text showing bottom utilization and 6x6 info
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 20)
            except:
                font = ImageFont.load_default()
            
            text = f"6x6 Reserve\nBottom: {bottom_util:.1f}%\nAspect: {aspect_ratio:.3f}"
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
            print(f"6x6 reserve space (green area): {scaled_reserve_width}x{scaled_reserve_height}")
            
            # Copy to clipboard
            abs_path = os.path.abspath(output_path)
            subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'])
            print(f"Preview copied to clipboard")
            
    except Exception as e:
        print(f"Error creating preview: {e}")

if __name__ == "__main__":
    success = test_optimized_6x6_reserve()
    sys.exit(0 if success else 1)