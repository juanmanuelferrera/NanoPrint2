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

class OptimizedCircularPackerWithSquareReserve:
    """Circular packer using the optimized nanofiche algorithm with square reserve."""
    
    def __init__(self, bin_width: int, bin_height: int, square_reserve_size: int = 10000):
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.square_reserve_size = square_reserve_size
        self.logger = logging.getLogger(__name__)
    
    def is_position_valid(self, x: int, y: int, working_radius: float, center_x: int, center_y: int) -> bool:
        """Check if a position is valid (inside circle and outside square reserve)."""
        # Check if tile center is inside circle
        tile_center_x = x + self.bin_width // 2
        tile_center_y = y + self.bin_height // 2
        distance_from_center = math.sqrt((tile_center_x - center_x)**2 + (tile_center_y - center_y)**2)
        
        if distance_from_center > working_radius:
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
    
    def generate_circular_row_placements_with_reserve(self, num_bins: int, working_radius: float,
                                                    center_x: int, center_y: int) -> List[Tuple[int, int]]:
        """Generate row-by-row circular placement avoiding square reserve."""
        
        placements = []
        images_placed = 0
        
        # Go row by row from top to bottom
        canvas_size = center_x * 2
        current_y = 0
        
        while images_placed < num_bins and current_y + self.bin_height <= canvas_size:
            # Calculate row center Y position
            row_center_y = current_y + self.bin_height // 2
            
            # Calculate distance from canvas center
            y_offset_from_center = abs(row_center_y - center_y)
            
            # Check if this row intersects the working circle
            if y_offset_from_center <= working_radius:
                # Calculate circle width at this Y position
                if y_offset_from_center < working_radius:
                    x_half_width = math.sqrt(working_radius**2 - y_offset_from_center**2)
                    row_width = int(2 * x_half_width)
                    
                    # Calculate theoretical images that could fit
                    theoretical_images = row_width // self.bin_width
                    
                    # Place images from left to right, checking for valid positions
                    row_start_x = center_x - (row_width // 2)
                    
                    images_in_row = 0
                    for col in range(theoretical_images):
                        if images_placed >= num_bins:
                            break
                        
                        x = row_start_x + col * self.bin_width
                        
                        # Ensure within canvas bounds
                        if x >= 0 and x + self.bin_width <= canvas_size:
                            # Check if position is valid (inside circle, outside square reserve)
                            if self.is_position_valid(x, current_y, working_radius, center_x, center_y):
                                placements.append((x, current_y))
                                images_placed += 1
                                images_in_row += 1
            
            current_y += self.bin_height
        
        return placements
    
    def pack_circle_with_square_reserve(self, num_bins: int) -> PackingResult:
        """Pack bins into circle with square reserve using optimized algorithm."""
        
        # Calculate theoretical minimum radius for circle packing
        bin_area = self.bin_width * self.bin_height
        total_area = num_bins * bin_area
        theoretical_radius = math.sqrt(total_area / math.pi)
        
        # Start with larger radius to account for square reserve
        current_radius = theoretical_radius * 1.5  # Start with 50% larger due to square reserve
        radius_step = 100
        
        best_placements = None
        best_radius = None
        
        # Find a working radius
        max_attempts = 200
        attempts = 0
        
        self.logger.info(f"Starting circular packing with {self.square_reserve_size}x{self.square_reserve_size} square reserve")
        self.logger.info(f"Theoretical radius: {theoretical_radius:.1f}, starting radius: {current_radius:.1f}")
        
        while best_placements is None and attempts < max_attempts:
            canvas_size = int(2 * current_radius)
            center_x = center_y = canvas_size // 2
            
            test_placements = self.generate_circular_row_placements_with_reserve(
                num_bins, current_radius, center_x, center_y
            )
            
            if len(test_placements) == num_bins:
                best_placements = test_placements
                best_radius = current_radius
                self.logger.info(f"Found working radius: {current_radius:.1f} after {attempts} attempts")
                break
            else:
                self.logger.info(f"Attempt {attempts}: radius {current_radius:.1f} placed {len(test_placements)}/{num_bins}")
                current_radius += radius_step
                attempts += 1
        
        if best_placements is None:
            raise RuntimeError(f"Could not find working radius after {max_attempts} attempts")
        
        # Binary search for optimal radius
        min_radius = theoretical_radius
        max_radius = best_radius
        
        while max_radius - min_radius > 5:  # 5 pixel precision
            test_radius = (min_radius + max_radius) / 2
            canvas_size = int(2 * test_radius)
            center_x = center_y = canvas_size // 2
            
            test_placements = self.generate_circular_row_placements_with_reserve(
                num_bins, test_radius, center_x, center_y
            )
            
            if len(test_placements) == num_bins:
                # This radius works, try smaller
                max_radius = test_radius
                best_radius = test_radius
                best_placements = test_placements
            else:
                # This radius too small, increase minimum
                min_radius = test_radius
        
        # Final results
        final_canvas_size = int(2 * best_radius)
        envelope_area = math.pi * best_radius ** 2
        envelope_ratio = envelope_area / total_area
        
        self.logger.info(f"Optimized circular packing: radius={best_radius:.1f}, envelope_ratio={envelope_ratio:.2f}")
        
        # Calculate approximate grid dimensions for compatibility
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

def test_optimized_circle_10000_reserve():
    """Test optimized circular packing with 10000x10000 pixel square reserve."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_optimized_circle_10000_reserve")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    square_reserve_size = 10000
    logger.info(f"Testing optimized circle with {square_reserve_size}x{square_reserve_size} pixel square reserve for {len(image_files)} images")
    
    # Create output directory
    output_dir = "optimized_circle_10000_reserve_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Create optimized packer
    packer = OptimizedCircularPackerWithSquareReserve(bin_width, bin_height, square_reserve_size)
    
    # Pack images
    try:
        packing_result = packer.pack_circle_with_square_reserve(len(image_files))
    except RuntimeError as e:
        logger.error(f"Packing failed: {e}")
        return False
    
    # Calculate statistics
    circle_radius = packing_result.canvas_width // 2
    circle_area = math.pi * circle_radius ** 2
    image_area = len(image_files) * bin_width * bin_height
    square_reserve_area = square_reserve_size * square_reserve_size
    
    # Count reserved tiles for statistics
    center_x = center_y = circle_radius
    reserved_tiles = 0
    total_tiles = 0
    
    for y in range(0, packing_result.canvas_height, bin_height):
        for x in range(0, packing_result.canvas_width, bin_width):
            if y + bin_height <= packing_result.canvas_height and x + bin_width <= packing_result.canvas_width:
                total_tiles += 1
                if not packer.is_position_valid(x, y, circle_radius, center_x, center_y):
                    reserved_tiles += 1
    
    logger.info(f"\nResults for OPTIMIZED CIRCLE with {square_reserve_size}x{square_reserve_size} SQUARE reserve:")
    logger.info(f"Circle: radius {circle_radius}px, diameter {packing_result.canvas_width}px")
    logger.info(f"Canvas: {packing_result.canvas_width}x{packing_result.canvas_height}")
    logger.info(f"Images placed: {len(packing_result.placements)}")
    logger.info(f"Circle area: {circle_area:.0f} px²")
    logger.info(f"Image area: {image_area:.0f} px²")
    logger.info(f"Square reserve area: {square_reserve_area:.0f} px²")
    logger.info(f"Circle efficiency: {image_area/circle_area*100:.1f}%")
    
    if len(packing_result.placements) < len(image_files):
        logger.error(f"Only placed {len(packing_result.placements)}/{len(image_files)} images!")
        return False
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/optimized_circle_10000_square_test.tif"
    
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
    log_path = Path(f"{output_dir}/optimized_circle_10000_square_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="optimized_circle_10000_square_test",
        approved=False
    )
    
    # Check if file was actually created
    if output_path.exists():
        logger.info(f"Thumbnail generated successfully: {output_path}")
        
        # Create preview and copy to clipboard
        create_and_copy_optimized_preview(output_dir, circle_radius, packing_result.canvas_width, 
                                        square_reserve_size, image_area/circle_area*100)
        
        print(f"OPTIMIZED CIRCLE with 10000x10000 SQUARE reserve test completed. Thumbnail: {output_path}")
        print(f"Circle: radius {circle_radius}px, diameter {packing_result.canvas_width}px")
        print(f"Images placed: {len(packing_result.placements)} using optimized circular algorithm")
        print(f"Circle efficiency: {image_area/circle_area*100:.1f}%")
        
        return True
    else:
        logger.error(f"Failed to generate thumbnail - file not created: {output_path}")
        return False

def create_and_copy_optimized_preview(output_dir, circle_radius, canvas_size, square_reserve_size, efficiency):
    """Create preview with optimized circular packing and center square highlighted."""
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    input_path = f"{output_dir}/optimized_circle_10000_square_test.tif"
    output_path = "optimized_circle_10000_square_preview.png"
    
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
            scaled_radius = new_width / 2
            
            # Calculate scaling for the square reserve
            square_ratio = square_reserve_size / canvas_size
            scaled_square_size = new_width * square_ratio
            scaled_square_half = scaled_square_size / 2
            
            print(f"Preview center: ({scaled_center_x:.0f},{scaled_center_y:.0f})")
            print(f"Circle radius: {scaled_radius:.0f}")
            print(f"Red square size: {scaled_square_size:.0f}x{scaled_square_size:.0f}")
            
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
            
            text = f"OPTIMIZED CIRCLE\n{square_reserve_size}x{square_reserve_size} Reserve\nRadius: {circle_radius}px\nEfficiency: {efficiency:.1f}%"
            
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
    success = test_optimized_circle_10000_reserve()
    sys.exit(0 if success else 1)