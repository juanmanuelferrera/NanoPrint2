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

def generate_true_elliptical_placements(num_bins, center_x, center_y, a, b, bin_width, bin_height):
    """Generate elliptical placement following the ellipse curve row by row for maximum density."""
    placements = []
    bins_placed = 0
    
    # Calculate how many rows we can fit vertically in the ellipse
    max_rows = int(2 * b / bin_height)
    
    # Start from top of ellipse and work down
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
        
        # Calculate y position for this row
        y = center_y - b + (row_idx + 0.5) * bin_height
        
        # Calculate how wide the ellipse is at this y position
        # Ellipse equation: x²/a² + y²/b² = 1
        # Solve for x: x = ±a * sqrt(1 - (y-cy)²/b²)
        y_offset = y - center_y
        if abs(y_offset) >= b:
            continue  # Outside ellipse vertically
        
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor * 0.95  # 95% to ensure fit
        
        # Calculate how many bins fit in this row
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Place bins centered in this row
        if bins_in_row > 0:
            start_x = center_x - (bins_in_row * bin_width) / 2
            
            for col in range(bins_in_row):
                if bins_placed >= num_bins:
                    break
                
                x = start_x + col * bin_width
                
                # Double-check that this position is actually within ellipse
                bin_center_x = x + bin_width // 2
                bin_center_y = y + bin_height // 2
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.98:  # Use 98% of ellipse
                    placements.append((int(x), int(y)))
                    bins_placed += 1
    
    return placements

def test_true_ellipse_packing():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_true_ellipse_packing")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images for true ellipse packing test")
    
    # Create output directory
    output_dir = "true_ellipse_packing_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Ellipse parameters (portrait 1.0:1.29 aspect ratio)
    aspect_x = 1.0
    aspect_y = 1.29
    
    # Calculate optimal ellipse size using area-based approach
    bin_area = bin_width * bin_height
    total_area = len(image_files) * bin_area * 1.4  # 40% overhead for elliptical packing
    
    aspect_ratio = aspect_x / aspect_y
    
    # Calculate ellipse radii: Area = π * a * b, where a/b = aspect_ratio
    b = math.sqrt(total_area / (math.pi * aspect_ratio))
    a = b * aspect_ratio
    
    canvas_width = int(2 * a)
    canvas_height = int(2 * b)
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    
    logger.info(f"Ellipse parameters: a={a:.1f}, b={b:.1f}")
    logger.info(f"Canvas size: {canvas_width}x{canvas_height}")
    logger.info(f"Aspect ratio: {aspect_x}:{aspect_y}")
    
    # Generate true elliptical placements
    placements = generate_true_elliptical_placements(
        len(image_files), center_x, center_y, a, b, bin_width, bin_height
    )
    
    logger.info(f"Generated {len(placements)} placements for {len(image_files)} images")
    logger.info(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}%")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, placements, canvas_width, canvas_height):
            self.rows = 0  # Not used in true ellipse mode
            self.columns = 0  # Not used in true ellipse mode
            self.canvas_width = canvas_width
            self.canvas_height = canvas_height
            self.placements = placements
            self.envelope_shape = EnvelopeShape.ELLIPSE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(placements, canvas_width, canvas_height)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/true_ellipse_packing_test.tif"
    
    # Create image bins from file paths
    image_bins = []
    for i, image_path in enumerate(image_files[:len(placements)]):  # Only use as many as we have placements
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate the full resolution TIFF and thumbnail
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/true_ellipse_packing_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="true_ellipse_packing_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Write test log
        log_filename = f"{output_dir}/true_ellipse_packing_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"True Ellipse Packing Test\n")
            log_file.write(f"Timestamp: {thumbnail_result.split('_')[-1].split('.')[0]}\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Images placed: {len(placements)}\n")
            log_file.write(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}%\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Envelope shape: ellipse (true curve-following)\n")
            log_file.write(f"Aspect ratio: {aspect_x}:{aspect_y}\n")
            log_file.write(f"Ellipse radii: a={a:.1f}, b={b:.1f}\n")
            log_file.write(f"Canvas size: {canvas_width}x{canvas_height}\n")
            log_file.write(f"Placement method: Row-by-row following ellipse curve\n")
            log_file.write(f"Optimization: Maximum density within ellipse boundary\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"True ellipse packing test completed. Thumbnail: {thumbnail_result}")
        print(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}% ({len(placements)}/{len(image_files)} images)")
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

if __name__ == "__main__":
    success = test_true_ellipse_packing()
    sys.exit(0 if success else 1)