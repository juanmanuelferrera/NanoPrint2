#!/usr/bin/env python3

import sys
import os
import glob
import re
import logging
import math
from pathlib import Path
from typing import List, Tuple

# Add the nanofiche_core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nanofiche_core'))

from nanofiche_core.logger import setup_logging
from nanofiche_core.renderer import NanoFicheRenderer
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.packer import EnvelopeShape, PackingResult

def natural_sort_key(filename):
    """Extract numeric part from filename for proper sorting (1, 2, ... 10, 11, ...)"""
    match = re.search(r'-(\d+)\.tif', filename)
    if match:
        return int(match.group(1))
    return 0

class BinaryEnvelopeSearchPacker:
    """Binary search packer that finds minimal envelope area."""
    
    def __init__(self, bin_width: int, bin_height: int, square_reserve_size: int = 10000):
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.square_reserve_size = square_reserve_size
        self.logger = logging.getLogger(__name__)
    
    def is_position_inside_circle_and_outside_square(self, x: int, y: int, circle_radius: float, 
                                                   center_x: int, center_y: int) -> bool:
        """Check if position is inside circle and outside square reserve."""
        # Check if tile center is inside circle
        tile_center_x = x + self.bin_width // 2
        tile_center_y = y + self.bin_height // 2
        distance_from_center = math.sqrt((tile_center_x - center_x)**2 + (tile_center_y - center_y)**2)
        
        if distance_from_center > circle_radius:
            return False  # Outside circle
        
        # Check if tile overlaps with center square reserve
        square_half_size = self.square_reserve_size // 2
        square_left = center_x - square_half_size
        square_right = center_x + square_half_size
        square_top = center_y - square_half_size
        square_bottom = center_y + square_half_size
        
        # Tile bounds
        tile_left = x
        tile_right = x + self.bin_width
        tile_top = y
        tile_bottom = y + self.bin_height
        
        # Check if tile overlaps with square reserve
        if not (tile_right <= square_left or tile_left >= square_right or 
                tile_bottom <= square_top or tile_top >= square_bottom):
            return False  # Overlaps with square reserve
        
        return True
    
    def pack_images_in_circle(self, num_bins: int, circle_radius: float) -> Tuple[List[Tuple[int, int]], bool]:
        """
        Pack images row-by-row in circle with square reserve.
        Returns: (placements, all_images_fit)
        """
        canvas_size = int(2 * circle_radius)
        center_x = center_y = canvas_size // 2
        
        placements = []
        images_placed = 0
        
        # Go row by row from top to bottom
        current_y = 0
        
        while images_placed < num_bins and current_y + self.bin_height <= canvas_size:
            # Place images left to right in this row
            current_x = 0
            
            while images_placed < num_bins and current_x + self.bin_width <= canvas_size:
                # Check if this position is valid
                if self.is_position_inside_circle_and_outside_square(current_x, current_y, circle_radius, center_x, center_y):
                    placements.append((current_x, current_y))
                    images_placed += 1
                
                current_x += self.bin_width
            
            current_y += self.bin_height
        
        # Check if all images fit
        all_images_fit = (images_placed == num_bins)
        return placements, all_images_fit
    
    def find_optimal_circle_with_binary_search(self, num_bins: int) -> PackingResult:
        """
        Binary search algorithm to find minimal circle area:
        1. Calculate image area
        2. Create envelope with area same as image area  
        3. Place images, check if any go outside envelope
        4. If outside then increase envelope area
        5. If inside then decrease envelope area
        6. Stop at last area where envelope >= image area
        """
        
        # Step 1: Calculate image area
        image_area = num_bins * self.bin_width * self.bin_height
        self.logger.info(f"Step 1: Image area = {image_area:,} pixels²")
        
        # Step 2: Start with envelope area same as image area
        # For circle: area = π * r², so r = sqrt(area / π)
        min_radius = math.sqrt(image_area / math.pi)
        
        # Set search bounds - max radius includes overhead for inefficiency
        max_radius = math.sqrt(image_area * 3 / math.pi)  # Up to 3x area
        
        self.logger.info(f"Step 2: Starting binary search - min_radius={min_radius:.1f}, max_radius={max_radius:.1f}")
        
        best_radius = None
        best_placements = None
        iteration = 0
        
        # Binary search loop
        while max_radius - min_radius > 1.0:  # 1 pixel precision
            iteration += 1
            test_radius = (min_radius + max_radius) / 2
            test_area = math.pi * test_radius * test_radius
            
            self.logger.info(f"Step {iteration + 2}: Testing radius={test_radius:.1f}, area={test_area:,.0f}")
            
            # Step 3: Place images and check if any go outside envelope
            placements, all_fit = self.pack_images_in_circle(num_bins, test_radius)
            
            if all_fit:
                # Step 5: If inside then decrease envelope area
                self.logger.info(f"  ✓ All {len(placements)} images fit - decreasing envelope area")
                max_radius = test_radius
                best_radius = test_radius
                best_placements = placements
            else:
                # Step 4: If outside then increase envelope area  
                self.logger.info(f"  ✗ Only {len(placements)}/{num_bins} images fit - increasing envelope area")
                min_radius = test_radius
        
        # Step 6: Stop at last area where envelope is larger than image area
        if best_radius is None:
            # Use the minimum working radius
            best_radius = max_radius
            best_placements, _ = self.pack_images_in_circle(num_bins, best_radius)
        
        final_canvas_size = int(2 * best_radius)
        final_envelope_area = math.pi * best_radius * best_radius
        efficiency = image_area / final_envelope_area * 100
        
        self.logger.info(f"Step 6: Final envelope - radius={best_radius:.1f}, area={final_envelope_area:,.0f}")
        self.logger.info(f"Efficiency: {image_area:,} / {final_envelope_area:,.0f} = {efficiency:.1f}%")
        
        # Calculate grid dimensions for compatibility
        rows = int(final_canvas_size / self.bin_height)
        cols = int(final_canvas_size / self.bin_width)
        
        return PackingResult(
            rows=rows,
            columns=cols,
            canvas_width=final_canvas_size,
            canvas_height=final_canvas_size,
            placements=best_placements,
            envelope_shape=EnvelopeShape.CIRCLE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )

def test_binary_envelope_search():
    """Test binary envelope search algorithm."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_binary_envelope_search")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    square_reserve_size = 10000
    logger.info(f"Testing binary envelope search with {square_reserve_size}x{square_reserve_size} square reserve for {len(image_files)} images")
    
    # Create output directory
    output_dir = "binary_envelope_search_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Create binary search packer
    packer = BinaryEnvelopeSearchPacker(bin_width, bin_height, square_reserve_size)
    
    # Execute binary search algorithm
    try:
        packing_result = packer.find_optimal_circle_with_binary_search(len(image_files))
    except Exception as e:
        logger.error(f"Binary search failed: {e}")
        return False
    
    # Calculate final statistics
    circle_radius = packing_result.canvas_width // 2
    circle_area = math.pi * circle_radius ** 2
    image_area = len(image_files) * bin_width * bin_height
    square_reserve_area = square_reserve_size * square_reserve_size
    efficiency = image_area / circle_area * 100
    
    logger.info(f"\nBINARY SEARCH RESULTS:")
    logger.info(f"Circle: radius {circle_radius}px, diameter {packing_result.canvas_width}px")
    logger.info(f"Canvas: {packing_result.canvas_width}x{packing_result.canvas_height}")
    logger.info(f"Images placed: {len(packing_result.placements)}")
    logger.info(f"Final efficiency: {efficiency:.1f}%")
    
    if len(packing_result.placements) < len(image_files):
        logger.error(f"Only placed {len(packing_result.placements)}/{len(image_files)} images!")
        return False
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/binary_envelope_search_test.tif"
    
    # Create image bins
    image_bins = []
    for i, image_path in enumerate(image_files[:len(packing_result.placements)]):
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate TIFF
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/binary_envelope_search_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="binary_envelope_search_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_binary_preview(output_dir, circle_radius, packing_result.canvas_width, 
                                     square_reserve_size, efficiency)
        
        print(f"BINARY ENVELOPE SEARCH test completed. Thumbnail: {output_path}")
        print(f"Algorithm: Pure binary search on envelope area")
        print(f"Circle: radius {circle_radius}px, diameter {packing_result.canvas_width}px")
        print(f"Images placed: {len(packing_result.placements)} using binary envelope search")
        print(f"Final efficiency: {efficiency:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_binary_preview(output_dir, circle_radius, canvas_size, square_reserve_size, efficiency):
    """Create preview with binary search result."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/binary_envelope_search_test.tif"
    output_path = "binary_envelope_search_preview.png"
    
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
            
            # Calculate center and scaled dimensions
            scaled_center_x = new_width / 2
            scaled_center_y = new_height / 2
            scaled_radius = new_width / 2
            
            # Calculate scaling for the square reserve
            square_ratio = square_reserve_size / canvas_size
            scaled_square_size = new_width * square_ratio
            scaled_square_half = scaled_square_size / 2
            
            # Draw directly on the resized image
            draw = ImageDraw.Draw(resized)
            
            # Draw the circle boundary
            draw.ellipse(
                [scaled_center_x - scaled_radius, scaled_center_y - scaled_radius,
                 scaled_center_x + scaled_radius, scaled_center_y + scaled_radius],
                outline='blue',
                width=3
            )
            
            # Fill the center square with solid red
            draw.rectangle(
                [scaled_center_x - scaled_square_half, scaled_center_y - scaled_square_half,
                 scaled_center_x + scaled_square_half, scaled_center_y + scaled_square_half],
                fill='red',
                outline='darkred',
                width=3
            )
            
            # Add text showing info
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 18)
            except:
                font = ImageFont.load_default()
            
            text = f"BINARY SEARCH\n{square_reserve_size}x{square_reserve_size} Reserve\nRadius: {circle_radius}px\nEfficiency: {efficiency:.1f}%"
            
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
    success = test_binary_envelope_search()
    sys.exit(0 if success else 1)